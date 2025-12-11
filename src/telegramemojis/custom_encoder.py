import av
from PIL import Image
import os
import shutil
from pathlib import Path
try:
    from .webm_alpha_muxer import mux_files
except ImportError:
    from webm_alpha_muxer import mux_files

from fractions import Fraction


def encode_stream_pyav(frames_dir: Path, output_path: Path, fps: float, crf: int, is_alpha_stream: bool, target_size: tuple = None, frame_indices: list = None):
    """
    Encodes a specific stream (Color or Alpha) using PyAV.
    If is_alpha_stream is True, extracts the alpha channel and encodes it as grayscale YUV420P.
    If False, encodes the RGB image as standard YUV420P.
    Supports on-the-fly resizing (target_size) and frame dropping (frame_indices).
    """
    # Sort frames to ensure correct order
    all_frame_files = sorted(list(frames_dir.glob('*.png')))
    if not all_frame_files:
        return

    # Filter frames if indices provided
    if frame_indices is not None:
        frame_files = [all_frame_files[i] for i in frame_indices if i < len(all_frame_files)]
    else:
        frame_files = all_frame_files

    if not frame_files:
        return

    # PyAV expects Fraction for rate
    fps_fraction = Fraction(fps).limit_denominator()

    # Use 'webm' container
    with av.open(str(output_path), 'w', format='webm') as container:
        stream = container.add_stream('libvpx-vp9', rate=fps_fraction)
        
        # Initial dimensions (from first frame, potentially resized)
        if target_size:
            width, height = target_size
        else:
            with Image.open(frame_files[0]) as first_img:
                width, height = first_img.size
        
        stream.width = width
        stream.height = height
        stream.pix_fmt = 'yuv420p'
        
        # Options consistent with previous ffmpeg command
        # -b:v 0 is crucial for CRF mode in validation
        stream.options = {
            'crf': str(crf),
            'b:v': '0', 
            # 'deadline': 'realtime' # Optional for speed
        }

        for i, fpath in enumerate(frame_files):
            with Image.open(fpath) as img:
                img = img.convert("RGBA")
                
                # Resize if needed
                if target_size and img.size != target_size:
                    img = img.resize(target_size, Image.Resampling.LANCZOS)
                
                if i == 0:
                    stream.width = img.width
                    stream.height = img.height

                if is_alpha_stream:
                    # Extract Alpha channel
                    alpha = img.split()[-1] # Put alpha into a new L-mode image
                    # Creating a grayscale image (L) and converting to video frame
                    frame = av.VideoFrame.from_image(alpha)
                else:
                    # Color stream: standard conversion
                    frame = av.VideoFrame.from_image(img)

                # Force pixel format to yuv420p for compatibility
                frame = frame.reformat(format='yuv420p')
                
                for packet in stream.encode(frame):
                    container.mux(packet)

        # Flush
        for packet in stream.encode():
            container.mux(packet)


def encode_with_alpha_muxing(frames_dir: Path, output_path: Path, fps: float = 30.0, crf: int = 30, target_size: tuple = None, frame_indices: list = None):
    """
    Encodes directory of PNG frames (must be RGBA) into a Transparent WebM
    by encoding separate Color and Alpha streams via PyAV and muxing them.
    """
    
    # Setup temp paths
    base_name = output_path.stem
    temp_dir = output_path.parent / "temp_enc"
    temp_dir.mkdir(exist_ok=True)
    
    color_webm = temp_dir / f"{base_name}_color.webm"
    alpha_webm = temp_dir / f"{base_name}_alpha.webm"
    
    # print(f"Custom Encoder (PyAV): Processing {len(frame_indices) if frame_indices else 'all'} frames...")
    
    # 1. Encode Color Stream
    # print("Encoding Color Stream (PyAV)...")
    encode_stream_pyav(frames_dir, color_webm, fps, crf, is_alpha_stream=False, target_size=target_size, frame_indices=frame_indices)
    
    # 2. Encode Alpha Stream
    # print("Encoding Alpha Stream (PyAV)...")
    encode_stream_pyav(frames_dir, alpha_webm, fps, crf, is_alpha_stream=True, target_size=target_size, frame_indices=frame_indices)
    
    # 3. Mux
    # print("Muxing Streams...")
    mux_files(str(color_webm), str(alpha_webm), str(output_path))
    
    # Cleanup
    if color_webm.exists(): color_webm.unlink()
    if alpha_webm.exists(): alpha_webm.unlink()
    if temp_dir.exists(): shutil.rmtree(temp_dir)
    
    # print(f"Success: {output_path} generated.")
    return output_path

