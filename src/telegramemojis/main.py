import argparse
import os
import shutil
import subprocess
from pathlib import Path
import tempfile 
import magic 

# --- Setup and Utility Functions (Omitted for brevity, but assumed to be unchanged) ---

def setup_directories(base_path: Path):
    """Ensures input, output, and archive directories exist."""
    dirs = {
        "input_moving": base_path / "input" / "moving",
        "input_static": base_path / "input" / "static",
        "output_webm": base_path / "output" / "webm", 
        "output_static": base_path / "output" / "static",
        "archive_webm": base_path / "archive" / "webm", 
        "archive_static": base_path / "archive" / "static",
        "archive_gif": base_path / "archive" / "gif", 
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

def convert_to_webm_intermediate(input_path: Path, output_path: Path, max_duration_sec: float = 2.84) -> Path:
    """
    Converts any input (original video or PNG sequence) to an intermediate WebM,
    trims to max_duration_sec, and rescales to Telegram sticker dimensions.
    """
    print(f"Converting {input_path.name} to intermediate WebM and trimming to {max_duration_sec} seconds...")

    # Set input parameters based on whether the input is a file or a PNG sequence pattern
    if "%" in input_path.name: # Indicates a frame sequence pattern (e.g., frame%04d.png)
        input_for_webm = str(input_path)
        input_format_param = ["-i"]
    else:
        input_for_webm = str(input_path)
        input_format_param = ["-i"]


    # Get original dimensions to set initial scale and maintain aspect ratio
    probe_dim_command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "V:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0:s=x",
        str(input_path)
    ]
    try:
        dim_result = subprocess.run(probe_dim_command, check=True, capture_output=True, text=True)
        width, height = map(int, dim_result.stdout.strip().split('x'))
    except Exception:
        print(f"Could not determine dimensions for {input_path.name}, falling back to 100x100 max.")
        width, height = 100, 100 # Fallback if cannot determine dimensions

    telegram_max_dim = 100 
    if max(width, height) <= telegram_max_dim:
        scaled_width, scaled_height = width, height
    elif width >= height:
        scaled_width = telegram_max_dim
        scaled_height = int(height * (telegram_max_dim / width))
    else:
        scaled_height = telegram_max_dim
        scaled_width = int(width * (telegram_max_dim / height))
    
    # Ensure dimensions are even for ffmpeg compatibility
    scaled_width = scaled_width if scaled_width % 2 == 0 else scaled_width - 1
    scaled_height = scaled_height if scaled_height % 2 == 0 else scaled_height - 1

    command = [
        "ffmpeg",
    ] + input_format_param + [input_for_webm,
        "-ss", "0",
        "-t", str(max_duration_sec),
        # format=rgba is critical here if input is a video, but it's redundant/harmless if input is already PNG sequence
        # The key is converting to yuva420p for the final VP9 encode
        "-vf", f"format=rgba,scale={scaled_width}:{scaled_height}:flags=lanczos,format=yuva420p", 
        "-c:v", "libvpx-vp9", 
        "-pix_fmt", "yuva420p", 
        "-metadata:s:v:0", "alpha_mode=1", 
        "-an", 
        "-y", 
        str(output_path),
    ]
    print(f"FFmpeg command in convert_to_webm_intermediate: {' '.join(command)}")
    print(f"Input for WebM: {input_for_webm}")
    try:
        subprocess.run(command, check=True, capture_output=True)
        print(f"Successfully converted and trimmed to {output_path.name}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error converting/trimming {input_path.name}: {e}")
        print(f"stdout: {e.stdout.decode()}")
        print(f"stderr: {e.stderr.decode()}")
        raise


def optimize_webm_size(input_path: Path, output_path: Path, target_size_kb: int = 64) -> Path:
    """
    Iteratively adjusts WebM quality to meet a target file size using ffmpeg.
    (Omitted for brevity, assumed to be unchanged)
    """
    print(f"Optimizing WebM size for {input_path.name} to target {target_size_kb}KB...")
    
    best_effort_size = os.path.getsize(input_path)
    best_effort_path = input_path 

    temp_output_base = output_path.parent / (output_path.stem + "_temp_opt")

    # Iterate through CRF values (higher CRF = lower quality = smaller file)
    for crf in range(25, 45, 5): 
        current_temp_output = temp_output_base.with_suffix(f".crf{crf}.webm")
        command = [
            "ffmpeg",
            "-i", str(input_path),
            "-c:v", "libvpx-vp9",
            "-crf", str(crf),
            "-pix_fmt", "yuva420p",
            "-metadata:s:v:0", "alpha_mode=1",
            "-an",
            "-loop", "0",
            "-y",
            str(current_temp_output),
        ]
        
        try:
            subprocess.run(command, check=True, capture_output=True)
            current_file_size = os.path.getsize(current_temp_output)
            print(f"Generated {current_temp_output.name} with size {current_file_size / 1024:.2f}KB (CRF={crf}).")

            if current_file_size <= target_size_kb * 1024:
                print(f"Successfully optimized {input_path.name} to {current_file_size / 1024:.2f}KB.")
                shutil.move(current_temp_output, output_path)
                return output_path
            
            if current_file_size < best_effort_size:
                best_effort_size = current_file_size
                best_effort_path = current_temp_output
            else:
                if current_temp_output.exists():
                    current_temp_output.unlink()

        except subprocess.CalledProcessError as e:
            print(f"Error optimizing {input_path.name} with CRF={crf}: {e}")
            if current_temp_output.exists():
                current_temp_output.unlink()

    # If target not met, try scaling down dimensions further 
    if best_effort_size > target_size_kb * 1024 and best_effort_path.exists():
        print(f"Target size not met with CRF. Trying additional scaling down...")
        probe_dim_command = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "V:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0:s=x",
            str(best_effort_path)
        ]
        try:
            dim_result = subprocess.run(probe_dim_command, check=True, capture_output=True, text=True)
            current_width, current_height = map(int, dim_result.stdout.strip().split('x'))
        except Exception:
            current_width, current_height = 512, 512 # Fallback
        
        for scale_percentage in range(90, 40, -10): 
            new_width = int(current_width * scale_percentage / 100)
            new_height = int(current_height * scale_percentage / 100)
            new_width = max(1, new_width if new_width % 2 == 0 else new_width - 1)
            new_height = max(1, new_height if new_height % 2 == 0 else new_height - 1)

            if new_width == 0 or new_height == 0:
                continue

            current_temp_output = temp_output_base.with_suffix(f".scale{scale_percentage}.webm")
            print(f"Trying with scale {scale_percentage}% ({new_width}x{new_height})...")
            command = [
                "ffmpeg",
                "-i", str(input_path), 
                "-vf", f"scale={new_width}:{new_height}:flags=lanczos,format=yuva420p",
                "-c:v", "libvpx-vp9",
                "-crf", "30", 
                "-pix_fmt", "yuva420p",
                "-metadata:s:v:0", "alpha_mode=1",

                "-an",
                "-loop", "0",
                "-y",
                str(current_temp_output),
            ]
            try:
                subprocess.run(command, check=True, capture_output=True)
                current_file_size = os.path.getsize(current_temp_output)
                print(f"Generated {current_temp_output.name} with size {current_file_size / 1024:.2f}KB.")

                if current_file_size <= target_size_kb * 1024:
                    print(f"Successfully optimized {input_path.name} to {current_file_size / 1024:.2f}KB.")
                    shutil.move(current_temp_output, output_path)
                    if best_effort_path.exists() and best_effort_path != input_path: best_effort_path.unlink()
                    return output_path
                
                if current_file_size < best_effort_size:
                    best_effort_size = current_file_size
                    best_effort_path = current_temp_output
                else:
                    if current_temp_output.exists():
                        current_temp_output.unlink()

            except subprocess.CalledProcessError as e:
                print(f"Error optimizing {input_path.name} with scale={scale_percentage}%: {e}")
                if current_temp_output.exists():
                    current_temp_output.unlink()
    
    if best_effort_path.exists():
        print(f"Could not meet target size for {input_path.name}. Best effort is {best_effort_size / 1024:.2f}KB.")
        shutil.move(best_effort_path, output_path)
        return output_path
    
    print(f"Failed to optimize {input_path.name}. Returning original file as best effort.")
    return input_path


def convert_to_telegram_sticker(input_path: Path, output_dir: Path) -> Path:
    """
    Converts a GIF/Video to Telegram sticker standards (WebM).
    - **GIFs are first converted to a series of transparent RGBA PNGs.**
    """
    print(f"\nProcessing {input_path.name}...")
    
    current_input_for_webm = input_path
    
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir_for_png_frames = Path(temp_dir_str)

        if is_gif(input_path):
            print(f"Detected GIF. Extracting frames to PNG sequence for robust transparency (RGBA encoding)...")
            
            # This is the step you requested: encoding the GIF to a series of RGBA frames.
            png_sequence_path = temp_dir_for_png_frames / "frame%04d.png"
            png_command = [
                "ffmpeg",
                "-i", str(input_path),
                "-pix_fmt", "rgba", # Ensures alpha channel is explicitly mapped for PNG output
                "-y",
                str(png_sequence_path)
            ]
            try:
                subprocess.run(png_command, check=True, capture_output=True)
                # The input for the next step is now the PNG sequence pattern
                current_input_for_webm = png_sequence_path 
                print(f"Successfully extracted frames to {current_input_for_webm}")
            except subprocess.CalledProcessError as e:
                print(f"Error extracting GIF frames for {input_path.name}: {e.stderr.decode()}")
                return None

        # Convert to intermediate WebM, trim, and initial scale
        intermediate_webm_path = output_dir / f"{input_path.stem}_intermediate.webm"
        try:
            # Pass the input_path or the PNG sequence path
            current_processed_path = convert_to_webm_intermediate(current_input_for_webm, intermediate_webm_path, max_duration_sec=2.84)
        except Exception as e:
            print(f"Failed to convert to intermediate WebM and trim {input_path.name}: {e}")
            return None
        
        # Optimize size and ensure transparency
        final_output_path = output_dir / f"{input_path.stem}.webm"
        try:
            final_output_path = optimize_webm_size(current_processed_path, final_output_path)
            # Clean up intermediate file if it was modified and is not the final output
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
    args = parser.parse_args()

    base_path = Path(args.path).resolve()
    dirs = setup_directories(base_path)

    if not check_ffmpeg_installed():
        return

    print(f"Monitoring input directories: {dirs['input_moving']} and {dirs['input_static']}")
    print(f"Outputting to: {dirs['output_webm']} and {dirs['output_static']}")
    print(f"Archiving to: {dirs['archive_webm']} and {dirs['archive_static']}")

    input_dirs = [dirs["input_moving"], dirs["input_static"]]
    output_webm_dir = dirs["output_webm"] 
    archive_webm_dir = dirs["archive_webm"] 
    archive_gif_dir = dirs["archive_gif"]

    for input_dir in input_dirs:
        print(f"\nScanning {input_dir} for GIFs/Videos...")
        for media_file in input_dir.iterdir():
            if media_file.is_file() and is_gif_or_video(media_file):
                try:
                    converted_path = convert_to_telegram_sticker(media_file, output_webm_dir) 
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