# Telegram Sticker Converter

This project provides a robust, **pure Python** command-line utility to convert media files into Telegram-compliant stickers. It supports both **Animated Stickers** (WebM) and **Static Custom Emojis** (WebP), automatically handling format conversion, resizing, transparency, and file size optimization.

## Features

*   **Pure Python Implementation:** Zero dependencies on system binaries like `ffmpeg`. Uses `PyAV` and `Pillow` for all media processing, making it highly portable.
*   **Animated Sticker Support:**
    *   Converts **GIFs**, **WebPs**, and **Videos** (MP4, MOV, etc.) to **WebM (VP9)**.
    *   **Transparency Preserved:** Correctly handles alpha channels in GIFs and WebPs using a custom alpha-muxing pipeline.
    *   **Smart Optimization:** Uses a greedy search algorithm to aggressively fit files under the strict **64KB** limit without sacrificing quality unnecessarily.
    *   **Auto-Trimming:** Trims to Telegram's max duration (approx 2.84s).
*   **Static Sticker Support:**
    *   Converts images (WebP, PNG, etc.) to **WebP**.
    *   **Strict Resizing:** Automatically pads and resizes images to **100x100** pixels (Telegram Custom Emoji standard).
*   **Organized Workflow:** dedicated `input`, `output`, and `archive` directories for batch processing.

## Prerequisites

1.  **Python 3.11+**
2.  **uv**: Modern Python package manager.
    *   [Install uv](https://github.com/astral-sh/uv)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd TelegramEmojis
    ```

2.  **Sync Dependencies:**
    ```bash
    uv sync
    ```

## Usage

1.  **Prepare Input Files:**
    *   **For Animations (Stickers):** Place `.gif`, `.webp`, `.mp4`, or `.mov` files into `input/moving/`.
    *   **For Static Emojis:** Place `.png` or `.webp` images into `input/static/`.

2.  **Run the Converter:**
    ```bash
    uv run python src/telegramemojis/main.py
    ```

    The script will:
    *   Scan `input/moving` and `input/static`.
    *   Process all valid files.
    *   Save converted stickers to `output/webm` (animated) or `output/static` (static).
    *   Move original files to `archive/`.

    *Note: You can also specify a custom base directory:*
    ```bash
    uv run python src/telegramemojis/main.py --path /path/to/custom/dir
    ```

## Directory Structure

The script uses the following structure (automatically created):

```
.
├── input/
│   ├── moving/     # IN: GIFs/Videos for Animated Stickers
│   └── static/     # IN: Images for Static Custom Emojis
├── output/
│   ├── webm/       # OUT: Converted Animated Stickers (.webm)
│   └── static/     # OUT: Converted Static Emojis (.webp)
└── archive/
    ├── webm/       # Archived original animated files
    └── static/     # Archived original static files
```

## Technical Details

### Animated Stickers (WebM)
*   **Format:** VP9 Video in WebM container.
*   **Dimensions:** Scaled to fit 512x512 box (one side exactly 512).
*   **Duration:** < 3 seconds.
*   **Size:** < 64 KB.
*   **Transparency:** Uses a custom implementation of VP9 Alpha channel muxing (BlockAdditions) to ensure transparency works even with limited encoders.

### Static Emojis (WebP)
*   **Format:** Lossless WebP.
*   **Dimensions:** 100x100 pixels (padded).

