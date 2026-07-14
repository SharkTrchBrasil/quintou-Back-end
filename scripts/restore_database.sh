#!/bin/bash

# Script de restore do banco de dados PostgreSQL
# Uso: ./restore_database.sh backup_file.sql.gz

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funções
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verifica argumentos
if [ $# -eq 0 ]; then
    log_error "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

BACKUP_FILE=$1

# Verifica se arquivo existe
if [ ! -f "$BACKUP_FILE" ]; then
    log_error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Verifica DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    log_error "DATABASE_URL environment variable is not set"
    exit 1
fi

log_warn "WARNING: This will REPLACE all data in the database!"
log_warn "Current database: $DATABASE_URL"
log_warn "Backup file: $BACKUP_FILE"
echo -n "Are you sure you want to continue? (yes/no): "
read -r confirmation

if [ "$confirmation" != "yes" ]; then
    log_info "Restore cancelled"
    exit 0
fi

log_info "Starting database restore..."

# Drop existing connections
log_info "Dropping existing database connections..."
psql "$DATABASE_URL" -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();" || true

# Restore database
log_info "Restoring from backup..."
gunzip -c "$BACKUP_FILE" | psql "$DATABASE_URL"

if [ $? -eq 0 ]; then
    log_info "Database restored successfully"
else
    log_error "Database restore failed"
    exit 1
fi

log_info "Restore process completed"
