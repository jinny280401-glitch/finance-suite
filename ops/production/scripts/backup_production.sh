#!/usr/bin/env bash
# Create a production backup for Finance Suite.
# Run on the Tencent Cloud server.

set -euo pipefail

WEB_DIR="${WEB_DIR:-/home/ubuntu/finance-suite-web}"
MCP_DIR="${MCP_DIR:-/home/ubuntu/finance-suite}"
BACKUP_ROOT="${BACKUP_ROOT:-/home/ubuntu/backups/finance-suite}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

STAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE="$BACKUP_ROOT/finance-suite-$STAMP.tar.gz"

mkdir -p "$BACKUP_ROOT"

INCLUDES=()

if [ -d "$WEB_DIR" ]; then
  INCLUDES+=("finance-suite-web")
else
  echo "WARN: missing $WEB_DIR; skipping web directory" >&2
fi

if [ -d "$MCP_DIR" ]; then
  INCLUDES+=("finance-suite")
else
  echo "WARN: missing $MCP_DIR; skipping MCP directory" >&2
fi

if [ "${#INCLUDES[@]}" -eq 0 ]; then
  echo "ERROR: no production directories found" >&2
  exit 1
fi

echo "Creating backup: $ARCHIVE"

tar \
  --exclude='finance-suite-web/venv' \
  --exclude='finance-suite-web/.venv' \
  --exclude='finance-suite-web/__pycache__' \
  --exclude='finance-suite-web/*/__pycache__' \
  --exclude='finance-suite-web/*/*/__pycache__' \
  --exclude='finance-suite-web/*/*/*/__pycache__' \
  --exclude='*.pyc' \
  --exclude='finance-suite/.venv' \
  --exclude='finance-suite/venv' \
  --exclude='finance-suite/__pycache__' \
  --exclude='finance-suite/*/__pycache__' \
  --exclude='finance-suite/*/*/__pycache__' \
  --exclude='finance-suite/*/*/*/__pycache__' \
  -C /home/ubuntu \
  -czf "$ARCHIVE" \
  "${INCLUDES[@]}"

sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"

echo "Backup complete:"
ls -lh "$ARCHIVE" "$ARCHIVE.sha256"

echo "Removing backups older than $RETENTION_DAYS days from $BACKUP_ROOT"
find "$BACKUP_ROOT" -type f \( -name 'finance-suite-*.tar.gz' -o -name 'finance-suite-*.tar.gz.sha256' \) -mtime +"$RETENTION_DAYS" -delete

echo "Recent backups:"
ls -1t "$BACKUP_ROOT"/finance-suite-*.tar.gz 2>/dev/null | head -10 || true
