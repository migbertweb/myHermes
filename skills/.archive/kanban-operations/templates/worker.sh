#!/bin/bash
# Worker script template for Hermes kanban tasks
# Usage: ./worker.sh <task_id> <workspace_path>
#
# Every worker MUST exit by calling:
#   hermes kanban complete <task_id>      # success
#   hermes kanban block <task_id> --reason "..."  # blocked
#
# Otherwise: worker exits rc=0 → protocol_violation → dispatcher retries
# until failure_limit → task blocks.

set -euo pipefail

TASK_ID="$1"
WORKSPACE="$2"
LOG_FILE="/tmp/worker-${TASK_ID}.log"

log() {
  echo "[$(date -Iseconds)] $*" >> "$LOG_FILE"
  echo "[$(date -Iseconds)] $*"
}

cleanup() {
  local exit_code=$?
  if [[ $exit_code -ne 0 ]]; then
    log "Worker failed with exit code $exit_code"
    # Report block with reason
    hermes kanban block "$TASK_ID" --reason "Worker failed: see log at $LOG_FILE" || true
  fi
  exit $exit_code
}
trap cleanup EXIT

# Validate args
if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <task_id> <workspace_path>" >&2
  exit 1
fi

log "Starting worker for task $TASK_ID in $WORKSPACE"

# Change to workspace
cd "$WORKSPACE" || { log "Cannot cd to $WORKSPACE"; exit 1; }

# === YOUR TASK LOGIC GOES HERE ===
# Example:
# echo "Building game hub page..."
# cat > src/pages/GameHub.jsx << 'GAMEHUB'
# import EnRaya from './EnRaya';
# import Snake from './Snake';
# export default function GameHub() { ... }
# GAMEHUB

# === MANDATORY: report result ===
# On success:
hermes kanban complete "$TASK_ID"
log "Task $TASK_ID marked complete"
