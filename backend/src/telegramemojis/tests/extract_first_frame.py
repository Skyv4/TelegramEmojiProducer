
from PIL import Image
import os

def extract_first_frame(gif_path, output_path):
    """
    Extracts the first frame from a GIF and saves it as a PNG, preserving transparency.
    """
    try:
        with Image.open(gif_path) as im:
            if im.info.get("transparency") is not None:
                # If the GIF has a transparency index, ensure it's preserved
                # Convert to RGBA to explicitly handle the alpha channel
                im = im.convert("RGBA")
            else:
                # If no transparency info, just convert to RGBA
                im = im.convert("RGBA")
            
            im.save(output_path, "PNG")
        print(f"Successfully extracted first frame from {gif_path} to {output_path}")
    except FileNotFoundError:
        print(f"Error: GIF file not found at {gif_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    gif_input_path = "/home/a112/Documents/code/immutable/TelegramEmojis/backend/archive/gif/4744-pepe-cross.gif"
    # Get the project root directory from the current working directory
    project_root = "/home/a112/Documents/code/immutable/TelegramEmojis/"
    output_file_name = "first_frame.png"
    output_full_path = os.path.join(project_root, output_file_name)

    extract_first_frame(gif_input_path, output_full_path)
