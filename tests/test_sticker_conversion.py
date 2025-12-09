import pytest
import shutil
import subprocess
import os
from pathlib import Path

from src.telegramemojis.main import convert_to_telegram_sticker, check_ffmpeg_installed, get_video_duration

# Define paths relative to the project root
TEST_BASE_DIR = Path(__file__).parent
ARCHIVE_GIF_PATH = TEST_BASE_DIR.parent / "archive" / "gif" / "4744-pepe-cross.gif"

@pytest.fixture(scope="module")
def setup_ffmpeg():
    if not check_ffmpeg_installed():
        pytest.skip("ffmpeg not installed or not in PATH, skipping tests.")

@pytest.fixture
def temp_dirs(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    return input_dir, output_dir

import json

def get_webm_info(file_path: Path):
    """
    Retrieves duration, dimensions, and checks for alpha channel presence in a WebM file.
    Returns (duration, width, height, has_alpha).
    """
    duration = 0.0
    width = 0
    height = 0
    has_alpha = False

    # First, get basic stream info using ffprobe
    ffprobe_command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "V:0",
        "-show_entries", "stream=duration,width,height,pix_fmt",
        "-of", "json", # Use JSON format for robust parsing
        str(file_path)
    ]
    try:
        result = subprocess.run(ffprobe_command, check=True, capture_output=True, text=True)
        info = json.loads(result.stdout)
        
        stream = info.get('streams', [])[0] if info.get('streams') else {}
        
        try:
            duration = float(stream.get('duration', '0.0'))
        except ValueError:
            pass # duration remains 0.0 if 'N/A' or invalid

        width = int(stream.get('width', 0))
        height = int(stream.get('height', 0))
        # pix_fmt is not directly used for alpha check anymore, but can be useful for debugging
        # pix_fmt = stream.get('pix_fmt', '') 
        
        # Check for alpha channel by attempting to extract it using alphaextract filter
        alpha_extract_command = [
            "ffmpeg",
            "-i", str(file_path),
            "-vf", "alphaextract",
            "-f", "null",
            "-", # Output to null device
            "-v", "quiet", # Suppress verbose output
            "-y"
        ]
        try:
            subprocess.run(alpha_extract_command, check=True, capture_output=True, timeout=10) # Added timeout
            has_alpha = True
        except subprocess.CalledProcessError:
            has_alpha = False # alphaextract will fail if there's no alpha channel
        except subprocess.TimeoutExpired:
            print(f"Alphaextract command timed out for {file_path}")
            has_alpha = False
        except Exception as e:
            print(f"Error during alphaextract check for {file_path}: {e}")
            has_alpha = False

    except Exception as e:
        print(f"Error probing WebM info for {file_path}: {e}")
        # Keep defaults if error occurs during ffprobe
        
    return duration, width, height, has_alpha


def test_gif_transparency_conversion(setup_ffmpeg, temp_dirs):
    input_dir, output_dir = temp_dirs
    
    # Copy the test GIF to the temporary input directory
    shutil.copy(ARCHIVE_GIF_PATH, input_dir)
    input_gif = input_dir / ARCHIVE_GIF_PATH.name
    
    # Run the conversion
    converted_webm_path = convert_to_telegram_sticker(input_gif, output_dir)
    
    # Assertions
    assert converted_webm_path is not None
    assert converted_webm_path.exists()
    assert converted_webm_path.suffix == ".webm"
    
    # Check file size
    file_size_kb = os.path.getsize(converted_webm_path) / 1024
    assert file_size_kb < 64, f"File size is {file_size_kb:.2f}KB, expected < 64KB"
    
    # Check duration, dimensions, and alpha
    duration, width, height, has_alpha = get_webm_info(converted_webm_path)
    assert duration < 3.0, f"Duration is {duration:.2f}s, expected < 3.0s"
    assert width <= 100 and height <= 100, f"Dimensions are {width}x{height}, expected max 100x100"
    assert has_alpha is True, "Output WebM does not have an alpha channel"

