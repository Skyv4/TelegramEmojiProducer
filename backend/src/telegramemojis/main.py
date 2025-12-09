import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import magic # python-magic library
from PIL import Image

def setup_directories(base_path: Path):
    """Ensures input, output, and archive directories exist."""
    dirs = {
        "input_moving": base_path / "input" / "moving",
        "input_static": base_path / "input" / "static",
        "output_webm": base_path / "output" / "webm", # Changed from output_gif
        "output_static": base_path / "output" / "static",
        "archive_webm": base_path / "archive" / "webm", # Changed from archive_gif
        "archive_static": base_path / "archive" / "static",
        "archive_gif": base_path / "archive" / "gif", # Ensure archive/gif is also created
    }

    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    
    return dirs

def check_ffmpeg_installed():
    """Checks if ffmpeg and ffprobe are installed."""
    for cmd in ["ffmpeg", "ffprobe"]:
        if shutil.which(cmd) is None:
            print(f"Error: {cmd} is not installed or not in PATH.")
            print("Please install ffmpeg (which includes ffprobe) to use this script.")
            return False
    return True

def is_gif_or_video(file_path: Path) -> bool:
    """Checks if a file is a GIF or a common video format using python-magic."""
    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(str(file_path))
        return file_type.startswith("image/gif") or file_type.startswith("video/")
    except Exception as e:
        print(f"Error checking file type for {file_path}: {e}")
        return False

def is_gif(file_path: Path) -> bool:
    """Checks if a file is specifically a GIF using python-magic."""
    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(str(file_path))
        return file_type.startswith("image/gif")
    except Exception as e:
        print(f"Error checking file type for {file_path}: {e}")
        return False

def has_alpha_channel(file_path: Path) -> bool:
    """Checks if a video file has an alpha channel."""
    command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "V:0",
        "-show_entries", "stream=pix_fmt",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        pix_fmt = result.stdout.strip()
        # Common pixel formats with alpha channel
        return "rgba" in pix_fmt or "bgra" in pix_fmt or "yuva" in pix_fmt
    except Exception as e:
        print(f"Error checking alpha channel for {file_path}: {e}")
        return False





def get_video_duration(file_path: Path) -> float:
    """Gets the duration of a video file using ffprobe."""
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting duration for {file_path}: {e}")
        return 0.0

def extract_gif_frames_with_transparency(gif_path: Path, output_dir: Path) -> tuple[list[Path], float]:
    """
    Extracts all frames from a GIF, preserving transparency using PIL.
    This is necessary because ffmpeg's GIF decoder doesn't properly convert
    GIF's palette-based transparency to WebM's alpha channel.
    
    Returns a list of PNG file paths and the frame duration in seconds.
    """
    frames = []
    frame_paths = []
    
    with Image.open(gif_path) as im:
        # Get frame duration (in milliseconds)
        frame_duration_ms = im.info.get('duration', 100)  # Default to 100ms if not specified
        frame_duration_sec = frame_duration_ms / 1000.0
        
        try:
            frame_idx = 0
            while True:
                # Convert frame to RGBA to ensure alpha channel
                frame = im.convert('RGBA')
                
                # Save frame as PNG (which preserves alpha)
                frame_path = output_dir / f"frame_{frame_idx:04d}.png"
                frame.save(frame_path, 'PNG')
                frame_paths.append(frame_path)
                
                frame_idx += 1
                im.seek(im.tell() + 1)
        except EOFError:
            # End of GIF
            pass
    
    print(f"Extracted {len(frame_paths)} frames from {gif_path.name} (frame duration: {frame_duration_sec}s)")
    
    return frame_paths, frame_duration_sec

def encode_frames_to_webm(frame_dir: Path, output_path: Path, max_duration_sec: float = 2.84, target_side_length: int = 512, crf: int = 30) -> Path:
    """
    Encodes PNG frames to WebM with alpha channel support, scaled to target_side_length,
    using a complex filtergraph for robust transparency handling.
    """
    fixed_fps = 30.0 # Telegram specification
    max_frames = int(fixed_fps * max_duration_sec)

    # Define the complex filtergraph for explicit alpha channel handling
    complex_filter = f"[0:v]scale={target_side_length}:{target_side_length}[scaled];"\
                     f"[scaled]split[rgb][alpha];"\
                     f"[alpha]alphaextract[alphachan];"\
                     f"[rgb][alphachan]alphamerge,format=yuva420p"

    command = [
        'ffmpeg',
        '-framerate', str(fixed_fps),
        '-i', str(frame_dir / 'frame_%04d.png'),
        '-frames:v', str(max_frames),
        '-filter_complex', complex_filter,
        '-c:v', 'libvpx-vp9',
        '-profile:v', '0',
        '-level', '3.1',
        '-pix_fmt', 'yuva420p',
        '-metadata:s:v:0', 'alpha_mode=1',
        '-crf', str(crf),
        '-auto-alt-ref', '1',
        '-b:v', '0',
        '-an',
        '-y',
        str(output_path)
    ]
    
    print(f"Encoding {max_frames} frames to WebM with transparency (target_side_length={target_side_length}, fps={fixed_fps}, crf={crf})...")
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Successfully encoded to {output_path.name} ({os.path.getsize(output_path) / 1024:.2f}KB)")
        print(f"ffmpeg stdout: {result.stdout}")
        print(f"ffmpeg stderr: {result.stderr}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error encoding frames: {e}")
        print(f"stderr: {e.stderr}")
        raise


def convert_gif_to_webm_with_transparency(gif_path: Path, output_path: Path, max_duration_sec: float = 2.84, target_side_length: int = 512, fixed_fps: float = 30.0) -> Path:
    """
    Converts a GIF to WebM while preserving transparency.
    Uses PIL to extract frames (which properly handles GIF transparency)
    and then encodes them to WebM with alpha channel.
    """
    print(f"\n{'='*60}")
    print(f"Converting GIF {gif_path.name} with transparency preservation")
    print(f"{'='*60}\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        frame_paths, frame_duration_sec = extract_gif_frames_with_transparency(gif_path, temp_path)
        
        if not frame_paths:
            raise ValueError(f"No frames extracted from {gif_path}")
        
        # Now encode the frames to WebM
        encode_frames_to_webm(temp_path, output_path, max_duration_sec=max_duration_sec, target_side_length=target_side_length, crf=30)
    
    print(f"GIF conversion complete: {output_path.name} ({os.path.getsize(output_path) / 1024:.2f}KB)\n")
    return output_path


def convert_to_webm_intermediate(input_path: Path, output_path: Path, max_duration_sec: int = 3, target_side_length: int = 512, fixed_fps: float = 30.0, colorkey_hex: str = None) -> Path:
    """
    Converts any input (GIF/video/PNG sequence) to an intermediate WebM,
    trims to max_duration_sec, and rescales to Telegram sticker/emoji dimensions.
    """
    print(f"Converting {input_path.name} to intermediate WebM (target_side_length={target_side_length}, fps={fixed_fps}) and trimming to {max_duration_sec} seconds...")

    # Determine scaling filter based on target_side_length
    if target_side_length == 100: # For emoji, exact 100x100
        scale_filter = f"scale={target_side_length}:{target_side_length}"
    else: # For stickers, scale to max_dim on one side, preserve aspect ratio
        scale_filter = f"scale='min({target_side_length},iw)':'min({target_side_length},ih)':force_original_aspect_ratio=decrease"

    vf_filters = []
    if colorkey_hex:
        vf_filters.append(f"colorkey={colorkey_hex}:similarity=0.1:blend=0.2")
    vf_filters.append(scale_filter)
    vf_filters.append(f"format=yuva420p") # Explicitly add format filter to ensure alpha
    vf_string = ",".join(vf_filters)

    command = [
        "ffmpeg",
        "-i", str(input_path),
        "-ss", "0",
        "-t", str(max_duration_sec),
        "-vf", vf_string,
        "-c:v", "libvpx-vp9",
        "-profile:v", "0",
        "-level", "3.1",
        "-pix_fmt", "yuva420p",
        "-metadata:s:v:0", "alpha_mode=1",
        "-auto-alt-ref", "1",
        "-crf", "30",
        "-b:v", "0",
        "-an",
        "-loop", "0",
        "-y",
        str(output_path),
    ]
    # Add -r (framerate) only if input is not image sequence or already has desired fps. To avoid re-encoding if not needed.
    # For simplicity, we'll always apply it, trusting ffmpeg to optimize if source matches.
    command.insert(2, '-r')
    command.insert(3, str(fixed_fps))

    try:
        result = subprocess.run(command, check=True, capture_output=True)
        print(f"Successfully converted and trimmed to {output_path.name}")
        print(f"ffmpeg stdout: {result.stdout.decode()}")
        print(f"ffmpeg stderr: {result.stderr.decode()}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error converting/trimming {input_path.name}: {e}")
        print(f"stdout: {e.stdout.decode()}")
        print(f"stderr: {e.stderr.decode()}")
        raise


def optimize_webm_size(input_path: Path, output_path: Path, target_size_kb: int = 64) -> Path:
    """
    Iteratively adjusts WebM quality to meet a target file size using ffmpeg.
    Target is 64KB, Telegram also recommends 512x512px and 30fps.
    """
    print(f"Optimizing WebM size for {input_path.name} to target {target_size_kb}KB...")
    
    best_effort_size = os.path.getsize(input_path)
    best_effort_path = input_path # Start with original if everything fails

    # Parameters to iterate
    # CRF: 0-63 (lower is better quality, larger file)
    # Target bitrate: in kbps (higher is better quality, larger file)
    # Telegram stickers are typically 512x512, 30fps. Already handled by intermediate conversion.

    # We need a temporary file for each attempt
    temp_output_base = output_path.parent / (output_path.stem + "_temp_opt")

    # Iterate through CRF values (higher CRF = lower quality = smaller file)
    # A good starting point for webm for decent quality is ~20-30.
    for crf in range(25, 45, 5): # Iterate from good quality to lower quality
        current_temp_output = temp_output_base.with_suffix(f".crf{crf}.webm")
        command = [
            "ffmpeg",
            "-i", str(input_path),
            "-vf", "format=yuva420p",  # Force alpha channel preservation
            "-c:v", "libvpx-vp9",
            "-profile:v", "0",
            "-level", "3.1",
            "-crf", str(crf),
            "-pix_fmt", "yuva420p",
            "-metadata:s:v:0", "alpha_mode=1",
            "-auto-alt-ref", "1",
            "-b:v", "0",
            "-an",
            "-y",
            str(current_temp_output),
        ]
        
        try:
            result = subprocess.run(command, check=True, capture_output=True)
            current_file_size = os.path.getsize(current_temp_output)
            print(f"Generated {current_temp_output.name} with size {current_file_size / 1024:.2f}KB (CRF={crf}).")
            print(f"ffmpeg stdout: {result.stdout.decode()}")
            print(f"ffmpeg stderr: {result.stderr.decode()}")

            if current_file_size <= target_size_kb * 1024:
                print(f"Successfully optimized {input_path.name} to {current_file_size / 1024:.2f}KB.")
                shutil.move(current_temp_output, output_path)
                return output_path
            
            # Keep track of the best effort so far (smallest file if target not met)
            if current_file_size < best_effort_size:
                best_effort_size = current_file_size
                best_effort_path = current_temp_output
            else:
                # If increasing CRF didn't help or made it worse, we might be at a local minimum,
                # or further increasing CRF might lead to unacceptable quality.
                # Remove this temp file as it's not the best effort.
                if current_temp_output.exists():
                    current_temp_output.unlink()

        except subprocess.CalledProcessError as e:
            print(f"Error optimizing {input_path.name} with CRF={crf}: {e}")
            if current_temp_output.exists():
                current_temp_output.unlink()
            # Continue trying other CRFs
        finally:
            if current_temp_output.exists():
                current_temp_output.unlink()
    
    # Final cleanup of any lingering best_effort_path if it's not the final output
    if output_path.exists() and best_effort_path.exists() and output_path != best_effort_path:
        best_effort_path.unlink()

    # If target size is still not met, move the best_effort_path to the final output_path
    if best_effort_path.exists():
        print(f"Could not meet target size for {input_path.name}. Best effort is {best_effort_size / 1024:.2f}KB.")
        shutil.move(best_effort_path, output_path)
        return output_path
    
    print(f"Failed to optimize {input_path.name}. Returning original file as best effort.")
    return input_path


def convert_to_telegram_sticker(input_path: Path, output_dir: Path, conversion_type: str = "sticker", colorkey_hex: str = None) -> Path:
    """
    Converts a GIF/Video to Telegram sticker or emoji standards (WebM):
    - Less than 3 seconds.
    - No background color (transparent).
    - Less than 256KB.
    - For stickers: 512px on one side, other side 512px or less, 30fps.
    - For emoji: exactly 100x100px, 30fps.
    """
    print(f"\nProcessing {input_path.name} as a Telegram {conversion_type}...")
    
    max_duration_sec = 2.84
    
    if conversion_type == "sticker":
        target_side_length = 512
        fixed_fps = 30.0
    elif conversion_type == "emoji":
        target_side_length = 100
        fixed_fps = 30.0
    else:
        raise ValueError(f"Invalid conversion_type: {conversion_type}. Must be 'sticker' or 'emoji'.")

    print(f"Target side length: {target_side_length}px, fixed FPS: {fixed_fps}fps")
    intermediate_webm_path = output_dir / f"{input_path.stem}_intermediate.webm"

    if is_gif(input_path):
        print(f"Detected GIF format - using PIL extraction to preserve transparency")
        try:
            current_processed_path = convert_gif_to_webm_with_transparency(
                input_path,
                intermediate_webm_path,
                max_duration_sec=max_duration_sec,
                target_side_length=target_side_length,
                fixed_fps=fixed_fps
            )
        except Exception as e:
            print(f"Failed to convert GIF {input_path.name}: {e}")
            return None
    else:
        print(f"Detected video format - using ffmpeg conversion")
        try:
            current_processed_path = convert_to_webm_intermediate(
                input_path, 
                intermediate_webm_path, 
                max_duration_sec=max_duration_sec, 
                target_side_length=target_side_length,
                fixed_fps=fixed_fps,
                colorkey_hex=colorkey_hex,
            )
        except Exception as e:
            print(f"Failed to convert to intermediate WebM and trim {input_path.name}: {e}")
            return None
    
    # Optimize size and ensure transparency
    final_output_path = output_dir / f"{input_path.stem}.webm"
    target_size_kb = 256 # Telegram video sticker/emoji limit
    try:
        final_output_path = optimize_webm_size(current_processed_path, final_output_path, target_size_kb=target_size_kb)
        if final_output_path != current_processed_path and current_processed_path.exists():
            current_processed_path.unlink()
    except Exception as e:
        print(f"Failed to optimize size for {input_path.name}: {e}")
        if current_processed_path.exists(): current_processed_path.unlink()
        return None
    
    print(f"Successfully converted {input_path.name} to {final_output_path.name} ({os.path.getsize(final_output_path) / 1024:.2f}KB)")
    return final_output_path


def main():
    parser = argparse.ArgumentParser(description="Convert GIFs/Videos to Telegram sticker standards.")
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Base path for input, output, and archive directories (default: current directory).",
    )
    parser.add_argument(
        "--bg-color",
        type=str,
        help="Optional: Hexadecimal color code (e.g., '0xFFFFFF' for white) to make transparent for GIFs. Overrides default white background removal.",
        default=None,
    )
    parser.add_argument(
        "--conversion-type",
        type=str,
        default="emoji",
        choices=["sticker", "emoji"],
        help="Type of Telegram element to convert to: 'sticker' (512px) or 'emoji' (100x100px). Defaults to 'sticker'.",
    )
    args = parser.parse_args()

    base_path = Path(args.path).resolve()
    dirs = setup_directories(base_path)

    if not check_ffmpeg_installed():
        return

    print(f"Monitoring input directories: {dirs['input_moving']} and {dirs['input_static']}")
    print(f"Outputting to: {dirs['output_webm']} and {dirs['output_static']}") # Changed output dir
    print(f"Archiving to: {dirs['archive_webm']} and {dirs['archive_static']}") # Changed archive dir

    input_dirs = [dirs["input_moving"], dirs["input_static"]]
    output_webm_dir = dirs["output_webm"] # Changed output dir variable
    archive_webm_dir = dirs["archive_webm"] # Archive for original webm inputs
    archive_gif_dir = dirs["archive_gif"] # Archive for original gif inputs

    for input_dir in input_dirs:
        print(f"\nScanning {input_dir} for GIFs/Videos...")
        for media_file in input_dir.iterdir():
            if media_file.is_file() and is_gif_or_video(media_file):
                colorkey_to_apply = None
                if is_gif(media_file):
                    if has_alpha_channel(media_file):
                        colorkey_to_apply = None
                    elif args.bg_color:
                        colorkey_to_apply = args.bg_color
                    else:
                        colorkey_to_apply = '0xFFFFFF'  
                try:
                    converted_path = convert_to_telegram_sticker(media_file, output_webm_dir, conversion_type=args.conversion_type, colorkey_hex=colorkey_to_apply)
                    if converted_path:
                        target_archive_dir = archive_gif_dir if is_gif(media_file) else archive_webm_dir
                        print(f"Moving original {media_file.name} to {target_archive_dir}")
                        shutil.move(str(media_file), str(target_archive_dir / media_file.name))
                except Exception as e:
                    print(f"Error processing {media_file.name}: {e}")
            elif media_file.is_file():
                print(f"Skipping non-GIF/video file: {media_file.name}")


if __name__ == "__main__":
    main()