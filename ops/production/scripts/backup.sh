#!/usr/bin/env bash
# Production backup script for Finance Suite.
# Creates timestamped backups under /home/ubuntu/backups and keeps 7 days.

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/finance-suite-web}"
MCP_DIR="${MCP_DIR:-/home/ubuntu/finance-suite}"
NGINX_DIR="${NGINX_DIR:-/etc/nginx}"
SYSTEMD_UNIT="${SYSTEMD_UNIT:-/etc/systemd/system/finance-suite.service}"
BACKUP_ROOT="${BACKUP_ROOT:-/home/ubuntu/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

STAMP="$(date +%Y%m%d-%H%M%S)"
WORK_DIR="$BACKUP_ROOT/finance-suite-$STAMP"
ARCHIVE="$BACKUP_ROOT/finance-suite-$STAMP.tar.gz"

if [ -e "$WORK_DIR" ] || [ -e "$ARCHIVE" ]; then
  echo "ERROR: backup target already exists: $WORK_DIR or $ARCHIVE" >&2
  exit 1
fi

mkdir -p "$WORK_DIR"

copy_if_exists() {
  local src="$1"
  local dst="$2"
  if [ -e "$src" ]; then
    mkdir -p "$(dirname "$dst")"
    cp -a "$src" "$dst"
    echo "Backed up $src"
  else
    echo "WARN: missing $src; skipped" >&2
  fi
}

copy_dir_if_exists() {
  local src="$1"
  local dst="$2"
  if [ -d "$src" ]; then
    mkdir -p "$(dirname "$dst")"
    rsync -a \
      --exclude 'venv/' \
      --exclude '.venv/' \
      --exclude '__pycache__/' \
      --exclude '*.pyc' \
      "$src/" "$dst/"
    echo "Backed up $src"
  else
    echo "WARN: missing $src; skipped" >&2
  fi
}

copy_dir_if_exists "$PROJECT_DIR" "$WORK_DIR/finance-suite-web"
copy_dir_if_exists "$MCP_DIR" "$WORK_DIR/finance-suite"
copy_dir_if_exists "$NGINX_DIR" "$WORK_DIR/etc/nginx"
copy_if_exists "$SYSTEMD_UNIT" "$WORK_DIR/etc/systemd/system/finance-suite.service"

copy_if_exists "$PROJECT_DIR/.env" "$WORK_DIR/secrets/finance-suite-web.env"
copy_if_exists "$MCP_DIR/.env" "$WORK_DIR/secrets/finance-suite.env"

find "$PROJECT_DIR" "$MCP_DIR" -maxdepth 3 -type f \( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \) 2>/dev/null |
while IFS= read -r db_file; do
  rel="${db_file#/}"
  copy_if_exists "$db_file" "$WORK_DIR/databases/$rel"
done

tar -C "$BACKUP_ROOT" -czf "$ARCHIVE" "finance-suite-$STAMP"
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
rm -rf "$WORK_DIR"

echo "Backup created:"
ls -lh "$ARCHIVE" "$ARCHIVE.sha256"

find "$BACKUP_ROOT" -maxdepth 1 -type f \( -name 'finance-suite-*.tar.gz' -o -name 'finance-suite-*.tar.gz.sha256' \) -mtime +"$RETENTION_DAYS" -delete

echo "Retention applied: ${RETENTION_DAYS} days"

