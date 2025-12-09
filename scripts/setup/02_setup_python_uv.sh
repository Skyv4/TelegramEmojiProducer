#!/bin/bash
# scripts/setup/02_setup_python_uv.sh

# -----------------------------------------------------------------------------
# Python and UV Setup Script
#
# This script ensures Python 3.12+ is available and installs the `uv` package
# manager globally using pipx.
# -----------------------------------------------------------------------------

set -e

# Determine script's own directory to reliably source config and common libs
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/config.sh
source "${_SCRIPT_DIR}/../lib/config.sh"
# shellcheck source=../lib/common.sh
source "${_SCRIPT_DIR}/../lib/common.sh"

log_info "Starting Python and uv setup..."

# --- 1. Ensure Python 3.12+ is available ---
log_info "Checking for Python 3.12+..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")")
    if printf '%s\n' "3.12" "${PYTHON_VERSION}" | sort -V -C; then
        log_info "Python ${PYTHON_VERSION} (3.12 or newer) is already installed."
    else
        log_fatal "Python 3.12 or newer is required. Current version: ${PYTHON_VERSION}. Please install it manually or update this script."
    fi
else
    log_fatal "Python 3 is not installed. Please install Python 3.12+ manually or update this script."
fi

# --- 2. Install pipx (if not already installed) ---
log_info "Checking for pipx..."
if ! command -v pipx &> /dev/null; then
    log_info "pipx not found. Installing pipx..."
    if sudo apt-get update && sudo apt-get install -y pipx; then
        log_info "pipx installed."
        # Ensure pipx path is in PATH for the current session
        export PATH="$PATH:/usr/local/bin"
    else
        log_fatal "Failed to install pipx. Aborting."
    fi
else
    log_info "pipx is already installed."
fi

# --- 3. Install uv using pipx ---
log_info "Installing/updating uv using pipx..."
if pipx install uv --include-deps; then
    log_info "uv installed/updated successfully."

    # Ensure uv is symlinked to /usr/local/bin for global access
    _UV_LOCAL_BIN="${HOME}/.local/bin/uv"

    if [ -f "${_UV_LOCAL_BIN}" ]; then
        log_info "Creating symlink for uv at /usr/local/bin/uv..."
        if sudo ln -sf "${_UV_LOCAL_BIN}" "/usr/local/bin/uv"; then
            log_info "Symlink created successfully: /usr/local/bin/uv -> ${_UV_LOCAL_BIN}"
        else
            log_warning "Failed to create symlink for uv. It might not be globally accessible."
        fi
    else
        log_warning "uv executable not found at ${_UV_LOCAL_BIN} after pipx installation. Symlink not created."
    fi
else
    log_fatal "Failed to install/update uv using pipx. Aborting."
fi

log_info "Python and uv setup complete."
