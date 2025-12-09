import unittest
import os
from pathlib import Path
from PIL import Image
import sys

# Add the src directory to the Python path to import main.py functions
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "telegramemojis"))

from main import process_png_for_transparency, hex_to_rgb

class TestTransparencyProcessing(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path("/home/a112/.gemini/tmp/42184351977895f3838ad9ace7d08f210dd2c41c34fd2d2c9700df3f0533401c")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.test_png_path = self.temp_dir / "test_image.png"
        self.bg_color_hex = "0xFFFFFF" # White background
        self.red_color = (255, 0, 0, 255) # Opaque red

    def tearDown(self):
        if self.test_png_path.exists():
            os.remove(self.test_png_path)
        # Clean up the temp directory if it's empty, or more robustly:
        # if self.temp_dir.exists() and not any(self.temp_dir.iterdir()):
        #     self.temp_dir.rmdir()

    def create_test_png(self, width=100, height=100, bg_color=(255, 255, 255, 255), include_red_square=True):
        img = Image.new('RGBA', (width, height), bg_color)
        if include_red_square:
            # Draw a red square in the middle
            for x in range(width // 4, 3 * width // 4):
                for y in range(height // 4, 3 * height // 4):
                    img.putpixel((x, y), self.red_color)
        img.save(self.test_png_path)

    def test_white_background_to_transparent(self):
        # Create a PNG with a white background and a red square
        self.create_test_png()

        # Process for transparency
        process_png_for_transparency(self.test_png_path, self.bg_color_hex, tolerance=10)

        # Load the processed image
        processed_img = Image.open(self.test_png_path).convert("RGBA")
        width, height = processed_img.size
        
        # Verify transparency in background areas
        bg_rgb = hex_to_rgb(self.bg_color_hex)
        for x in range(width):
            for y in range(height):
                pixel = processed_img.getpixel((x, y))
                if not (width // 4 <= x < 3 * width // 4 and height // 4 <= y < 3 * height // 4):
                    # This is a background pixel
                    self.assertLessEqual(pixel[3], 75, f"Background pixel at ({x},{y}) is not transparent enough (alpha: {pixel[3]})")
                else:
                    # This is part of the red square, should be mostly opaque
                    # Due to Gaussian blur, some edge pixels might have reduced alpha
                    self.assertGreaterEqual(pixel[3], 200, f"Red square pixel at ({x},{y}) has unexpected transparency (alpha: {pixel[3]})")
                    # Also check color, allowing for slight variations due to processing
                    self.assertAlmostEqual(pixel[0], self.red_color[0], delta=10)
                    self.assertAlmostEqual(pixel[1], self.red_color[1], delta=10)
                    self.assertAlmostEqual(pixel[2], self.red_color[2], delta=10)

    def test_no_background_color_present(self):
        # Create a PNG with a black background and a red square, try to remove white
        self.create_test_png(bg_color=(0, 0, 0, 255)) 

        # Process for transparency (removing white)
        process_png_for_transparency(self.test_png_path, self.bg_color_hex, tolerance=10)

        # Load the processed image
        processed_img = Image.open(self.test_png_path).convert("RGBA")
        width, height = processed_img.size

        # Verify no pixels became transparent (except potentially some edge anti-aliasing artifacts if any)
        for x in range(width):
            for y in range(height):
                pixel = processed_img.getpixel((x, y))
                # All pixels should be mostly opaque, as white was not present
                self.assertGreaterEqual(pixel[3], 200, f"Pixel at ({x},{y}) became transparent unexpectedly (alpha: {pixel[3]})")
                
                if not (width // 4 <= x < 3 * width // 4 and height // 4 <= y < 3 * height // 4):
                    # Black background area
                    self.assertAlmostEqual(pixel[0], 0, delta=10)
                    self.assertAlmostEqual(pixel[1], 0, delta=10)
                    self.assertAlmostEqual(pixel[2], 0, delta=10)

if __name__ == '__main__':
    unittest.main()
