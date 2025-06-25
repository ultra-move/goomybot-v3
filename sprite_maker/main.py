from PIL import Image
import requests
from io import BytesIO
import os # Import the os module for path operations

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

    def combine_images(self, output_path="combined_image.png", horizontal_spacing=0):
        """
        Downloads all images from the provided URLs, resizes them to the smallest
        common overall height, and combines them side-by-side into a single image,
        aligning their visible content to a common bottom line.

        Args:
            output_path (str): The full path and filename to save the combined image,
                                including the directory.
            horizontal_spacing (int): The horizontal spacing between images in pixels.
                                      Use a positive value for gaps, 0 for touching,
                                      and a negative value for overlapping.

        Returns:
            PIL.Image.Image: The combined image object.
        """
        if not self.urls:
            print("No URLs provided to combine.")
            return None

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

        # Convert all images to RGBA and find the minimum overall height
        # This min_overall_height will be the height of our final combined canvas
        processed_images = []
        for img in images:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            processed_images.append(img)

        # Find the minimum *overall* height (including transparency) among all images.
        min_overall_height = min(img.height for img in processed_images)

        resized_images_info = [] # Store (resized_img, content_bottom_y_in_resized_img)
        for img in processed_images:
            # Resize image to the common minimum overall height
            if img.height != min_overall_height:
                width = int(img.width * min_overall_height / img.height)
                if width == 0: width = 1 # Ensure width is at least 1 to avoid errors
                resized_img = img.resize((width, min_overall_height), Image.LANCZOS)
            else:
                resized_img = img

            # Find the bounding box of the *actual content* (non-transparent pixels)
            # of the resized image. bbox is (left, upper, right, lower).
            bbox = resized_img.getbbox()
            
            # The 'lower' value of the bbox is the y-coordinate of the content's bottom edge
            # relative to the resized image's top (y=0).
            # If bbox is None, the image is fully transparent, so its "content bottom"
            # is considered the image's full height, aligning it to the canvas bottom.
            if bbox:
                content_bottom_y_in_resized_img = bbox[3] 
            else:
                content_bottom_y_in_resized_img = resized_img.height # Fully transparent image

            resized_images_info.append({
                'image': resized_img,
                'content_bottom_y': content_bottom_y_in_resized_img
            })

        # Determine the target common bottom y-coordinate on the combined canvas.
        # This will be the maximum content_bottom_y found among all resized images.
        # This ensures all images' visible content bottoms are aligned to this line.
        target_content_bottom_y = max(info['content_bottom_y'] for info in resized_images_info)
        
        # Calculate total width of the combined image
        total_width = sum(info['image'].width for info in resized_images_info)
        if len(resized_images_info) > 1:
            total_width += (len(resized_images_info) - 1) * horizontal_spacing

        # Create the final combined image with a fully transparent background.
        combined_image = Image.new('RGBA', (total_width, min_overall_height), (0, 0, 0, 0))

        x_offset = 0
        for info in resized_images_info:
            img = info['image']
            content_bottom_y = info['content_bottom_y']

            # Calculate the y_offset needed to align this image's content bottom
            # with the shared target_content_bottom_y.
            y_offset = target_content_bottom_y - content_bottom_y

            # Create a temporary blank layer the size of the combined image
            layer = Image.new('RGBA', (total_width, min_overall_height), (0, 0, 0, 0))
            
            # Paste the current image onto its specific spot on the layer with the calculated y_offset.
            # The img itself serves as the mask when pasting an RGBA image onto another RGBA layer.
            layer.paste(img, (x_offset, y_offset), img)

            # Alpha composite the layer onto the main combined image.
            # This correctly blends the current image, respecting its alpha channel,
            # and prevents parts of previously pasted images from being "erased".
            combined_image = Image.alpha_composite(combined_image, layer)

            x_offset += img.width + horizontal_spacing

        # Ensure the output directory exists before saving
        output_directory = os.path.dirname(output_path)
        if output_directory and not os.path.exists(output_directory):
            try:
                os.makedirs(output_directory)
                print(f"Created directory: {output_directory}")
            except OSError as e:
                print(f"Error creating directory {output_directory}: {e}")
                return None

        # Save the final combined image
        try:
            combined_image.save(output_path)
            print(f"Combined image saved to {output_path}")
        except Exception as e:
            print(f"Error saving combined image to {output_path}: {e}")
            return None

        return combined_image

# --- Example Usage ---
if __name__ == "__main__":
    pokemon_urls = [
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/1.png",
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/4.png", 
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/7.png", 
    ]

    # Define a relative directory to save the image
    output_dir = "sprites"
    output_filename = "kanto_starters.png"


    # Create the 'sprites' directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    full_output_path_overlapping = os.path.join(output_dir, output_filename)

    horizontal_spacing = -60
    print(f"\n--- Combining images with {horizontal_spacing} spacing (overlapping) ---")
    combiner_overlapping = ImageCombiner(pokemon_urls)
    combined_img_overlapping = combiner_overlapping.combine_images(full_output_path_overlapping, horizontal_spacing=horizontal_spacing)
    if combined_img_overlapping:
        print("Images overlapping process complete.")
