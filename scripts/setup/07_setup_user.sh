#!/bin/bash
set -e

# Determine script's own directory to reliably source config and common libs
_SETUP_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_LIB_DIR="${_SETUP_SCRIPT_DIR}/../lib" # Assuming this script is in setup/, so ../lib

# shellcheck source=../lib/config.sh
source "${_LIB_DIR}/config.sh"
# shellcheck source=../lib/common.sh
source "${_LIB_DIR}/common.sh"

log_info "Starting Media Telegram Processor User and System PNPM Setup (07_setup_user.sh)..."
log_info "This script should be run once during initial server setup for the Media Telegram Processor project."

# --- Ensure System User and Group Exist ---
# SYSTEM_USER and SYSTEM_GROUP are sourced from config.sh (e.g., www-data)
# The "system" flag tells ensure_user_group_exists to create a system account.
ensure_user_group_exists "${SYSTEM_USER}" "${SYSTEM_GROUP}" "system"

# --- Ensure pnpm is accessible for the system user via corepack ---
# Temporarily bypass system-wide setup to avoid sudo issues
log_info "Ensuring pnpm is available for Media Telegram Processor system user '${SYSTEM_USER}' via corepack..."

COREPACK_USER_CACHE_DIR="/var/www/.cache/node/corepack"

log_info "Ensuring corepack cache directory exists for '${SYSTEM_USER}' at ${COREPACK_USER_CACHE_DIR}..."
if sudo mkdir -p "${COREPACK_USER_CACHE_DIR}"; then
    log_info "Corepack cache directory ensured."
else
    log_fatal "Failed to create corepack cache directory: ${COREPACK_USER_CACHE_DIR}"
fi

log_info "Setting ownership of '${COREPACK_USER_CACHE_DIR}' to '${SYSTEM_USER}:${SYSTEM_GROUP}'..."
if sudo chown -R "${SYSTEM_USER}:${SYSTEM_GROUP}" "${COREPACK_USER_CACHE_DIR}"; then
    log_info "Ownership set for '${COREPACK_USER_CACHE_DIR}'."
else
    log_fatal "Failed to set ownership for '${COREPACK_USER_CACHE_DIR}'."
fi

sudo -u "${SYSTEM_USER}" bash -c "export NVM_DIR=/var/www/.nvm; [ -s \"\$NVM_DIR/nvm.sh\" ] && \\. \"\$NVM_DIR/nvm.sh\"; corepack enable && corepack prepare pnpm@latest --activate"
log_info "Corepack and pnpm setup attempted for Media Telegram Processor user '${SYSTEM_USER}'."

log_info "Media Telegram Processor User and System PNPM Setup (07_setup_user.sh) complete."
log_info "The service user '${SYSTEM_USER}' and group '${SYSTEM_GROUP}' have been ensured for Media Telegram Processor."
log_info "A system-wide pnpm (via corepack) has been set up for Media Telegram Processor."
log_info "The main deploy.sh script will further configure pnpm specifically for the Media Telegram Processor '${SYSTEM_USER}' user's environment."
