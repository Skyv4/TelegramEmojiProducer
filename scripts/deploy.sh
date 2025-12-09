#!/bin/bash
# scripts/deploy.sh
set -e

# Determine script's own directory to reliably source config and common libs
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/config.sh
source "${_SCRIPT_DIR}/lib/config.sh"
# shellcheck source=lib/common.sh
source "${_SCRIPT_DIR}/lib/common.sh"

log_info "Starting deployment of Media Telegram Processor Frontend and Backend services..."

# --- Configuration (from config.sh) ---
# Variables like PROJECT_ROOT_DIR, APP_DIR, BACKEND_DIR,
# FRONTEND_DEPLOY_TARGET_DIR, BACKEND_DEPLOY_TARGET_DIR,
# SYSTEM_USER, SYSTEM_GROUP,
# FRONTEND_SERVICE_NAME, FRONTEND_SERVICE_FILE_PATH, FRONTEND_APP_PORT, NEXTAUTH_URL_PROD,
# BACKEND_SERVICE_NAME, BACKEND_SERVICE_FILE_PATH, BACKEND_APP_PORT
# are sourced from config.sh.

# Construct full paths for environment files
_SOURCE_PROD_ENV_FILE="${PROJECT_ROOT_DIR}/.env.production"
_FRONTEND_TARGET_ENV_FILE="${FRONTEND_DEPLOY_TARGET_DIR}/${DEPLOY_ENV_FILE_BASENAME}"
_BACKEND_TARGET_ENV_FILE="${BACKEND_DEPLOY_TARGET_DIR}/${DEPLOY_ENV_FILE_BASENAME}"

# --- 0. Create Deployment Target Directories ---
log_info "Ensuring frontend deployment target directory exists: ${FRONTEND_DEPLOY_TARGET_DIR}"
if ${SUDO} mkdir -p "${FRONTEND_DEPLOY_TARGET_DIR}"; then
    log_info "Frontend deployment target directory ensured."
else
    log_fatal "Failed to create frontend deployment target directory: ${FRONTEND_DEPLOY_TARGET_DIR}"
fi

log_info "Ensuring backend deployment target directory exists: ${BACKEND_DEPLOY_TARGET_DIR}"
if ${SUDO} mkdir -p "${BACKEND_DEPLOY_TARGET_DIR}"; then
    log_info "Backend deployment target directory ensured."
else
    log_fatal "Failed to create backend deployment target directory: ${BACKEND_DEPLOY_TARGET_DIR}"
fi

# --- 1. Check for Production Environment File ---
log_info "Checking for production environment file at: ${_SOURCE_PROD_ENV_FILE}"
if [ ! -f "${_SOURCE_PROD_ENV_FILE}" ]; then
    log_fatal "Production environment file not found at ${_SOURCE_PROD_ENV_FILE}".
    log_fatal "Please create this file with your production secrets (DATABASE_URL, NEXTAUTH_SECRET, etc.)."
    log_fatal "You can use .env.example as a template."
fi
log_info "Production environment file found. Ensure it is up-to-date with production values."

# --- 2. Synchronize Application Files to Deployment Directories ---
log_info "Synchronizing frontend application files from ${PROJECT_ROOT_DIR} to ${FRONTEND_DEPLOY_TARGET_DIR}..."
ensure_command_exists "rsync"
if ${SUDO} rsync -a --delete --checksum \
    --exclude 'node_modules' \
    --exclude '.next' \
    --exclude '.git' \
    --exclude '.env*' \
    --exclude 'backend/' \
    --exclude 'scripts/' \
    "${PROJECT_ROOT_DIR}/" "${FRONTEND_DEPLOY_TARGET_DIR}/"; then
    log_info "Frontend application files synchronized to ${FRONTEND_DEPLOY_TARGET_DIR}."
else
    log_fatal "Failed to synchronize frontend application files."
fi

log_info "Synchronizing backend application files from ${BACKEND_DIR} to ${BACKEND_DEPLOY_TARGET_DIR}..."
if ${SUDO} rsync -a --delete --checksum \
    --exclude 'venv' \
    --exclude '__pycache__' \
    --exclude '.git' \
    --exclude '.env*' \
    "${BACKEND_DIR}/" "${BACKEND_DEPLOY_TARGET_DIR}/"; then
    log_info "Backend application files synchronized to ${BACKEND_DEPLOY_TARGET_DIR}."
else
    log_fatal "Failed to synchronize backend application files."
fi

# --- 2.5 Copy and Set Permissions for Target Environment Files ---
log_info "Copying production environment file to frontend deployment target..."
if ${SUDO} cp "${_SOURCE_PROD_ENV_FILE}" "${_FRONTEND_TARGET_ENV_FILE}"; then
    log_info "Copied ${_SOURCE_PROD_ENV_FILE} to ${_FRONTEND_TARGET_ENV_FILE}".
else
    log_fatal "Failed to copy environment file to frontend deployment target."
fi

log_info "Ensuring target environment file ${_FRONTEND_TARGET_ENV_FILE} has correct permissions..."
ensure_command_exists "chown"
ensure_command_exists "chmod"
if ${SUDO} chown "${SYSTEM_USER}:${SYSTEM_GROUP}" "${_FRONTEND_TARGET_ENV_FILE}" && \
   ${SUDO} chmod 640 "${_FRONTEND_TARGET_ENV_FILE}"; then
    log_info "Permissions set for ${_FRONTEND_TARGET_ENV_FILE}".
else
    log_fatal "Failed to set permissions for ${_FRONTEND_TARGET_ENV_FILE}".
fi

# For backend, we need to create a simple .env if it doesn't exist or just copy relevant vars.
# For simplicity, let's copy the same .env.production, but ideally, backend might need different/fewer vars.
log_info "Copying production environment file to backend deployment target..."
if ${SUDO} cp "${_SOURCE_PROD_ENV_FILE}" "${_BACKEND_TARGET_ENV_FILE}"; then
    log_info "Copied ${_SOURCE_PROD_ENV_FILE} to ${_BACKEND_TARGET_ENV_FILE}".
else
    log_fatal "Failed to copy environment file to backend deployment target."
fi

log_info "Ensuring target environment file ${_BACKEND_TARGET_ENV_FILE} has correct permissions..."
if ${SUDO} chown "${SYSTEM_USER}:${SYSTEM_GROUP}" "${_BACKEND_TARGET_ENV_FILE}" && \
   ${SUDO} chmod 640 "${_BACKEND_TARGET_ENV_FILE}"; then
    log_info "Permissions set for ${_BACKEND_TARGET_ENV_FILE}".
else
    log_fatal "Failed to set permissions for ${_BACKEND_TARGET_ENV_FILE}".
fi


# --- 3. Create/Update Systemd Service Files ---
log_info "Creating/Updating frontend systemd service file at ${FRONTEND_SERVICE_FILE_PATH}..."
ensure_command_exists "tee"
if ${SUDO} tee "${FRONTEND_SERVICE_FILE_PATH}" > /dev/null <<EOF
[Unit]
Description=Media Telegram Processor Next.js application
After=network.target

[Service]
User=${SYSTEM_USER}
Group=${SYSTEM_GROUP}
WorkingDirectory=${FRONTEND_DEPLOY_TARGET_DIR}
ExecStart=/bin/bash -c 'source /var/www/.nvm/nvm.sh && pnpm start -p ${FRONTEND_APP_PORT}'

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

Environment="NODE_ENV=production"

[Install]
WantedBy=multi-user.target
EOF
then
    log_info "Frontend systemd service file created/updated at ${FRONTEND_SERVICE_FILE_PATH}."
else
    log_fatal "Failed to write frontend systemd service file to ${FRONTEND_SERVICE_FILE_PATH}."
fi

log_info "Creating/Updating backend systemd service file at ${BACKEND_SERVICE_FILE_PATH}..."
if ${SUDO} tee "${BACKEND_SERVICE_FILE_PATH}" > /dev/null <<EOF
[Unit]
Description=Media Telegram Processor FastAPI application
After=network.target

[Service]
User=${SYSTEM_USER}
Group=${SYSTEM_GROUP}
WorkingDirectory=${BACKEND_DEPLOY_TARGET_DIR}
ExecStart=/bin/bash -c 'source ${BACKEND_DEPLOY_TARGET_DIR}/.venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port ${BACKEND_APP_PORT} --log-level info'

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

Environment="PYTHONUNBUFFERED=1" # Ensure Python output is not buffered

[Install]
WantedBy=multi-user.target
EOF
then
    log_info "Backend systemd service file created/updated at ${BACKEND_SERVICE_FILE_PATH}."
else
    log_fatal "Failed to write backend systemd service file to ${BACKEND_SERVICE_FILE_PATH}."
fi


# --- 4. Reload Systemd and Enable Services ---
log_info "Reloading systemd daemon..."
ensure_command_exists "systemctl"
if ${SUDO} systemctl daemon-reload; then
    log_info "Systemd daemon reloaded."
else
    log_fatal "Failed to reload systemd daemon."
fi

log_info "Enabling ${FRONTEND_SERVICE_NAME}.service to start on boot..."
if ${SUDO} systemctl enable "${FRONTEND_SERVICE_NAME}.service"; then
    log_info "${FRONTEND_SERVICE_NAME}.service enabled."
else
    log_fatal "Failed to enable ${FRONTEND_SERVICE_NAME}.service."
fi

log_info "Enabling ${BACKEND_SERVICE_NAME}.service to start on boot..."
if ${SUDO} systemctl enable "${BACKEND_SERVICE_NAME}.service"; then
    log_info "${BACKEND_SERVICE_NAME}.service enabled."
else
    log_fatal "Failed to enable ${BACKEND_SERVICE_NAME}.service."
fi

# --- 5. Prepare service user environments ---
# Frontend: Ensure pnpm is available for SYSTEM_USER via corepack
prepare_service_user_pnpm_environment

# Backend: Ensure uv and python venv for SYSTEM_USER
log_info "Ensuring uv is available for backend service user '${SYSTEM_USER}'..."
if ! ${SUDO} -u "${SYSTEM_USER}" -H bash -c "command -v uv"; then
    log_fatal "uv not found for ${SYSTEM_USER}. Please ensure '02_setup_python_uv.sh' was executed successfully and uv is in the PATH for ${SYSTEM_USER}."
else
    log_info "uv already available for ${SYSTEM_USER}."
fi


# --- 6. Install Dependencies and Build (in respective DEPLOY_TARGET_DIRs) ---

# Set ownership before build to allow www-data to write node_modules, venv, etc.
set_target_ownership_and_permissions "${FRONTEND_DEPLOY_TARGET_DIR}" "${SYSTEM_USER}" "${SYSTEM_GROUP}"
set_target_ownership_and_permissions "${BACKEND_DEPLOY_TARGET_DIR}" "${SYSTEM_USER}" "${SYSTEM_GROUP}"

log_info "--- Frontend Build Process ---"
log_info "Navigating to frontend deployment directory: ${FRONTEND_DEPLOY_TARGET_DIR}"
if ! cd "${FRONTEND_DEPLOY_TARGET_DIR}"; then
    log_fatal "Failed to navigate to ${FRONTEND_DEPLOY_TARGET_DIR}."
fi

log_info "Installing/updating dependencies with pnpm in ${FRONTEND_DEPLOY_TARGET_DIR} as user ${SYSTEM_USER}..."
if ${SUDO} -u "${SYSTEM_USER}" -H bash -c "export NVM_DIR=/var/www/.nvm; [ -s \"$NVM_DIR/nvm.sh\" ] && \. \"$NVM_DIR/nvm.sh\"; cd ${FRONTEND_DEPLOY_TARGET_DIR} && pnpm install --frozen-lockfile"; then
    log_info "Frontend dependencies installed."
else
    log_fatal "Failed to install frontend dependencies in ${FRONTEND_DEPLOY_TARGET_DIR}."
fi

log_info "Removing Next.js cache in ${FRONTEND_DEPLOY_TARGET_DIR} (if any)..."
if ${SUDO} -u "${SYSTEM_USER}" bash -c "cd ${FRONTEND_DEPLOY_TARGET_DIR} && rm -rf .next"; then
    log_info "Next.js cache removed."
else
    log_warning "Failed to remove .next directory, or it didn't exist."
fi

log_info "Building Next.js application in ${FRONTEND_DEPLOY_TARGET_DIR} as user ${SYSTEM_USER}..."
if ${SUDO} -u "${SYSTEM_USER}" -H bash -c "export NVM_DIR=/var/www/.nvm; [ -s \"$NVM_DIR/nvm.sh\" ] && \. \"$NVM_DIR/nvm.sh\"; cd ${FRONTEND_DEPLOY_TARGET_DIR} && pnpm next build ."; then
    log_info "Next.js application built."
else
    log_fatal "Next.js application build failed."
fi

log_info "Pruning devDependencies in frontend as user ${SYSTEM_USER}..."
if ${SUDO} -u "${SYSTEM_USER}" -H bash -c "export NVM_DIR=/var/www/.nvm; [ -s \"$NVM_DIR/nvm.sh\" ] && \. \"$NVM_DIR/nvm.sh\"; cd ${FRONTEND_DEPLOY_TARGET_DIR} && pnpm prune --prod"; then
    log_info "Frontend devDependencies pruned."
else
    log_fatal "Failed to prune frontend devDependencies."
fi

log_info "--- Backend Setup Process ---"
log_info "Navigating to backend deployment directory: ${BACKEND_DEPLOY_TARGET_DIR}"
if ! cd "${BACKEND_DEPLOY_TARGET_DIR}"; then
    log_fatal "Failed to navigate to ${BACKEND_DEPLOY_TARGET_DIR}."
fi

log_info "Creating Python virtual environment and installing dependencies in ${BACKEND_DEPLOY_TARGET_DIR} as user ${SYSTEM_USER}..."
if ${SUDO} -u "${SYSTEM_USER}" -H bash -c "cd ${BACKEND_DEPLOY_TARGET_DIR} && uv venv && source .venv/bin/activate && uv pip install -r requirements.txt"; then
    log_info "Backend dependencies installed."
else
    log_fatal "Failed to install backend dependencies in ${BACKEND_DEPLOY_TARGET_DIR}."
fi


# --- 7. Set Final Ownership and Permissions for Deployment Directories ---
set_target_ownership_and_permissions "${FRONTEND_DEPLOY_TARGET_DIR}" "${SYSTEM_USER}" "${SYSTEM_GROUP}"
set_target_ownership_and_permissions "${BACKEND_DEPLOY_TARGET_DIR}" "${SYSTEM_USER}" "${SYSTEM_GROUP}"

# --- 8. Restart Services ---
log_info "Restarting ${FRONTEND_SERVICE_NAME} service..."
if ${SUDO} systemctl restart "${FRONTEND_SERVICE_NAME}.service"; then
    log_info "${FRONTEND_SERVICE_NAME}.service restarted."
else
    log_fatal "Failed to restart ${FRONTEND_SERVICE_NAME}.service."
fi

log_info "Restarting ${BACKEND_SERVICE_NAME} service..."
if ${SUDO} systemctl restart "${BACKEND_SERVICE_NAME}.service"; then
    log_info "${BACKEND_SERVICE_NAME}.service restarted."
else
    log_fatal "Failed to restart ${BACKEND_SERVICE_NAME}.service."
fi

log_info "Reloading Caddy (if used)..."
if systemctl list-units --full -all | grep -q 'caddy.service'; then
    if ${SUDO} systemctl reload caddy; then
        log_info "Caddy reloaded."
    else
        log_warning "Failed to reload Caddy. Check Caddy status/logs."
    fi
else
    log_info "Caddy service not found, skipping reload."
fi

echo ""
log_info "--------------------------------------------------------------------"
log_info " Deployment complete!"
log_info "--------------------------------------------------------------------"
echo " Frontend Service Status:   ${SUDO} systemctl status ${FRONTEND_SERVICE_NAME}.service"
echo " Frontend Service Logs:   journalctl -u ${FRONTEND_SERVICE_NAME}.service -f"
echo " Backend Service Status:    ${SUDO} systemctl status ${BACKEND_SERVICE_NAME}.service"
echo " Backend Service Logs:    journalctl -u ${BACKEND_SERVICE_NAME}.service -f"
echo ""
log_info " IMPORTANT REMINDERS:"
log_info " 1. Ensure your production environment file (${_SOURCE_PROD_ENV_FILE}) is correctly populated with all necessary production values."
log_info " 2. Frontend is running from ${FRONTEND_DEPLOY_TARGET_DIR} as user ${SYSTEM_USER}."
log_info " 3. Backend is running from ${BACKEND_DEPLOY_TARGET_DIR} as user ${SYSTEM_USER}."
log_info " 4. Your Caddy (or other reverse proxy) configuration should be proxying to"
log_info "    Frontend: localhost:${FRONTEND_APP_PORT}"
log_info "    Backend:  localhost:${BACKEND_APP_PORT}"
log_info "--------------------------------------------------------------------"