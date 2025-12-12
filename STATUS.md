# Project Status: Pure Python Implementation & Transparency Fixed

## Overview
The Telegram Animated Sticker Converter has been successfully refactored to a **pure Python implementation**, removing all dependencies on external system binaries (specifically `ffmpeg`). It produces high-quality, transparent WebM stickers compatible with Telegram's strict requirements.

## Key Achievements

### 1. Removal of External Dependencies (FFmpeg Bypass)
*   **Old Architecture:** Relied on `subprocess` calls to a system-installed `ffmpeg` binary for all media processing.
*   **New Architecture:** Fully self-contained using **PyAV (`av`)** and **Pillow (`PIL`)**.
    *   **PyAV**: Bundles `libav*` libraries directly, allowing the script to encode VP9 video streams anywhere Python is installed.
    *   **Portability:** The project can now run in any environment with the dependencies installed via `uv` or `pip`, without requiring manual system package configuration.

### 2. Resolved GIF Transparency Issues
*   **Problem:** PyAV (and certain `ffmpeg` configurations) incorrectly decoded transparent GIFs onto an opaque white background (`bgra` format issues), resulting in stickers with white boxes.
*   **Solution:** Implemented a **Hybrid Extraction Pipeline**:
    *   **GIFs & WebPs:** Detected via `python-magic`. Frames are extracted using **Pillow (PIL)**, which robustly handles palettes and transparency disposal, guaranteeing accurate RGBA output.
    *   **Video (MP4/MOV):** Processed using **PyAV** for efficient decoding of standard video formats.

### 3. Custom Transparency Muxing (VP9 Alpha)
*   **Challenge:** The bundled `libvpx` encoder (like many system builds) often fails to encode `yuva420p` (native alpha) correctly, stripping the alpha channel.
*   **Solution:** We encode two separate VP9 streams using PyAV:
    1.  **Color Stream:** Standard `yuv420p` (opaque).
    2.  **Alpha Stream:** Grayscale `yuv420p` representing the alpha mask.
*   **Muxer:** A custom pure-Python muxer (`webm_alpha_muxer.py`) combines these streams into a single WebM container using the **BlockAdditions** standard (Alpha Mode 1). This ensures compatibility with Telegram and browsers while bypassing encoder limitations.

### 4. Advanced Greedy Search Optimization
*   **Previous Approach:** Simple iterative CRF adjustment followed by scaling.
*   **New "Greedy Search" Strategy:** Implemented a multi-dimensional optimization search to robustly fit the **64KB** limit while maximizing quality.
*   **Dimensions:** Optimization now dynamically adjusts:
    *   **Scale:** (1.0x to 0.4x)
    *   **CRF:** (30 to 50)
    *   **FPS (Framerate):** (Full, 2/3, 1/2, 1/3 speed)
*   **Adaptive Jumping:** The search algorithm uses a heuristic "Quality Score" to order candidates and employs adaptive jumping—skipping less aggressive configurations if the current file size is significantly over the limit—to find a solution quickly.

## Current status
*   **Working:** The pipeline is fully functional and verified.
*   **Input (Animated):** Supports GIFs and WebPs (with full transparency) and video files -> WebM/VP9.
*   **Input (Static):** Supports WebP/Images -> WebP (100x100).
*   **Output:** Generates compliant `.webm` (animated) and `.webp` (static) files.
*   **Usage:** Run via `uv run python src/telegramemojis/main.py`.