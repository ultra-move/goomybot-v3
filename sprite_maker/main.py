import os
from PIL import Image
import requests
from io import BytesIO

class ImageCombiner:
    def __init__(self, urls):
        """
        Initializes the ImageCombiner with a list of image URLs.

        Args:
            urls (list): A list of strings, where each string is a URL to an image.
                         Must contain at least one URL.
        """
        if not urls or not isinstance(urls, list):
            raise ValueError("Urls must be a non-empty list of strings.")
        self.urls = urls

    def _download_image(self, url):
        """
        Downloads an image from a given URL and returns a PIL Image object.

        Args:
            url (str): The URL of the image to download.

        Returns:
            PIL.Image.Image: The downloaded image as a PIL Image object.

        Raises:
            requests.exceptions.RequestException: If there's an issue downloading the image.
            PIL.UnidentifiedImageError: If the downloaded content is not a valid image.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
            image_data = BytesIO(response.content)
            img = Image.open(image_data)
            return img
        except requests.exceptions.RequestException as e:
            print(f"Error downloading image from {url}: {e}")
            raise
        except Image.UnidentifiedImageError as e:
            print(f"Could not identify image from {url}. It might not be a valid image: {e}")
            raise

    def combine_images(self, output_path="combined_image.png", horizontal_spacing=0, vertical_align='bottom'):
        """
        Downloads all images from the provided URLs, resizes them to the smallest
        common overall height, and combines them side-by-side into a single image,
        with spacing applied between content areas and specified vertical alignment.

        Args:
            output_path (str): The full path and filename to save the combined image,
                                including the directory.
            horizontal_spacing (int): The horizontal spacing between *image content* in pixels.
                                    Use a positive value for gaps, 0 for touching,
                                    and a negative value for overlapping.
            vertical_align (str): Defines the vertical alignment strategy.
                                  Can be 'top', 'bottom', or 'center'.
                                  'top': Aligns the top of each resized image to the top of the canvas.
                                  'bottom': Aligns the visible content of images to a common bottom line.
                                  'center': Aligns the visible content of images to the vertical center of the canvas.

        Returns:
            PIL.Image.Image: The combined image object.
        """
        if not self.urls:
            print("No URLs provided to combine.")
            return None

        if vertical_align not in ['top', 'bottom', 'center']:
            raise ValueError("vertical_align must be 'top', 'bottom', or 'center'.")

        images = []
        for url in self.urls:
            try:
                img = self._download_image(url)
                images.append(img)
            except (requests.exceptions.RequestException, Image.UnidentifiedImageError):
                print(f"Skipping image from {url} due to download/processing error.")
                continue

        if not images:
            print("No images were successfully downloaded to combine.")
            return None

        processed_images_info = []
        for img in images:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            processed_images_info.append({'image': img})

        min_overall_height = min(info['image'].height for info in processed_images_info)

        resized_images_data = [] # Store {image, content_bottom_y, content_left_x, content_right_x, content_top_y, content_height}
        for info in processed_images_info:
            img = info['image']
            
            if img.height != min_overall_height:
                width = int(img.width * min_overall_height / img.height)
                if width == 0: width = 1 
                resized_img = img.resize((width, min_overall_height), Image.LANCZOS)
            else:
                resized_img = img

            bbox = resized_img.getbbox() 
            
            if bbox:
                content_left_x = bbox[0]
                content_top_y = bbox[1]
                content_right_x = bbox[2]
                content_bottom_y = bbox[3]
                content_height = content_bottom_y - content_top_y
            else:
                content_left_x = 0
                content_top_y = 0
                content_right_x = resized_img.width
                content_bottom_y = resized_img.height
                content_height = resized_img.height

            resized_images_data.append({
                'image': resized_img,
                'content_left_x': content_left_x,
                'content_top_y': content_top_y,
                'content_right_x': content_right_x,
                'content_bottom_y': content_bottom_y,
                'content_height': content_height
            })

        # Calculate total width of the combined image based on content and spacing
        total_canvas_width_needed = 0
        current_content_x_on_canvas = 0

        for i, info in enumerate(resized_images_data):
            content_left_x = info['content_left_x']
            content_right_x = info['content_right_x']
            
            paste_x_for_image = current_content_x_on_canvas - content_left_x
            
            current_image_content_right_on_canvas = paste_x_for_image + content_right_x

            total_canvas_width_needed = max(total_canvas_width_needed, current_image_content_right_on_canvas)

            current_content_x_on_canvas = current_image_content_right_on_canvas + horizontal_spacing

        total_width = max(1, total_canvas_width_needed)

        combined_image = Image.new('RGBA', (total_width, min_overall_height), (0, 0, 0, 0))

        current_content_x_on_canvas = 0

        # Determine target_content_bottom_y for 'bottom' alignment
        # This will be the maximum content_bottom_y found among all resized images.
        target_content_bottom_y = max(info['content_bottom_y'] for info in resized_images_data)

        for info in resized_images_data:
            img = info['image']
            
            y_offset = 0 # Default for 'top' alignment

            if vertical_align == 'bottom':
                # Calculate y_offset to align content bottom to the lowest content bottom
                y_offset = target_content_bottom_y - info['content_bottom_y']
            elif vertical_align == 'center':
                # Calculate y_offset to center content vertically within the canvas height
                content_mid_point_y_in_image = info['content_top_y'] + info['content_height'] / 2
                target_mid_point_y_on_canvas = min_overall_height / 2
                y_offset = int(target_mid_point_y_on_canvas - content_mid_point_y_in_image) # Cast to int for pixel precision

            paste_x_offset = current_content_x_on_canvas - info['content_left_x']
            
            layer = Image.new('RGBA', (combined_image.width, combined_image.height), (0, 0, 0, 0))
            layer.paste(img, (paste_x_offset, y_offset), img)

            combined_image = Image.alpha_composite(combined_image, layer)

            current_image_content_right_on_canvas = paste_x_offset + info['content_right_x']
            current_content_x_on_canvas = current_image_content_right_on_canvas + horizontal_spacing

        output_directory = os.path.dirname(output_path)
        if output_directory and not os.path.exists(output_directory):
            try:
                os.makedirs(output_directory)
                print(f"Created directory: {output_directory}")
            except OSError as e:
                print(f"Error creating directory {output_directory}: {e}")
                return None

        try:
            combined_image.save(output_path)
            print(f"Combined image saved to {output_path}")
        except Exception as e:
            print(f"Error saving combined image to {output_path}: {e}")
            return None

        return combined_image

# --- Example Usage ---
if __name__ == "__main__":
    """pokemon_urls = [
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/130.png",
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/38.png",
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/186.png"        
    ]

    # Define a relative directory to save the image
    output_dir = r"sprites"
    output_filename = "july_4th.png"

    # Create the 'sprites' directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
# Example 3: Center Alignment
    full_output_path_center = os.path.join(output_dir, output_filename)
    print(f"\n--- Combining images with 10px spacing (Center Aligned) ---")
    combiner_center = ImageCombiner(pokemon_urls)
    combined_img_center = combiner_center.combine_images(full_output_path_center, horizontal_spacing=10, vertical_align='center')
    if combined_img_center:
        print(f"Images combined with 10px spacing, center aligned. Process complete.")
"""
    whois_directory = ""