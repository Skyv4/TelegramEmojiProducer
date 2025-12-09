#!/usr/bin/env python3
"""
Test script to verify PIL properly scales GIF frames to 100x100 while preserving transparency.
"""

from PIL import Image
from pathlib import Path
import os


def test_pil_scaling_with_transparency(gif_path: Path, output_dir: Path, target_size: tuple = (100, 100)):
    """
    Extract first frame from GIF, scale it to target size, and verify transparency is preserved.
    """
    print(f"Testing PIL scaling with transparency preservation")
    print(f"Input: {gif_path}")
    print(f"Target size: {target_size}")
    print(f"=" * 60)
    
    with Image.open(gif_path) as im:
        print(f"\nOriginal GIF info:")
        print(f"  Size: {im.size}")
        print(f"  Mode: {im.mode}")
        print(f"  Format: {im.format}")
        print(f"  Has transparency: {im.info.get('transparency') is not None}")
        
        # Convert to RGBA to preserve transparency
        frame = im.convert('RGBA')
        print(f"\nAfter RGBA conversion:")
        print(f"  Size: {frame.size}")
        print(f"  Mode: {frame.mode}")
        
        # Scale the image using high-quality resampling
        scaled_frame = frame.resize(target_size, Image.Resampling.LANCZOS)
        print(f"\nAfter scaling to {target_size}:")
        print(f"  Size: {scaled_frame.size}")
        print(f"  Mode: {scaled_frame.mode}")
        
        # Check if alpha channel has any transparent pixels
        alpha_channel = scaled_frame.split()[3]  # Get alpha channel (4th channel in RGBA)
        alpha_values = list(alpha_channel.getdata())
        min_alpha = min(alpha_values)
        max_alpha = max(alpha_values)
        transparent_pixels = sum(1 for a in alpha_values if a < 255)
        total_pixels = len(alpha_values)
        
        print(f"\nAlpha channel analysis:")
        print(f"  Min alpha value: {min_alpha}")
        print(f"  Max alpha value: {max_alpha}")
        print(f"  Transparent pixels: {transparent_pixels}/{total_pixels} ({100*transparent_pixels/total_pixels:.1f}%)")
        
        # Save the scaled frame
        output_path = output_dir / "scaled_100x100_test.png"
        scaled_frame.save(output_path, 'PNG')
        print(f"\nSaved scaled frame to: {output_path}")
        print(f"File size: {os.path.getsize(output_path) / 1024:.2f}KB")
        
        # Verify the saved file
        with Image.open(output_path) as saved_im:
            print(f"\nVerifying saved file:")
            print(f"  Size: {saved_im.size}")
            print(f"  Mode: {saved_im.mode}")
            print(f"  Has alpha: {'A' in saved_im.mode}")
        
        if transparent_pixels > 0:
            print(f"\n✅ SUCCESS: Transparency is preserved! ({transparent_pixels} transparent pixels)")
        else:
            print(f"\n❌ WARNING: No transparent pixels found!")
        
        return output_path


if __name__ == '__main__':
    gif_path = Path('/home/a112/Documents/code/immutable/TelegramEmojis/backend/archive/gif/4744-pepe-cross.gif')
    output_dir = Path('/home/a112/Documents/code/immutable/TelegramEmojis')
    
    test_pil_scaling_with_transparency(gif_path, output_dir, target_size=(100, 100))
