#!/bin/bash
# scripts/setup/01_setup_system.sh

# -----------------------------------------------------------------------------
# System Setup Script
#
# This script performs initial system-level setup for the Media Telegram Processor deployment,
# including updating packages, installing essential tools, and setting up
# the system user and group for the application.
# -----------------------------------------------------------------------------

set -e

# Determine script's own directory to reliably source config and common libs
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/config.sh
source "${_SCRIPT_DIR}/../lib/config.sh"
# shellcheck source=../lib/common.sh
source "${_SCRIPT_DIR}/../lib/common.sh"

log_info "Starting Media Telegram Processor system setup..."

# --- 1. Update System Packages ---
log_info "Updating system packages for Media Telegram Processor deployment..."
ensure_command_exists "sudo"
ensure_command_exists "apt-get" "apt"
if sudo apt-get update && sudo apt-get upgrade -y; then
    log_info "System packages updated."
else
    log_fatal "Failed to update system packages."
fi

# --- 2. Install Essential Tools ---
log_info "Installing essential tools (curl, git, rsync, build-essential, tee, gnupg, ca-certificates, lsb-release) for Media Telegram Processor..."
if sudo apt-get install -y curl git rsync build-essential gnupg ca-certificates lsb-release; then
    log_info "Essential tools installed."
else
    log_fatal "Failed to install essential tools."
fi

# --- 3. Ensure System User and Group Exist ---
log_info "Ensuring system user '${SYSTEM_USER}' and group '${SYSTEM_GROUP}' exist for Media Telegram Processor..."
# SYSTEM_USER and SYSTEM_GROUP are sourced from config.sh
ensure_user_group_exists "${SYSTEM_USER}" "${SYSTEM_GROUP}" "system"
log_info "System user and group ensured for Media Telegram Processor."

log_info "Media Telegram Processor system setup complete."
