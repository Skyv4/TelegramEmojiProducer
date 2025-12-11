import argparse
import os
import shutil
import subprocess
from pathlib import Path
import tempfile 
import magic 
import struct
try:
    from .custom_encoder import encode_with_alpha_muxing
except ImportError:
    # Fallback for running script directly
    from custom_encoder import encode_with_alpha_muxing

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
    }

    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    
    return dirs

import av
from PIL import Image

def resize_to_square(img: Image.Image, target_size: int = 100) -> Image.Image:
    """Resizes and pads an image to fit exactly within a square canvas."""
    width, height = img.size
    
    # Calculate scale to fit largest dimension
    scale = target_size / max(width, height)
    
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    # Resize if necessary
    if scale != 1.0:
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
    # Create transparent square canvas
    new_img = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    
    # Center
    x_offset = (target_size - new_width) // 2
    y_offset = (target_size - new_height) // 2
    
    new_img.paste(img, (x_offset, y_offset))
    return new_img


def get_video_info(file_path: Path):
    """Gets duration, dimensions, and framerate using PyAV."""
    try:
        with av.open(str(file_path)) as container:
            stream = container.streams.video[0]
            # Duration in seconds
            duration = float(stream.duration * stream.time_base) if stream.duration else 0.0
            
            # Framerate
            # stream.average_rate is usually reliable
            fps = float(stream.average_rate)
            
            width = stream.width
            height = stream.height
            
            return duration, width, height, fps
    except Exception as e:
        print(f"Error inspecting {file_path}: {e}")
        return 0.0, 512, 512, 30.0

def extract_rgba_frames_from_video(input_path: Path, output_frames_dir: Path, max_duration_sec: float = 2.84) -> float:
    """
    Extracts RGBA PNG frames using PIL (for GIFs) or PyAV (for other video formats),
    trims to max_duration_sec, and rescales.
    Returns the framerate.
    """
    
    def get_webp_durations(file_path):
        """Manually parse WebP ANMF chunks to get durations in ms."""
        try:
            with open(file_path, "rb") as f:
                data = f.read()

            if data[0:4] != b'RIFF': return []
            pos = 12
            frame_durations = []
            
            while pos < len(data):
                chunk_id = data[pos:pos+4].decode('ascii', errors='ignore')
                try:
                    chunk_size = struct.unpack('<I', data[pos+4:pos+8])[0]
                except: break
                pos += 8
                
                if chunk_id == 'ANMF':
                    # ANMF Duration is at content offset 12 (3 bytes, LE)
                    # 3x4 bytes for X,Y,W,H = 12 bytes
                    if pos + 15 <= len(data):
                        dur_bytes = data[pos+12 : pos+15]
                        duration = dur_bytes[0] | (dur_bytes[1] << 8) | (dur_bytes[2] << 16)
                        frame_durations.append(duration)
                    
                pos += chunk_size
                if chunk_size % 2 != 0: pos += 1
            return frame_durations
        except:
             return []

    print(f"Extracting frames from {input_path.name}...")
    
    mime_type = magic.from_file(str(input_path), mime=True)
    is_image_animation = mime_type in ['image/gif', 'image/webp']

    if is_image_animation:
        # Use PIL for robust GIF/WebP transparency handling
        try:
            with Image.open(input_path) as img:
                # Handle resizing calculations based on first frame
                width, height = img.size
                
                # Assume a standard-ish framerate if duration info is missing
                # GIFs have variable frame delays
                fps = 30.0 
                if 'duration' in img.info:
                    # PIL gives duration per frame in ms
                    # Average it?
                    pass
                
                # NOTE: For GIFs, we usually iterate all frames. Calculating simplified FPS from total duration is tricky.
                # Let's try to get an average FPS or just default to 30 and rely on the number of frames we extract.
                pass
                
                
                frame_count = 0
                
                # Resampling Logic (Variable Duration -> Constant 30 FPS)
                target_fps = 30.0
                target_frame_duration_ms = 1000.0 / target_fps
                max_frames = int(max_duration_sec * target_fps)
                
                durations = []
                if mime_type == 'image/webp':
                     durations = get_webp_durations(str(input_path))
                     
                accumulated_time_ms = 0.0
                next_target_time_ms = 0.0
                
                print(f"Resampling to {target_fps} FPS. Manual Durations found: {len(durations)}")
                
                for i in range(img.n_frames):
                    if frame_count >= max_frames:
                        break
                        
                    img.seek(i)
                    
                    # Determine duration of THIS source frame
                    # Priority: 1. Manual WebP Parser 2. Pillow Info 3. Default (100ms)
                    frame_dur_ms = 100.0 # Default fallback
                    if i < len(durations):
                        frame_dur_ms = float(durations[i])
                    elif 'duration' in img.info and img.info['duration'] > 0:
                         frame_dur_ms = float(img.info['duration'])
                         
                    frame_end_time_ms = accumulated_time_ms + frame_dur_ms
                    
                    # Lazy load frame
                    frame = None 
                    
                    while next_target_time_ms < frame_end_time_ms:
                         if frame_count >= max_frames: break
                         
                         if frame is None:
                             # Convert and Force 100x100 Square
                             raw_frame = img.convert("RGBA")
                             frame = resize_to_square(raw_frame, 100)
                         
                         out_name = output_frames_dir / f"frame{frame_count:04d}.png"
                         frame.save(out_name)
                         frame_count += 1
                         next_target_time_ms += target_frame_duration_ms
                    
                    accumulated_time_ms = frame_end_time_ms
                    
                print(f"Extracted {frame_count} frames (resampled to {target_fps} FPS) from animated image using PIL to {output_frames_dir}")
                return target_fps

        except Exception as e:
             print(f"Error extracting animated image with PIL: {e}. Falling back to PyAV...")
             # Fallthrough to PyAV if PIL fails

    # PyAV Path (Videos or fallback)
    duration, width, height, fps = get_video_info(input_path)
    
    # Fallback FPS if detection failed or is weird
    if fps <= 0 or fps > 120: fps = 30.0

    frame_count = 0
    max_frames = int(max_duration_sec * fps)
    
    try:
        with av.open(str(input_path)) as container:
            stream = container.streams.video[0]
            stream.thread_type = "AUTO" 
            
            for frame in container.decode(stream):
                if frame_count >= max_frames:
                    break
                    
                # Convert to PIL Image
                # layout="rgba" ensures we get alpha if present (e.g. gif)
                img = frame.to_image().convert("RGBA")
                
                # Resize to Square
                img = resize_to_square(img, 100)
                
                out_name = output_frames_dir / f"frame{frame_count:04d}.png"
                img.save(out_name)
                frame_count += 1
                
        print(f"Extracted {frame_count} frames to {output_frames_dir}")
        return fps
        
    except Exception as e:
        print(f"Error extracting frames from {input_path.name}: {e}")
        raise




def get_optimization_candidates(base_fps: float):
    """
    Generates a sorted list of encoding configurations (Scale, CRF, FPS Divisor).
    Sorted by estimated quality (descending).
    """
    # STRICT 100x100 Constraint usually applies for Emojis.
    # Therefore we DISABLE scaling down resolution (Scale < 1.0) because it changes the dimensions from 100x100.
    scales = [1.0] 
    
    # We expand the CRF range and FPS divisors to compensate for lack of scaling.
    crfs = [30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50]
    
    # FPS Divisors: 1.0 (Original), 1.5, 2.0, 3.0, 4.0
    fps_divisors = [1.0]
    if base_fps >= 20: fps_divisors.append(1.5)
    if base_fps >= 30: fps_divisors.append(2.0)
    if base_fps >= 40: fps_divisors.append(2.5)
    if base_fps >= 50: fps_divisors.append(3.0) 
    if base_fps >= 60: fps_divisors.append(4.0)

    candidates = []
    
    for scale in scales:
        for div in fps_divisors:
            for crf in crfs:
                # Heuristic Quality Score
                score = (scale ** 1.8) * (1.0 / div) * ((60 - crf) ** 1.2)
                candidates.append({
                    "scale": scale,
                    "crf": crf,
                    "fps_div": div,
                    "score": score
                })
    
    # Sort by score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates

def convert_to_telegram_sticker(input_path: Path, output_dir: Path) -> Path:
    """
    Converts a GIF/Video to Telegram sticker standards (WebM).
    - **GIFs are first converted to a series of transparent RGBA PNGs.**
    - Uses a greedy search optimization strategy to fit 64KB.
    """
    print(f"\nProcessing {input_path.name}...")

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir_for_png_frames = Path(temp_dir_str)

        try:
            # Extract RGBA frames from input (Max Quality, Max 512px, Full FPS)
            base_fps = extract_rgba_frames_from_video(input_path, temp_dir_for_png_frames, max_duration_sec=2.84)
            
            # Count actual frames extracted
            all_frames = sorted(list(temp_dir_for_png_frames.glob("*.png")))
            total_frames = len(all_frames)
            if total_frames == 0:
                print("No frames extracted.")
                return None
                
            with Image.open(all_frames[0]) as first_img:
                base_width, base_height = first_img.size

        except Exception as e:
            print(f"Error during frame extraction for {input_path.name}: {e}")
            return None

        final_output_path = output_dir / f"{input_path.stem}.webm"
        target_size_kb = 64
        target_size_bytes = target_size_kb * 1024
        
        candidates = get_optimization_candidates(base_fps)
        
        best_effort_path = None
        best_effort_size = float('inf')
        
        # Temp output file
        temp_output_path = output_dir / f"{input_path.stem}_temp_opt.webm"
        
        print(f"Starting optimization search for {input_path.name} (Target: {target_size_kb}KB)...")
        print(f"Base: {base_width}x{base_height} @ {base_fps:.2f}fps. {len(candidates)} configurations generated.")

        i = 0
        while i < len(candidates):
            config = candidates[i]
            
            # Prepare Parameters
            scale = config["scale"]
            crf = config["crf"]
            fps_div = config["fps_div"]
            
            target_width = int(base_width * scale)
            target_height = int(base_height * scale)
            # Ensure even dims
            target_width = max(2, target_width if target_width % 2 == 0 else target_width - 1)
            target_height = max(2, target_height if target_height % 2 == 0 else target_height - 1)
            
            target_fps = base_fps / fps_div
            
            # Frame Indices (Subsampling)
            # np.linspace-like selection
            if fps_div == 1.0:
                frame_indices = None # All frames
            else:
                # Select frames to approximate new FPS
                # We simply skip frames.
                # If div is 2.0, take 0, 2, 4...
                # Ideally we distribute them evenly.
                count_needed = int(total_frames / fps_div)
                if count_needed < 1: count_needed = 1
                frame_indices = [int(j * fps_div) for j in range(count_needed)]
                # Clamp
                frame_indices = [idx for idx in frame_indices if idx < total_frames]

            # description_str = f"Scale={scale:.2f} ({target_width}x{target_height}), CRF={crf}, FPS={target_fps:.1f} (Div {fps_div})"
            # print(f"Checking [{i}/{len(candidates)}]: {description_str} ...", end="", flush=True)
            
            try:
                processed_path = encode_with_alpha_muxing(
                    frames_dir=temp_dir_for_png_frames,
                    output_path=temp_output_path,
                    fps=target_fps,
                    crf=crf,
                    target_size=(target_width, target_height),
                    frame_indices=frame_indices
                )
                
                size = os.path.getsize(processed_path)
                # print(f" Size: {size/1024:.2f}KB")
                
                if size <= target_size_bytes:
                    print(f"Success! Optimized {input_path.name} to {size/1024:.2f}KB with Scale={scale:.2f}, CRF={crf}, FPS={target_fps:.1f}")
                    shutil.move(processed_path, final_output_path)
                    return final_output_path
                
                if size < best_effort_size:
                    best_effort_size = size
                    # Keep a copy? No, we reuse the path. 
                    # We should maintain a separate "best effort" file if we want to fallback.
                    best_effort_file = output_dir / f"{input_path.stem}_best_effort.webm"
                    shutil.copy(processed_path, best_effort_file)
                    best_effort_path = best_effort_file

                # Greedy Step:
                # If we are significantly over (e.g. 150KB vs 64KB), the current score resulted in ~2.3x overage.
                # We need to drop quality significantly.
                # Assume Size is somewhat proportional to Score (it's not linear, but Score correlates).
                # NewScoreTarget = CurrentScore / (size / target_size_bytes)
                
                ratio = size / target_size_bytes
                if ratio > 1.1:
                    current_score = config["score"]
                    target_score_est = current_score / (ratio ** 0.8) # Damping factor
                    
                    # Find next candidate with score <= target_score_est
                    next_i = i + 1
                    while next_i < len(candidates) and candidates[next_i]["score"] > target_score_est:
                        next_i += 1
                    
                    if next_i > i + 1:
                        # print(f"  -> Skipping {next_i - i - 1} configs (Ratio {ratio:.2f}). Jumping to item {next_i}.")
                        i = next_i
                    else:
                        i += 1
                else:
                    i += 1

            except Exception as e:
                print(f"Error optimizing {input_path.name}: {e}")
                i += 1
        
        # End of loop
        if best_effort_path and best_effort_path.exists():
            print(f"Could not meet target size for {input_path.name}. Best effort is {best_effort_size / 1024:.2f}KB.")
            shutil.move(best_effort_path, final_output_path)
            return final_output_path
        
        print(f"Failed to optimize {input_path.name}. Returning None.")
        return None


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

    print(f"Monitoring input directories: {dirs['input_moving']} and {dirs['input_static']}")
    print(f"Outputting to: {dirs['output_webm']} and {dirs['output_static']}")
    print(f"Archiving to: {dirs['archive_webm']} and {dirs['archive_static']}")

    input_dirs = [dirs["input_moving"], dirs["input_static"]]
    output_webm_dir = dirs["output_webm"] 
    archive_webm_dir = dirs["archive_webm"]

    for input_dir in input_dirs:
        print(f"\nScanning {input_dir} for GIFs/Videos...")
        for media_file in input_dir.iterdir():
            if media_file.is_file():
                mime_type = magic.from_file(media_file, mime=True)
                if mime_type.startswith('video/') or mime_type in ['image/gif', 'image/webp']:
                    output_file = convert_to_telegram_sticker(media_file, output_webm_dir)
                    if output_file:
                        shutil.move(media_file, archive_webm_dir / media_file.name)
                        print(f"Archived {media_file.name} to {archive_webm_dir}")
                    else:
                        print(f"Failed to convert {media_file.name}. Keeping in input directory.")
                else:
                    print(f"Skipping unsupported file: {media_file.name} (MIME type: {mime_type})")

if __name__ == "__main__":
    main()