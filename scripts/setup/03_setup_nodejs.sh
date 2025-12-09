#!/bin/bash
# scripts/setup/02_setup_nodejs.sh

# -----------------------------------------------------------------------------
# Node.js Setup Script
#
# This script installs Node.js and npm (if not already present) using NodeSource
# PPA, which provides up-to-date versions.
# -----------------------------------------------------------------------------

set -e

# Determine script's own directory to reliably source config and common libs
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/config.sh
source "${_SCRIPT_DIR}/../lib/config.sh"
# shellcheck source=../lib/common.sh
source "${_SCRIPT_DIR}/../lib/common.sh"

log_info "Starting Node.js setup..."

# --- 1. Add NodeSource APT repository ---
log_info "Adding NodeSource APT repository for Node.js ${NODE_MAJOR_VERSION:-20}..."
ensure_command_exists "curl"
ensure_command_exists "apt-get"

# Define Node.js major version (e.g., 18, 20). Default to 20 if not set.
NODE_MAJOR_VERSION=${NODE_MAJOR_VERSION:-20}

# Check if NodeSource PPA is already added to avoid errors
if [ ! -f /etc/apt/sources.list.d/nodesource.list ]; then
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR_VERSION.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list
    log_info "NodeSource repository added."
else
    log_info "NodeSource repository already exists. Skipping addition."
fi

# --- 2. Update apt cache and install Node.js ---
log_info "Updating apt cache and installing Node.js..."
if sudo apt-get update && sudo apt-get install -y nodejs; then
    log_info "Node.js and npm installed."
else
    log_fatal "Failed to install Node.js and npm."
fi

# --- 3. Verify Installation ---
log_info "Verifying Node.js and npm installation..."
ensure_command_exists "node"
ensure_command_exists "npm"

log_info "Node.js version: $(node -v)"
log_info "npm version: $(npm -v)"

log_info "Node.js setup complete."
