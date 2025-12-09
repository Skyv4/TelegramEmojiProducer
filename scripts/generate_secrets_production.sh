#!/bin/bash
# scripts/generate_secrets_production.sh

# -----------------------------------------------------------------------------
# Generate Production Environment File
#
# This script generates the .env.production file for production deployment
# purposes of the Media Telegram Processor project, using values defined in config.sh.
# -----------------------------------------------------------------------------

# Determine script's own directory to reliably source config
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/config.sh
source "${_SCRIPT_DIR}/lib/config.sh"
# shellcheck source=lib/common.sh
source "${_SCRIPT_DIR}/lib/common.sh"

log_info "Starting Media Telegram Processor production environment file generation..."

ENV_TARGET_FILE="${PROJECT_ROOT_DIR}/.env.production"

log_info "Looking for environment template at: ${ENV_LOCAL_FILE}"
if [ ! -f "${ENV_LOCAL_FILE}" ]; then
    log_fatal "Environment template not found at ${ENV_LOCAL_FILE}. Cannot generate .env.production file for Media Telegram Processor."
fi

log_info "Copying template to target production environment file: ${ENV_TARGET_FILE}"
if cp "${ENV_LOCAL_FILE}" "${ENV_TARGET_FILE}"; then
    log_info "Template copied successfully for Media Telegram Processor production setup."
else
    log_fatal "Failed to copy template to ${ENV_TARGET_FILE}."
fi

# --- Set NEXTAUTH_URL for Production ---
log_info "Updating NEXTAUTH_URL in ${ENV_TARGET_FILE} for Media Telegram Processor production..."
if sed -i "s|^NEXTAUTH_URL=.*|NEXTAUTH_URL=${NEXTAUTH_URL_PROD}|" "${ENV_TARGET_FILE}"; then
    log_info "NEXTAUTH_URL updated for Media Telegram Processor production."
else
    log_warning "Failed to update NEXTAUTH_URL in ${ENV_TARGET_FILE}. Please update it manually for Media Telegram Processor production."
fi

# --- Construct and Set DATABASE_URL for Production ---
_DATABASE_URL="sqlite:///./sql_app.db" # Using SQLite for production
log_info "Updating DATABASE_URL in ${ENV_TARGET_FILE} for Media Telegram Processor production..."
if sed -i "s|^DATABASE_URL=.*|DATABASE_URL=${_DATABASE_URL}|" "${ENV_TARGET_FILE}"; then
    log_info "DATABASE_URL updated for Media Telegram Processor production."
else
    log_warning "Failed to update DATABASE_URL in ${ENV_TARGET_FILE}. Please update it manually for Media Telegram Processor production."
fi

# --- Generate and Set NEXTAUTH_SECRET for Production ---
# Generate a new secret for production
_NEXTAUTH_SECRET=$(openssl rand -hex 32)
log_info "Updating NEXTAUTH_SECRET in ${ENV_TARGET_FILE} for Media Telegram Processor production..."
if sed -i "s|^NEXTAUTH_SECRET=.*|NEXTAUTH_SECRET=${_NEXTAUTH_SECRET}|" "${ENV_TARGET_FILE}"; then
    log_info "NEXTAUTH_SECRET updated with a newly generated secret for Media Telegram Processor production."
else
    log_warning "Failed to update NEXTAUTH_SECRET in ${ENV_TARGET_FILE}. Please update it manually for Media Telegram Processor production."
fi

# --- Set NEXT_PUBLIC_BACKEND_URL for internal proxying ---
# This assumes Next.js proxies requests to the backend running on the same server via localhost.
log_info "Updating NEXT_PUBLIC_BACKEND_URL in ${ENV_TARGET_FILE} for Media Telegram Processor production (Caddy-proxied API)..."
if sed -i "s|^NEXT_PUBLIC_BACKEND_URL=.*|NEXT_PUBLIC_BACKEND_URL=${NEXTAUTH_URL_PROD}/api/v1|" "${ENV_TARGET_FILE}"; then
    log_info "NEXT_PUBLIC_BACKEND_URL updated for Media Telegram Processor production."
else
    log_warning "Failed to update NEXT_PUBLIC_BACKEND_URL in ${ENV_TARGET_FILE}. Please update it manually for Media Telegram Processor production."
fi

log_info "Media Telegram Processor production environment file generated at ${ENV_TARGET_FILE}."
log_info "Please review the file and ensure all values are correct for your Media Telegram Processor production setup."
log_info "You can edit the file directly: nano ${ENV_TARGET_FILE}"
log_info "Generation complete for Media Telegram Processor production environment."
