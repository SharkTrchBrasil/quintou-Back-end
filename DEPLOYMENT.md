# 🚀 Guia de Deployment - Quintou Backend

## Pré-requisitos

- Docker & Docker Compose
- Conta AWS (S3)
- Conta Stripe
- Domínio configurado
- SSL/TLS certificado

## Checklist Pré-Deployment

### Segurança
- [ ] `SECRET_KEY` gerada aleatoriamente (min 32 chars)
- [ ] `STRIPE_WEBHOOK_SECRET` configurado
- [ ] `CORS_ORIGINS` restrito a domínios específicos
- [ ] SSL/HTTPS habilitado
- [ ] Firewall configurado (apenas portas 80, 443)
- [ ] Database com senha forte
- [ ] Redis protegido (não expor porta 6379)

### Infraestrutura
- [ ] Bucket S3 criado e configurado
- [ ] RDS PostgreSQL provisionado (ou usar Docker)
- [ ] ElastiCache Redis (ou usar Docker)
- [ ] Domínio apontando para servidor
- [ ] SSL certificado instalado
- [ ] Backup automático configurado

### Monitoramento
- [ ] Sentry configurado
- [ ] Logs centralizados
- [ ] Alertas configurados
- [ ] Health check endpoint funcionando

## Deployment com Docker

### 1. Preparar ambiente

```bash
# Clone repositório
git clone <repo-url>
cd quintou/backend

# Crie arquivo .env
cp .env.example .env
# EDITE o .env com valores de produção
```

### 2. Configurar .env de Produção

```bash
# Gere SECRET_KEY seguro
openssl rand -hex 32

# Configure no .env
ENVIRONMENT=production
SECRET_KEY=<sua-chave-gerada>
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/quintou
REDIS_URL=redis://redis:6379/0
CORS_ORIGINS=https://app.quintou.com,https://quintou.com

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# AWS
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=quintou-prod

# Email
SENDGRID_API_KEY=...
EMAIL_FROM=noreply@quintou.com

# Firebase
FIREBASE_CREDENTIALS_JSON={"type":"service_account",...}
```

### 3. Build e Start

```bash
# Build imagens
docker-compose build

# Inicie containers
docker-compose up -d

# Verifique logs
docker-compose logs -f backend

# Verifique health
curl https://api.quintou.com/health
```

### 4. Execute Migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Seed Dados Iniciais

```bash
docker-compose exec backend python scripts/seed_data.py
```

## Deployment em VPS (Ubuntu 22.04)

### 1. Preparar Servidor

```bash
# Atualize sistema
sudo apt update && sudo apt upgrade -y

# Instale Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Instale Docker Compose
sudo apt install docker-compose-plugin

# Instale Nginx
sudo apt install nginx
```

### 2. Configure Nginx

```nginx
# /etc/nginx/sites-available/quintou
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.quintou.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.quintou.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.quintou.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.quintou.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Logs
    access_log /var/log/nginx/quintou_access.log;
    error_log /var/log/nginx/quintou_error.log;
    
    # WebSocket support
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
    
    # API endpoints
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Body size (para uploads)
        client_max_body_size 100M;
    }
}
```

```bash
# Ative site
sudo ln -s /etc/nginx/sites-available/quintou /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Configure SSL com Let's Encrypt

```bash
# Instale Certbot
sudo apt install certbot python3-certbot-nginx

# Obtenha certificado
sudo certbot --nginx -d api.quintou.com

# Auto-renovação já está configurada
```

### 4. Configure Backup Automático

```bash
# Edite crontab
crontab -e

# Adicione linha para backup diário às 2am
0 2 * * * /home/quintou/backend/scripts/backup_database.sh >> /var/log/quintou_backup.log 2>&1
```

## Deployment em AWS

### Opção 1: ECS Fargate

1. **Push imagem para ECR**:
```bash
aws ecr create-repository --repository-name quintou-backend
docker tag quintou-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/quintou-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/quintou-backend:latest
```

2. **Configure RDS PostgreSQL**
3. **Configure ElastiCache Redis**
4. **Crie Task Definition no ECS**
5. **Configure ALB**
6. **Crie Service no ECS**

### Opção 2: EC2

Similar ao deployment em VPS (veja acima).

### Opção 3: Elastic Beanstalk

```bash
# Instale EB CLI
pip install awsebcli

# Inicialize
eb init

# Deploy
eb create quintou-production
```

## Monitoramento

### 1. Configure Sentry

```python
# Adicione ao requirements.txt
sentry-sdk[fastapi]

# Configure em app/main.py
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

sentry_sdk.init(
    dsn="https://...@sentry.io/...",
    traces_sample_rate=0.1,
    environment="production"
)
```

### 2. Configure Alertas

```bash
# Exemplo com Uptime Robot ou similar
# Configure alertas para:
- /health endpoint (HTTP 200)
- Database connectivity
- Redis connectivity
- Resposta < 2 segundos
```

### 3. Logs

```bash
# Centralizar logs com CloudWatch, Datadog, ou similar
docker-compose logs -f backend | tee -a /var/log/quintou/app.log
```

## Rollback

```bash
# Volte para versão anterior
git checkout <previous-commit>
docker-compose build
docker-compose up -d

# Ou use tag específica
docker-compose pull <tag-anterior>
docker-compose up -d
```

## Troubleshooting

### Container não inicia

```bash
# Verifique logs
docker-compose logs backend

# Verifique variáveis de ambiente
docker-compose config

# Entre no container
docker-compose exec backend bash
```

### Database connection error

```bash
# Teste conexão manualmente
docker-compose exec backend python -c "from app.database import engine; import asyncio; asyncio.run(engine.connect())"
```

### High CPU/Memory

```bash
# Monitore recursos
docker stats

# Verifique queries lentas
docker-compose exec db psql -U postgres -c "SELECT * FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;"
```

## Manutenção

### Atualização de Dependências

```bash
# Atualize requirements.txt
pip install -U <package>
pip freeze > requirements.txt

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Database Migration

```bash
# Sempre teste em staging primeiro!
docker-compose exec backend alembic upgrade head
```

### Backup Manual

```bash
./scripts/backup_database.sh
```

### Restore

```bash
./scripts/restore_database.sh backup_20261231.sql.gz
```

## Suporte

- Documentação: https://docs.quintou.com
- Issues: https://github.com/quintou/backend/issues
- Email: dev@quintou.com
