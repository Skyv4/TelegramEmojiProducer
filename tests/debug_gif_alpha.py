
import os
from pathlib import Path
from PIL import Image
import shutil

def debug_gif_extraction(gif_path: Path, output_dir: Path):
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    print(f"Debugging GIF: {gif_path}")
    
    with Image.open(gif_path) as im:
        print(f"Global Info: {im.info}")
        print(f"Global Mode: {im.mode}")
        
        try:
            frame_idx = 0
            while True:
                print(f"--- Frame {frame_idx} ---")
                print(f"Frame Info: {im.info}")
                print(f"Frame Mode: {im.mode}")
                
                # Logic from old.py
                frame = im.convert('RGBA')
                alphas = frame.getchannel('A')
                min_a, max_a = alphas.getextrema()
                print(f"Alpha range: {min_a}-{max_a}")
                
                if min_a == 0:
                     # Find first transparent pixel
                     data = frame.getdata()
                     for i, pixel in enumerate(data):
                         if pixel[3] == 0:
                             print(f"Sample Transparent Pixel (Frame {frame_idx}): {pixel}")
                             break
                
                if "transparency" in im.info:
                    transparent_color_index = im.info["transparency"]
                    print(f"Transparency Index: {transparent_color_index}")
                    
                    # REPLICATING THE BUGGY LOGIC
                    p_frame = im.copy().convert('P')
                    print(f"p_frame Mode: {p_frame.mode}")
                    
                    # Analyze if indices match
                    # Let's check the palette of p_frame vs im
                    im_palette = im.getpalette()
                    p_frame_palette = p_frame.getpalette()
                    
                    if im_palette == p_frame_palette:
                        print("Palette matches.")
                    else:
                        print("Palette MISMATCH! convert('P') likely generated a new palette.")
                        # This confirms the bug if printed.
                        
                    # Check if the transparent index in p_frame actually corresponds to transparency
                    # We can't easily know which pixel is SUPPOSED to be transparent without visual inspection,
                    # but if the palette changed, the index is almost certainly wrong.
                    
                    # Let's try to find a pixel with the transparent index
                    mask_data = [1 if pixel == transparent_color_index else 0 for pixel in p_frame.getdata()]
                    transparent_pixel_count = sum(mask_data)
                    print(f"Pixels matching index {transparent_color_index} in p_frame: {transparent_pixel_count}")

                else:
                    print("No transparency info in this frame.")
                
                # Save just the first few frames to inspect
                if frame_idx < 3:
                    frame.save(output_dir / f"frame_{frame_idx:04d}.png")
                
                # Attempt cleaning
                clean_bg = Image.new('RGBA', frame.size, (0, 0, 0, 0))
                # composite requires mask to be '1', 'L', or 'RGBA'. frame is RGBA, can be used as mask (uses alpha)
                cleaned_frame = Image.composite(frame, clean_bg, frame)
                
                print("Checking CLEANED frame...")
                data_clean = cleaned_frame.getdata()
                found_clean = False
                for i, pixel in enumerate(data_clean):
                     if pixel[3] == 0:
                         print(f"Sample Cleaned Pixel (Frame {frame_idx}): {pixel}")
                         found_clean = True
                         break
                
                frame_idx += 1
                if frame_idx >= 2: break # Limit to 2 frames for debug
                try:
                    im.seek(im.tell() + 1)
                except EOFError:
                    break
        except EOFError:
            pass

if __name__ == "__main__":
    gif_path = Path("input/moving/4744-pepe-cross.gif")
    output_dir = Path("debug_output")
    if gif_path.exists():
        debug_gif_extraction(gif_path, output_dir)
    else:
        print(f"File not found: {gif_path}")
