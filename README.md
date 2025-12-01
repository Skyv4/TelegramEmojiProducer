# Telegram Animated Sticker Converter

This project provides a command-line utility to convert GIF and video files into Telegram-compliant animated WebM stickers. It automatically handles trimming duration, attempting background transparency, and optimizing file size to meet Telegram's specifications.

## Features

*   **Input Flexibility:** Converts `.gif` files and common video formats.
*   **Duration Trimming:** Automatically trims media to a maximum of 2.84 seconds.
*   **Background Transparency:** Attempts to make solid white or black backgrounds transparent.
*   **Size Optimization:** Iteratively adjusts video quality and dimensions to keep the output file size under 64KB.
*   **Telegram Standard Compliance:** Ensures output WebM files meet Telegram's animated sticker requirements (WebM format, VP9 codec, alpha channel, max 512x512px dimensions, max 2.84s duration, max 64KB size).
*   **Organized Workflow:** Uses dedicated input, output, and archive directories for efficient management.

## Telegram Animated Sticker Specifications

For an animated sticker to be accepted by Telegram, it typically needs to adhere to the following:

*   **Format:** WebM (`.webm`)
*   **Video Codec:** VP9
*   **Resolution:** One side must be 512 pixels, and the other side must be 512 pixels or less. (e.g., 512x512, 512x300, 200x512). The script scales to `512px` on the longest side while maintaining aspect ratio.
*   **Duration:** Up to 3 seconds. This script targets **2.84 seconds**.
*   **File Size:** Up to 64KB.
*   **FPS:** Should generally be 30 FPS. This script resamples to 20 FPS for GIFs and maintains original FPS for videos.
*   **Transparency:** Must have a transparent background (alpha channel).

## Prerequisites

Before using this script, ensure you have the following installed:

1.  **Python 3.11+**: The project is configured for Python 3.11.
2.  **Rye (or UV)**: Used for Python project management and dependency installation.
    *   [Install Rye](https://rye-up.com/guide/installation/)
3.  **FFmpeg & FFprobe**: Essential tools for video/GIF processing.
    *   **Linux (Debian/Ubuntu-based):** `sudo apt update && sudo apt install ffmpeg`
    *   **Linux (Fedora-based):** `sudo dnf -y install https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm && sudo dnf update && sudo dnf install -y ffmpeg`
    *   **Linux (Arch Linux-based):** `sudo pacman -Sy && sudo pacman -S ffmpeg`
    *   **Via Snap (if available):** `sudo snap install ffmpeg`

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd TelegramEmojis
    ```
    (Replace `<repository_url>` with the actual URL if this were a GitHub repo).

2.  **Initialize and synchronize the Python environment using Rye:**
    ```bash
    rye sync
    ```
    This will set up a virtual environment and install the required Python packages (`Pillow`, `python-magic`).

## Usage

1.  **Prepare Input Files:**
    Place your `.gif` or video files (`.mp4`, `.mov`, etc.) into the `input/moving` directory.
    If you have static image files that you want to process, place them in `input/static` (though current script only supports animated/video inputs).

2.  **Run the Converter:**
    Execute the script from the project root directory:
    ```bash
    rye run python src/telegramemojis/main.py
    ```

    You can also specify a custom base path for the `input`, `output`, and `archive` directories:
    ```bash
    rye run python src/telegramemojis/main.py --path /path/to/your/custom/base/directory
    ```

## Directory Structure

The script uses the following directory structure (created automatically if they don't exist):

```
.
├── input/
│   ├── moving/     # Place your animated GIFs/Videos here for conversion
│   └── static/     # (Future use for static images)
├── output/
│   ├── webm/       # Converted WebM stickers will be saved here
│   └── static/     # (Future use for static images)
└── archive/
    ├── webm/       # Original video files moved here after processing
    ├── gif/        # Original GIF files moved here after processing
    └── static/     # (Future use for static images)
```

## Example Workflow

Let's say you have a GIF named `my_awesome_gif.gif`.

1.  Place `my_awesome_gif.gif` into `input/moving/`.
2.  Run `rye run python src/telegramemojis/main.py`.
3.  The script will process `my_awesome_gif.gif`.
4.  A new file, `my_awesome_gif.webm`, will appear in `output/webm/`. Its size will be <= 64KB and duration <= 2.84s.
5.  The original `my_awesome_gif.gif` will be moved to `archive/gif/`.
