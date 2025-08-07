import base64
from PIL import Image
import numpy as np
import os
import requests
from io import BytesIO

class Swapper():

    def __init__(self, IMG_BB_API_KEY):
        self.IMG_BB_API_KEY = IMG_BB_API_KEY
        self.IMG_BB_URL = 'https://api.imgbb.com/1/upload'
        self.palettes = [
            r"https://raw.githubusercontent.com/ultra-move/goomybot-v3/refs/heads/prod/sprites/swapped/input/dragon_palette.png",
            r"https://raw.githubusercontent.com/ultra-move/goomybot-v3/refs/heads/prod/sprites/swapped/input/electric_palette.png",
            r"https://raw.githubusercontent.com/ultra-move/goomybot-v3/refs/heads/prod/sprites/swapped/input/ghost_palette.png",
            r"https://raw.githubusercontent.com/ultra-move/goomybot-v3/refs/heads/prod/sprites/swapped/input/grass_palette.png",
            r"https://raw.githubusercontent.com/ultra-move/goomybot-v3/refs/heads/prod/sprites/swapped/input/water_palette.png",
        ]

    def load_image_rgba(self, path):
        return np.array(Image.open(path).convert("RGBA"))

    def extract_opaque_colors(self, img_array):
        pixels = img_array.reshape(-1, 4)
        opaque = pixels[pixels[:, 3] > 0]
        return np.unique(opaque[:, :3], axis=0)

    def remap_colors_randomly(self, target_img, source_palette):
        target_pixels = target_img.reshape(-1, 4)
        opaque_pixels = target_pixels[target_pixels[:, 3] > 0]
        target_palette = np.unique(opaque_pixels[:, :3], axis=0)
        # If source palette is too small, allow repeats by sampling with replacement
        sampled_source = source_palette[np.random.choice(len(source_palette), len(target_palette), replace=True)]
        mapping = {tuple(target): tuple(source) for target, source in zip(target_palette, sampled_source)}
        remapped = target_img.copy()
        for y in range(remapped.shape[0]):
            for x in range(remapped.shape[1]):
                r, g, b, a = remapped[y, x]
                if a == 0:
                    continue
                remapped[y, x, :3] = mapping.get((r, g, b), (r, g, b))
        return remapped

    def save_image(self, img_array, path):
        Image.fromarray(img_array, mode="RGBA").save(path)

    def save_image_from_url(self, url, save_path):
        """
        Synchronously downloads an image from a given URL and saves it.
        """
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with Image.open(BytesIO(response.content)) as img:
                img.save(save_path)
            print(f"Image downloaded from {url} and saved to {save_path}")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading image from {url}: {e}")
        except IOError as e:
            print(f"Error saving image to {save_path}: {e}")
            
    def mem_image_from_url(self, url):
        """
        Synchronously downloads an image from a given URL and returns it as a NumPy array.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            img_data = Image.open(BytesIO(response.content)).convert("RGBA")
            return np.array(img_data)
        except Exception as e:
            print(f"Error downloading or loading image from {url}: {e}")
            return None

    def generate_swap(self, source_url, target_url):
        """
        Synchronously generates a color-remapped image and returns it as a Base64 string.
        """
        source_img = self.mem_image_from_url(source_url)
        target_img = self.mem_image_from_url(target_url)

        if source_img is None or target_img is None:
            return None

        source_palette = self.extract_opaque_colors(source_img)
        remapped_array = self.remap_colors_randomly(target_img, source_palette)
        remapped_pil_image = Image.fromarray(remapped_array, mode="RGBA")
        buffer = BytesIO()
        remapped_pil_image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        return base64_image
    
    def generate_swap_bytes(self, source_url, target_url):
        """
        Synchronously generates a color-remapped image and returns it as a bytes object.
        """
        source_img = self.mem_image_from_url(source_url)
        target_img = self.mem_image_from_url(target_url)

        if source_img is None or target_img is None:
            return None

        source_palette = self.extract_opaque_colors(source_img)
        remapped_array = self.remap_colors_randomly(target_img, source_palette)
        remapped_pil_image = Image.fromarray(remapped_array, mode="RGBA")
        buffer = BytesIO()
        remapped_pil_image.save(buffer, format="PNG")
        image_bytes = BytesIO(buffer.getvalue())
        
        return image_bytes
        
    def upload_to_imgbb(self, base64_image_data):
        """
        Synchronously uploads a Base64 encoded image to ImgBB and returns the URL.
        """
        payload = {
            'key': self.IMG_BB_API_KEY,
            'image': base64_image_data
        }
        try:
            print("Uploading image to ImgBB...")
            response = requests.post(self.IMG_BB_URL, data=payload)
            response.raise_for_status()
            result = response.json()
            if result.get('success'):
                image_url = result['data']['url']
                print("Image uploaded successfully!")
                return image_url
            else:
                print(f"ImgBB upload failed: {result.get('error', {}).get('message', 'Unknown error')}")
                return None
        except Exception as e:
            print(f"An error occurred during the API call: {e}")
            return None