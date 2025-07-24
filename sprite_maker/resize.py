from PIL import Image
import os

def scale_png_to_96x96(input_folder, output_folder):
    """
    Scales down all PNG images in the input_folder to 96x96 pixels
    and saves them to the output_folder.

    Args:
        input_folder (str): The path to the folder containing the original PNG images.
        output_folder (str): The path to the folder where scaled images will be saved.
    """

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".png"):
            input_filepath = os.path.join(input_folder, filename)
            output_filepath = os.path.join(output_folder, filename)

            try:
                with Image.open(input_filepath) as img:
                    # Resize the image to 96x96 pixels
                    # Image.LANCZOS is a high-quality downsampling filter
                    img = img.resize((96, 96), Image.LANCZOS)
                    img.save(output_filepath)
                    print(f"Scaled '{filename}' and saved to '{output_filepath}'")
            except Exception as e:
                print(f"Error processing '{filename}': {e}")

if __name__ == "__main__":
    # --- Configuration ---
    # Create a subfolder named 'input_pngs' in the same directory as the script
    # and put your PNGs there.
    input_directory = r"C:\Users\kbren\source\repos\goomybot-v3\sprites\resize_input"

    # Create a subfolder named 'output_96x96' for the scaled images
    output_directory = r"C:\Users\kbren\source\repos\goomybot-v3\sprites\resize_output"
    # -------------------

    if os.listdir(input_directory) == []:
        print(f"The '{input_directory}' folder is empty. Please add some PNG images to it.")
    else:
        print(f"\nScaling PNGs from '{input_directory}' to '{output_directory}'...")
        scale_png_to_96x96(input_directory, output_directory)
        print("\nScaling complete!")
        print(f"Check the '{output_directory}' folder for your scaled images.")
