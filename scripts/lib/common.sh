#!/bin/bash

# -----------------------------------------------------------------------------
# Common Bash Functions Library
#
# This library provides shared functions for logging, command checks,
# user/group management, pnpm/corepack setup, and permission settings
# to be used by various setup and deployment scripts.
#
# Scripts using this library should source it, e.g:
# source "${SCRIPTS_DIR}/lib/common.sh"
# (Assumes SCRIPTS_DIR is defined, typically from config.sh)
# -----------------------------------------------------------------------------

# --- Sudo Handling ---
# If the script is not running in an interactive terminal, use -S to read from stdin.
# This prevents sudo from hanging waiting for a password.
if ! tty -s; then
    SUDO="sudo -S"
else
    SUDO="sudo"
fi

# --- Logging Functions ---
# Standardized logging with timestamps and levels.

_log() {
    local level="$1"
    shift
    echo "$(date '+%Y-%m-%d %H:%M:%S') [${level}] - $*
"
}

log_info() {
    _log "INFO" "$@"
}

log_warning() {
    _log "WARNING" "$@" >&2
}

log_error() {
    _log "ERROR" "$@" >&2
    # Consider exiting on error, or let calling script decide.
    # For now, just logs to stderr.
}

log_fatal() {
    _log "FATAL" "$@" >&2
    exit 1
}

# --- Prerequisite Checks ---

# Ensures a command exists, exits fatally if not.
# Usage: ensure_command_exists "command_name" ["optional_package_name_for_hint"]
ensure_command_exists() {
    local cmd="$1"
    local pkg_hint="$2"
    if ! command -v "${cmd}" &> /dev/null; then
        local msg="Command '${cmd}' not found. Please install it."
        if [ -n "${pkg_hint}" ]; then
            msg="${msg} (Package might be '${pkg_hint}')"
        fi
        log_fatal "${msg}"
    fi
}

# --- User and Group Management ---

# Ensures a user and group exist. Creates them if they don't.
# Usage: ensure_user_group_exists "user_name" "group_name" ["system_account_flag"]
# If system_account_flag is "system", creates a system account.
ensure_user_group_exists() {
    local user_name="$1"
    local group_name="$2"
    local system_flag="$3" # "system" or empty

    if ! getent group "${group_name}" &> /dev/null; then
        log_info "Group '${group_name}' does not exist. Creating..."
        if ${SUDO} groupadd "${group_name}"; then
            log_info "Group '${group_name}' created."
        else
            log_fatal "Failed to create group '${group_name}'."
        fi
    else
        log_info "Group '${group_name}' already exists."
    fi

    if ! id "${user_name}" &> /dev/null; then
        log_info "User '${user_name}' does not exist. Creating..."
        local useradd_opts=""
        if [ "${system_flag}" == "system" ]; then
            # System account: no home dir by default (-M), no user group (-N), system account (-r)
            # Set shell to nologin for security.
            # Set a conventional home for web server users, even if not strictly used.
            useradd_opts="-r -M -N -g ${group_name} -s /usr/sbin/nologin -d /var/www"
        else
            # Regular account (adjust options as needed if this function is used for non-system users)
            useradd_opts="-g ${group_name}"
        fi
        
        if ${SUDO} useradd ${useradd_opts} "${user_name}"; then
            log_info "User '${user_name}' created."
        else
            log_fatal "Failed to create user '${user_name}'."
        fi
    else
        log_info "User '${user_name}' already exists."
    fi
}

# --- PNPM/Corepack Setup Functions ---

# Sets up pnpm system-wide via corepack.
# This makes *a* version of pnpm generally available.
# Assumes corepack is available or will be installed if npm is present.
setup_system_pnpm_via_corepack() {
    log_info "Ensuring pnpm is available system-wide via corepack..."
    ensure_command_exists "sudo"

    if ! command -v corepack &> /dev/null; then
        log_warning "corepack command not found globally. Attempting to install via npm..."
        ensure_command_exists "npm" "nodejs"
        if ${SUDO} npm i -g corepack; then
            log_info "Corepack installed globally via npm."
            # Re-check after install
            ensure_command_exists "corepack" "corepack"
        else
            log_fatal "Failed to install corepack globally via npm. Please install it manually."
        fi
    fi

    if ${SUDO} corepack enable; then
        log_info "Corepack enabled system-wide."
    else
        log_fatal "Failed to enable corepack system-wide."
    fi
    # Prepare a recent version of pnpm. 'latest' might be too volatile for some.
    # Using a known good recent version or allowing it to be configured might be better.
    # For now, let's use 'latest' as in the original 06_setup_user.sh.
    if ${SUDO} corepack prepare pnpm@latest --activate; then
        log_info "pnpm@latest prepared and activated system-wide via corepack."
    else
        log_fatal "Failed to prepare pnpm@latest system-wide via corepack."
    fi
}

# Prepares the pnpm environment for a specific service user.
# This ensures the service user runs the *intended* version of pnpm.
# Parameters sourced from config.sh:
# - SYSTEM_USER
# - SYSTEM_GROUP
# - COREPACK_SERVICE_USER_CACHE_DIR
prepare_service_user_pnpm_environment() {
    log_info "Preparing pnpm environment for service user '${SYSTEM_USER}'..."
    ensure_command_exists "sudo"
    ensure_command_exists "pnpm" "pnpm (via corepack or global install)" # For 'pnpm -v'

    # This function assumes config.sh has been sourced and variables are available.
    if [ -z "${SYSTEM_USER}" ] || [ -z "${SYSTEM_GROUP}" ] || [ -z "${COREPACK_SERVICE_USER_CACHE_DIR}" ]; then
        log_fatal "SYSTEM_USER, SYSTEM_GROUP, or COREPACK_SERVICE_USER_CACHE_DIR not set. Source config.sh."
    fi

    local current_pnpm_version
    current_pnpm_version=$(pnpm -v)
    if [ -z "${current_pnpm_version}" ]; then
        log_fatal "Could not determine current pnpm version. Ensure pnpm is installed and in PATH for the deploying user."
    fi
    log_info "Current pnpm version (from deploying environment) is ${current_pnpm_version}."
    log_info "Preparing this pnpm version for '${SYSTEM_USER}' via corepack."

    log_info "Ensuring corepack cache directory exists for '${SYSTEM_USER}' at ${COREPACK_SERVICE_USER_CACHE_DIR}..."
    if ${SUDO} mkdir -p "${COREPACK_SERVICE_USER_CACHE_DIR}"; then
        log_info "Corepack cache directory ensured."
    else
        log_fatal "Failed to create corepack cache directory: ${COREPACK_SERVICE_USER_CACHE_DIR}"
    fi
    
    # Ensure .cache and its parent /var/www (if applicable) are accessible and owned correctly.
    # This chown might be broad; adjust if /var/www has other specific ownership needs.
    # Example: if COREPACK_SERVICE_USER_CACHE_DIR is /var/www/.cache/node/corepack, then /var/www/.cache needs correct ownership.
    local cache_parent_dir
    cache_parent_dir=$(dirname "${COREPACK_SERVICE_USER_CACHE_DIR}") # e.g. /var/www/.cache/node
    cache_parent_dir=$(dirname "${cache_parent_dir}") # e.g. /var/www/.cache
    
    log_info "Setting ownership of '${cache_parent_dir}' to '${SYSTEM_USER}:${SYSTEM_GROUP}'..."
    if ${SUDO} chown -R "${SYSTEM_USER}:${SYSTEM_GROUP}" "${cache_parent_dir}"; then
        log_info "Ownership set for '${cache_parent_dir}'."
    else
        log_warning "Failed to set ownership for '${cache_parent_dir}'. Corepack might have issues for '${SYSTEM_USER}'."
        # Not making this fatal as the directory might already have correct permissions or be non-critical in some setups.
    fi

    log_info "Running corepack commands as '${SYSTEM_USER}'..."
    if ${SUDO} -u "${SYSTEM_USER}" -H bash -c "export NVM_DIR=/var/www/.nvm; [ -s \"$NVM_DIR/nvm.sh\" ] && \. \"$NVM_DIR/nvm.sh\"; corepack enable"; then
        log_info "Corepack enabled for '${SYSTEM_USER}'."
    else
        log_fatal "Failed to enable corepack for '${SYSTEM_USER}'."
    fi

    if ${SUDO} -u "${SYSTEM_USER}" -H bash -c "export NVM_DIR=/var/www/.nvm; [ -s \"$NVM_DIR/nvm.sh\" ] && \. \"$NVM_DIR/nvm.sh\"; corepack prepare pnpm@${current_pnpm_version} --activate"; then
        log_info "pnpm@${current_pnpm_version} prepared and activated for '${SYSTEM_USER}'."
    else
        log_fatal "Failed to prepare pnpm@${current_pnpm_version} for '${SYSTEM_USER}'."
    fi
}

# --- File System Permissions ---

# Sets standard ownership and permissions for a target directory.
# Usage: set_target_ownership_and_permissions "/path/to/target" "owner_user" "owner_group"
set_target_ownership_and_permissions() {
    local target_dir="$1"
    local owner_user="$2"
    local owner_group="$3"

    if [ -z "${target_dir}" ] || [ -z "${owner_user}" ] || [ -z "${owner_group}" ]; then
        log_fatal "Usage: set_target_ownership_and_permissions <target_dir> <owner_user> <owner_group>"
    fi

    log_info "Setting final ownership for '${target_dir}' to '${owner_user}:${owner_group}'..."
    if ${SUDO} chown -R "${owner_user}:${owner_group}" "${target_dir}"; then
        log_info "Ownership set."
    else
        log_fatal "Failed to set ownership for '${target_dir}'."
    fi

    log_info "Setting permissions for '${target_dir}' (u=rwX, g=rX, o=)...\n"
    # u=rwX: User gets read, write, execute (execute only for directories or if already executable for files).
    # g=rX: Group gets read, execute.
    # o=: Others get nothing.
    if ${SUDO} chmod -R u=rwX,g=rX,o= "${target_dir}"; then
        log_info "Permissions set."
    else
        log_fatal "Failed to set permissions for '${target_dir}'."
    fi
}

log_info "Common functions library (common.sh) loaded.
"
