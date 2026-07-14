#!/bin/bash

# Script de backup automático do banco de dados PostgreSQL
# Adicione ao cron para execução diária: 0 2 * * * /path/to/backup_database.sh

set -e

# Configurações
BACKUP_DIR="${BACKUP_DIR:-/var/backups/quintou}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="quintou_backup_${DATE}.sql.gz"

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

# Criar diretório de backup se não existir
mkdir -p "$BACKUP_DIR"

log_info "Starting database backup..."

# Verifica se DATABASE_URL está definida
if [ -z "$DATABASE_URL" ]; then
    log_error "DATABASE_URL environment variable is not set"
    exit 1
fi

# Realiza backup
log_info "Backing up to: $BACKUP_DIR/$BACKUP_FILE"
pg_dump "$DATABASE_URL" | gzip > "$BACKUP_DIR/$BACKUP_FILE"

if [ $? -eq 0 ]; then
    log_info "Backup completed successfully"
    
    # Verifica tamanho do backup
    SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
    log_info "Backup size: $SIZE"
else
    log_error "Backup failed"
    exit 1
fi

# Remove backups antigos
log_info "Removing backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "quintou_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

# Lista backups existentes
log_info "Current backups:"
ls -lh "$BACKUP_DIR"/quintou_backup_*.sql.gz | tail -5

# Upload para S3 (opcional)
if [ ! -z "$AWS_BACKUP_BUCKET" ]; then
    log_info "Uploading backup to S3..."
    aws s3 cp "$BACKUP_DIR/$BACKUP_FILE" "s3://$AWS_BACKUP_BUCKET/database-backups/" --storage-class STANDARD_IA
    
    if [ $? -eq 0 ]; then
        log_info "Backup uploaded to S3 successfully"
    else
        log_warn "Failed to upload backup to S3"
    fi
fi

log_info "Backup process completed"
