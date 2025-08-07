import os
import time
from PIL import Image
import requests
from io import BytesIO

def color_to_black_png_and_save(image_url, output_filename):
    """
    Takes a PNG image from a URL, replaces all colored pixels with black pixels,
    preserving transparency, and saves the modified image to a specified file.

    Args:
        image_url (str): The URL of the PNG image.
        output_filename (str): The path and filename where the modified PNG will be saved.

    Returns:
        bool: True if the image was successfully processed and saved, False otherwise.
    """
    try:
        response = requests.get(image_url)
        response.raise_for_status()  # Raise an exception for bad status codes

        image_data = BytesIO(response.content)
        img = Image.open(image_data).convert("RGBA")  # Ensure RGBA for transparency

        width, height = img.size
        pixels = img.load()

        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]

                # Check if the pixel is not fully transparent and has some color
                if a > 0 and (r != 0 or g != 0 or b != 0):
                    pixels[x, y] = (0, 0, 0, a)  # Change to black, preserve original alpha

        img.save(output_filename, format="PNG")
        print(f"Modified image successfully saved to {output_filename}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error fetching image from URL: {e}")
        return False
    except IOError as e:
        print(f"Error processing or saving image: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

if __name__ == '__main__':
    print("\n--- Testing with an actual web URL ---")
    for i in range (277):
        i = i + 10000
        transparent_png_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/refs/heads/master/sprites/pokemon/{i+1}.png"
        output_web_filename = fr"C:\Users\kbren\source\repos\goomybot-v3\sprites\whois\{i+1}.png"

        success = color_to_black_png_and_save(transparent_png_url, output_web_filename)
        if success:
            print(f"Check '{output_web_filename}' to see the result.")
            time.sleep(.5)
        else:
            print("Web image processing failed.")