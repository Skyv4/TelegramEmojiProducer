from PIL import Image
import os
import subprocess
import tempfile
from pathlib import Path

def extract_gif_frames_to_png(gif_path: Path, output_dir: Path) -> tuple[list[Path], float]:
    """
    Extracts all frames from a GIF, preserving transparency, and saves them as PNG files.
    Returns a list of PNG file paths and the frame duration in seconds.
    """
    frames = []
    frame_paths = []

    with Image.open(gif_path) as im:
        frame_duration_ms = im.info.get('duration', 100)
        frame_duration_sec = frame_duration_ms / 1000.0

        try:
            frame_idx = 0
            while True:
                frame = im.convert('RGBA')
                frame_path = output_dir / f"frame_{frame_idx:04d}.png"
                frame.save(frame_path, 'PNG')
                frame_paths.append(frame_path)

                frame_idx += 1
                im.seek(im.tell() + 1)
        except EOFError:
            pass

    print(f"Extracted {len(frame_paths)} frames from {gif_path.name} (frame duration: {frame_duration_sec}s)")
    return frame_paths, frame_duration_sec

def encode_png_frames_to_webm(frame_dir: Path, output_path: Path, fps: float, max_duration_sec: float = 2.84, target_side_length: int = 100) -> Path:
    """
    Encodes PNG frames to WebM with alpha channel support, scaled to target_side_length.
    """
    max_frames = int(30.0 * max_duration_sec)

    # Define the complex filtergraph for explicit alpha channel handling
    # 1. Scale the input to 100x100
    # 2. Split the stream into two: one for RGB, one for Alpha
    # 3. Use 'alphaextract' to get the alpha channel as a grayscale image
    # 4. Use 'alphamerge' to merge the scaled RGB and the extracted alpha
    # 5. Finally, ensure the output format is yuva420p
    complex_filter = f"[0:v]scale={target_side_length}:{target_side_length}[scaled];"\
                     f"[scaled]split[rgb][alpha];"\
                     f"[alpha]alphaextract[alphachan];"\
                     f"[rgb][alphachan]alphamerge,format=yuva420p"

    command = [
        'ffmpeg',
        '-framerate', '30.0',
        '-i', str(frame_dir / 'frame_%04d.png'),
        '-frames:v', str(max_frames),
        '-filter_complex', complex_filter,
        '-c:v', 'libvpx-vp9',
        '-profile:v', '0',
        '-level', '3.1',
        '-pix_fmt', 'yuva420p',
        '-metadata:s:v:0', 'alpha_mode=1',
        '-crf', '38',
        '-auto-alt-ref', '1',
        '-b:v', '0',
        '-an',
        '-y',
        str(output_path)
    ]

    print(f"Encoding {max_frames} frames to WebM with transparency (target_side_length={target_side_length}, fps={fps})...")

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

if __name__ == "__main__":
    gif_input_path = Path("/home/a112/Documents/code/immutable/TelegramEmojis/backend/archive/gif/4744-pepe-cross.gif")
    output_dir = Path("/home/a112/Documents/code/immutable/TelegramEmojis/backend/output/tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_webm_path = output_dir / f"{gif_input_path.stem}_converted.webm"

    if not gif_input_path.exists():
        print(f"Error: GIF file not found at {gif_input_path}")
    else:
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            print(f"Using temporary directory for frames: {temp_dir}")

            frame_paths, frame_duration_sec = extract_gif_frames_to_png(gif_input_path, temp_dir)

            if frame_paths:
                actual_gif_fps = 1.0 / frame_duration_sec if frame_duration_sec > 0 else 30.0 # Default to 30 if duration is 0 or unspec
                encode_png_frames_to_webm(temp_dir, output_webm_path, actual_gif_fps)
            else:
                print(f"No frames extracted from {gif_input_path}. WebM conversion skipped.")
