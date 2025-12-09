#!/bin/bash
# scripts/setup/04_setup_pnpm.sh

# -----------------------------------------------------------------------------
# PNPM Setup Script
#
# This script ensures pnpm is available system-wide via corepack.
# -----------------------------------------------------------------------------

set -e

# Determine script's own directory to reliably source config and common libs
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/config.sh
source "${_SCRIPT_DIR}/../lib/config.sh"
# shellcheck source=../lib/common.sh
source "${_SCRIPT_DIR}/../lib/common.sh"

log_info "Starting pnpm setup..."

# --- 1. Setup pnpm system-wide via corepack ---
# This function is defined in common.sh
setup_system_pnpm_via_corepack

log_info "pnpm setup complete."
