#!/bin/bash

# -----------------------------------------------------------------------------
# Shared Configuration Variables
#
# This file defines common variables used across various setup and deployment
# scripts for the Media Telegram Processor project.
#
# IMPORTANT: Review and update placeholder values, especially DB_PASSWORD,
# before running any setup scripts that depend on this configuration.
# -----------------------------------------------------------------------------

# --- Project Structure ---
# Determine Project Root Directory dynamically
# This assumes config.sh is in scripts/lib/, so ../.. goes to project root.
PROJECT_ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

APP_DIR_RELATIVE="app" # Frontend application directory
APP_DIR="${PROJECT_ROOT_DIR}/${APP_DIR_RELATIVE}"
BACKEND_DIR_RELATIVE="backend" # Backend application directory
BACKEND_DIR="${PROJECT_ROOT_DIR}/${BACKEND_DIR_RELATIVE}"
SCRIPTS_DIR="${PROJECT_ROOT_DIR}/scripts"
LIB_DIR="${SCRIPTS_DIR}/lib"

# --- Deployment Configuration ---
SYSTEM_USER="www-data" # User for running services
SYSTEM_GROUP="www-data" # Group for running services

# Frontend Service Configuration (Next.js)
FRONTEND_DEPLOY_TARGET_DIR="/var/www/media-telegram-processor-frontend"
FRONTEND_SERVICE_NAME="media-telegram-processor-frontend"
FRONTEND_SERVICE_FILE_PATH="/etc/systemd/system/${FRONTEND_SERVICE_NAME}.service" # Used by deploy.sh
FRONTEND_APP_PORT="3112" # Port the Next.js app runs on (used in systemd service file)
NEXTAUTH_URL_PROD="https://telegram.skyvale.org" # Frontend URL for production (used in systemd service file and Caddy)

# Backend Service Configuration (FastAPI)
BACKEND_DEPLOY_TARGET_DIR="/var/www/media-telegram-processor-backend"
BACKEND_SERVICE_NAME="media-telegram-processor-backend"
BACKEND_SERVICE_FILE_PATH="/etc/systemd/system/${BACKEND_SERVICE_NAME}.service" # Used by deploy.sh
BACKEND_APP_PORT="8000" # Port the FastAPI app runs on (used in systemd service file)

# --- Secrets and Environment Files ---
# These are now standard .env files in the project root.
# Scripts should handle .env.local, .env.production, and .env.example as needed.
ENV_EXAMPLE_FILE="${PROJECT_ROOT_DIR}/.env.example"
ENV_LOCAL_FILE="${PROJECT_ROOT_DIR}/.env.local"
ENV_PROD_FILE="${PROJECT_ROOT_DIR}/.env.production"

# The final environment file to be used in the deployment target directory.
# Next.js automatically picks up '.env' in the production environment.
DEPLOY_ENV_FILE_BASENAME=".env"

# Path to the script that generates the local development environment file.
GENERATE_ENV_SCRIPT_RELATIVE_PATH="scripts/generate_secrets.sh" # Relative to PROJECT_ROOT_DIR

# --- Database Configuration (SQLite will be used, file-based, no complex setup needed here) ---
# DB_PATH="sqlite:///./sql_app.db" # Example SQLite path

# --- PNPM/Corepack Configuration ---
# Cache directory for the SYSTEM_USER (e.g., www-data) when using corepack.
# Typically /var/www/.cache/node/corepack if SYSTEM_USER's home is /var/www
COREPACK_SERVICE_USER_CACHE_DIR="/var/www/.cache/node/corepack"

# Add other shared configuration variables here as needed.

# --- Sanity Check (Optional but Recommended) ---
# Ensure critical directories derived from PROJECT_ROOT_DIR exist if scripts assume them.
# For example, ensure APP_DIR is valid:
if [ ! -d "${APP_DIR}" ]; then
    echo "Configuration Error: Media Telegram Processor Frontend application directory not found at ${APP_DIR}" >&2
    echo "PROJECT_ROOT_DIR was determined as: ${PROJECT_ROOT_DIR}" >&2
    # exit 1 # Uncomment if you want scripts to fail hard if APP_DIR is wrong
fi
if [ ! -d "${BACKEND_DIR}" ]; then
    echo "Configuration Error: Media Telegram Processor Backend application directory not found at ${BACKEND_DIR}" >&2
    echo "PROJECT_ROOT_DIR was determined as: ${PROJECT_ROOT_DIR}" >&2
    # exit 1 # Uncomment if you want scripts to fail hard if APP_DIR is wrong
fi