# Telegram Animated Sticker Converter: Gemini Agent Insights

This document provides a technical overview and insights into the design and implementation of the Telegram Animated Sticker Converter, as developed by the Gemini agent.

## Project Overview

The Telegram Animated Sticker Converter is a Python-based utility designed to automate the process of transforming GIF or video files into Telegram-compliant animated WebM stickers. It addresses the specific technical requirements set by Telegram for animated stickers, ensuring compatibility, optimal file size, and visual quality.

## Core Functionality & Design

The solution is structured around a pipeline that processes an input media file through several stages to meet Telegram's specifications:

1.  **Input Handling & Pre-processing:**
    *   **File Type Detection:** Utilizes the `python-magic` library to accurately identify input files as GIFs or other video formats.
    *   **Directory Management:** Employs `pathlib` to robustly manage input, output, and archive directories, ensuring their existence and organized file storage.
    *   **`ffmpeg` and `ffprobe` Integration:** The core conversion relies heavily on `ffmpeg` for media manipulation and `ffprobe` for media introspection (e.g., getting duration, dimensions, alpha channel info). These are invoked via `subprocess` calls.

2.  **Conversion to Intermediate WebM & Initial Trimming:**
    *   The `convert_to_webm_intermediate` function takes any supported input (GIF/video) and performs an initial conversion to WebM format (`libvpx-vp9` codec).
    *   **Trimming:** Automatically trims the media to a precise duration of **2.84 seconds** using `ffmpeg`'s `-t` option.
    *   **Scaling:** Rescales the video to ensure one side is 512 pixels (maintaining aspect ratio), aligning with Telegram's dimension requirements. Dimensions are adjusted to be even numbers for `ffmpeg` compatibility.
    *   **Transparency:** Configures `ffmpeg` to use `yuva420p` pixel format and sets `alpha_mode=1` to ensure the output WebM retains or gains an alpha channel for transparency.

3.  **Iterative WebM Optimization (`optimize_webm_size`):**
    *   This is the most critical and complex stage, focusing on reducing the file size to under 64KB while preserving quality.
    *   **CRF Iteration:** The function iteratively re-encodes the WebM using `libvpx-vp9` with varying Constant Rate Factor (CRF) values (from 25 to 40). Lower CRF values mean higher quality but larger files, so the script progressively increases CRF to find the smallest file size that is still acceptable or meets the target.
    *   **Dynamic Scaling:** If CRF iteration alone isn't sufficient, the script further reduces the video dimensions by scaling down (from 90% to 40% of the initial 512px target) to achieve the target file size.
    *   **Best Effort Strategy:** The function keeps track of the smallest file generated across all iterations, moving it to the final output if the 64KB target cannot be strictly met.
    *   **Intermediate File Cleanup:** Ensures that temporary intermediate files generated during optimization are removed.

4.  **Consolidated Conversion (`convert_to_telegram_sticker`):**
    *   This function orchestrates the entire workflow, calling `convert_to_webm_intermediate` and `optimize_webm_size` sequentially.
    *   It handles error propagation and manages intermediate file cleanup.

## Telegram Sticker Compliance

The solution meticulously addresses all specified Telegram animated sticker requirements:

*   **Format:** Outputs `.webm` files.
*   **Video Codec:** Uses `libvpx-vp9`.
*   **Resolution:** Ensures one side is 512 pixels or less, maintaining aspect ratio.
*   **Duration:** Trims precisely to **2.84 seconds**.
*   **File Size:** Iteratively optimizes to achieve **less than 64KB**.
*   **Transparency:** Incorporates alpha channel (`yuva420p`, `alpha_mode=1`) for transparent backgrounds. While explicit background color removal (white/black) was initially discussed, the WebM conversion itself with alpha channel support allows for native transparency.

## Technical Details & Challenges

*   **`pyproject.toml` and `src-layout`:** Initial setup was challenging due to `setuptools` package discovery issues with `rye`. Refactoring to a `src-layout` and precise `[tool.setuptools.packages.find]` configuration resolved this.
*   **`ffmpeg` Command Complexity:** Building robust `ffmpeg` commands for complex filtergraphs (scaling, palette generation/use for GIF, `libvpx-vp9` options for WebM) required careful construction and debugging, especially with handling temporary files and iterative processes.
*   **Iterative Optimization:** The core challenge was designing an efficient iterative process to hit the strict 64KB file size limit. The chosen approach of first varying CRF and then scaling down provides a good balance between quality and size reduction.
*   **Temporary File Management:** Robust handling of intermediate files is crucial to prevent disk clutter and ensure only the final optimized output remains.

## Future Enhancements

*   **User-Defined Parameters:** Allow users to configure target duration, max file size, or specific `ffmpeg` parameters via CLI arguments.
*   **Error Handling:** Implement more granular error reporting and recovery strategies.
*   **GUI Interface:** Develop a simple graphical user interface for easier interaction.
*   **Static Image Sticker Support:** Extend functionality to convert static images (e.g., PNG) to Telegram's WebP sticker format.
*   **Lossless Transparency:** Explore more advanced background removal techniques if simple color-keying is insufficient.