# 🚀 GUIA DE DEPLOY - QUINTOU BACKEND

**Versão:** 2.0 (Pós-Correções)  
**Data:** 13 de Julho de 2026  
**Ambiente:** Produção

---

## 📋 PRÉ-REQUISITOS

### Serviços Externos Necessários

1. **✅ PostgreSQL** (v14+)
   - Database criado
   - Usuário com permissões
   - URL de conexão

2. **✅ Stripe Account**
   - Conta verificada
   - API Keys (live mode)
   - Webhook configurado
   - Connect habilitado (para split payments)

3. **✅ AWS S3**
   - Bucket criado
   - IAM user com permissões
   - Access Key + Secret Key
   - CORS configurado

4. **✅ Provedor de Email**
   - **Opção A:** SendGrid (recomendado)
     - Conta criada
     - API Key
     - Domínio verificado
   - **Opção B:** SMTP
     - Host, porta, credenciais
     - App password (se Gmail)

5. **✅ Firebase** (Notificações Push)
   - Projeto criado
   - Service account JSON
   - FCM habilitado

6. **✅ APIs Opcionais**
   - Mapbox (geocoding)
   - CPFHub (validação de CPF)

---

## 📦 INSTALAÇÃO

### 1. Clone e Dependências

```bash
# Clone o repositório
git clone https://github.com/seu-repo/quintou-backend.git
cd quintou-backend

# Crie ambiente virtual
python -m venv venv

# Ative o ambiente
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale dependências
pip install -r requirements.txt
```

### 2. Configuração de Variáveis de Ambiente

Crie o arquivo `.env` na raiz do projeto:

```env
# ==========================================
# DATABASE
# ==========================================
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/quintou_production

# ==========================================
# JWT AUTHENTICATION
# ==========================================
SECRET_KEY=gere_uma_chave_secreta_super_forte_aqui_256_bits
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ==========================================
# AWS S3 (Upload de Imagens)
# ==========================================
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
S3_BUCKET_NAME=quintou-production-images

# ==========================================
# STRIPE (Pagamentos)
# ==========================================
STRIPE_SECRET_KEY=sk_live_sua_chave_live_aqui
STRIPE_WEBHOOK_SECRET=whsec_seu_webhook_secret_aqui

# ==========================================
# EMAIL (SendGrid - RECOMENDADO)
# ==========================================
SENDGRID_API_KEY=SG.sua_api_key_sendgrid
EMAIL_FROM=noreply@quintou.com

# ==========================================
# EMAIL ALTERNATIVO (SMTP)
# ==========================================
# Descomente se não usar SendGrid
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=seu_email@gmail.com
# SMTP_PASSWORD=sua_senha_de_app
# SMTP_TLS=true
# EMAIL_FROM=seu_email@gmail.com

# ==========================================
# FIREBASE (Notificações Push)
# ==========================================
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json

# ==========================================
# APIS EXTERNAS
# ==========================================
CPFHUB_API_KEY=sua_chave_cpfhub
MAPBOX_ACCESS_TOKEN=pk.sua_chave_mapbox

# ==========================================
# FRONTEND URL
# ==========================================
FRONTEND_URL=https://app.quintou.com

# ==========================================
# CONFIGURAÇÕES DA API
# ==========================================
ENVIRONMENT=production
CORS_ORIGINS=https://app.quintou.com,https://www.quintou.com
```

### 3. Gerar Secret Key Segura

```python
# Execute este script Python para gerar uma chave segura
import secrets
print(secrets.token_urlsafe(64))
```

---

## 🗄️ MIGRAÇÃO DO BANCO DE DADOS

### 1. Aplicar Migrações

```bash
# Verificar status atual
alembic current

# Ver histórico de migrações
alembic history

# Aplicar todas as migrações
alembic upgrade head

# Verificar se password_reset_tokens foi criado
alembic current
# Deve mostrar: add_password_reset (head)
```

### 2. Verificar Schema

```sql
-- Conecte ao PostgreSQL e verifique
\dt

-- Tabelas esperadas:
-- users
-- spaces
-- space_images
-- space_addons
-- space_pricing_tiers
-- space_promotions
-- availability_rules
-- bookings
-- booking_addons
-- payments
-- reviews
-- categories
-- conversations
-- messages
-- favorites
-- notifications
-- reports
-- password_reset_tokens ✨ NOVA

-- Verificar campos da tabela users
\d users

-- Deve incluir:
-- fcm_token
-- stripe_account_status
```

---

## 🔐 CONFIGURAÇÃO DO STRIPE

### 1. Webhook Configuration

1. Acesse https://dashboard.stripe.com/webhooks
2. Clique em "Add endpoint"
3. URL: `https://api.quintou.com/payments/webhook`
4. Eventos para escutar:
   - ✅ `account.updated`
   - ✅ `checkout.session.completed`
   - ✅ `payment_intent.succeeded`
5. Copie o "Signing secret" (`whsec_...`)
6. Adicione ao `.env` como `STRIPE_WEBHOOK_SECRET`

### 2. Testar Webhook

```bash
# Instale Stripe CLI
# https://stripe.com/docs/stripe-cli

# Faça login
stripe login

# Teste o webhook
stripe trigger checkout.session.completed

# Monitore eventos em tempo real
stripe listen --forward-to https://api.quintou.com/payments/webhook
```

### 3. Stripe Connect

Certifique-se de que:
- ✅ Stripe Connect está habilitado na sua conta
- ✅ Express accounts configurados para Brasil
- ✅ Documentos necessários para KYC definidos
- ✅ Webhooks de Connect configurados

---

## 📧 CONFIGURAÇÃO DE EMAIL

### Opção A: SendGrid (Recomendado)

```bash
# 1. Crie conta em sendgrid.com
# 2. Verifique seu domínio (noreply@quintou.com)
# 3. Crie API Key com permissão "Mail Send"
# 4. Adicione ao .env:
SENDGRID_API_KEY=SG.sua_chave
EMAIL_FROM=noreply@quintou.com

# 5. Teste o envio
curl -X POST https://api.quintou.com/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```

### Opção B: Gmail SMTP

```bash
# 1. Ative verificação em 2 etapas na sua conta Google
# 2. Gere uma "Senha de app": https://myaccount.google.com/apppasswords
# 3. Configure no .env:
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_de_app_de_16_caracteres
SMTP_TLS=true
EMAIL_FROM=seu_email@gmail.com
```

---

## 🔥 CONFIGURAÇÃO DO FIREBASE

### 1. Obter Credenciais

1. Acesse https://console.firebase.google.com
2. Selecione seu projeto
3. Vá em **Project Settings** > **Service Accounts**
4. Clique em **Generate New Private Key**
5. Baixe o JSON
6. Renomeie para `firebase-credentials.json`

### 2. Upload das Credenciais

```bash
# No servidor de produção
mkdir -p /app
cp firebase-credentials.json /app/firebase-credentials.json
chmod 600 /app/firebase-credentials.json

# Ou use secrets do Docker/Kubernetes
```

---

## 🐳 DEPLOY COM DOCKER

### 1. Dockerfile

Crie `Dockerfile` na raiz:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia aplicação
COPY . .

# Expõe porta
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. docker-compose.yml (Desenvolvimento)

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: quintou
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
    volumes:
      - ./firebase-credentials.json:/app/firebase-credentials.json:ro

volumes:
  postgres_data:
```

### 3. Build e Run

```bash
# Build da imagem
docker build -t quintou-backend:latest .

# Run com docker-compose
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Aplicar migrações
docker-compose exec api alembic upgrade head
```

---

## ☸️ DEPLOY NO KUBERNETES

### 1. Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: quintou-secrets
type: Opaque
stringData:
  DATABASE_URL: "postgresql+asyncpg://user:pass@host/db"
  SECRET_KEY: "sua_secret_key"
  STRIPE_SECRET_KEY: "sk_live_..."
  STRIPE_WEBHOOK_SECRET: "whsec_..."
  SENDGRID_API_KEY: "SG...."
  AWS_ACCESS_KEY_ID: "AKIA..."
  AWS_SECRET_ACCESS_KEY: "..."
```

### 2. Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quintou-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: quintou-backend
  template:
    metadata:
      labels:
        app: quintou-backend
    spec:
      containers:
      - name: api
        image: quintou-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: quintou-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 3. Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: quintou-backend
spec:
  selector:
    app: quintou-backend
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 4. Apply

```bash
kubectl apply -f secrets.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Verificar
kubectl get pods
kubectl logs -f deployment/quintou-backend
```

---

## 🔍 VERIFICAÇÃO PÓS-DEPLOY

### 1. Health Check

```bash
curl https://api.quintou.com/health

# Resposta esperada:
{
  "status": "healthy",
  "version": "2.0",
  "environment": "production"
}
```

### 2. Teste de Autenticação

```bash
# Registrar usuário
curl -X POST https://api.quintou.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@quintou.com",
    "password": "Test123!",
    "full_name": "Test User",
    "cpf": "12345678900",
    "phone": "11999999999"
  }'

# Login
curl -X POST https://api.quintou.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@quintou.com",
    "password": "Test123!"
  }'
```

### 3. Teste de Reset de Senha

```bash
# Solicitar reset
curl -X POST https://api.quintou.com/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@quintou.com"}'

# Verificar se email foi enviado (logs ou inbox)
```

### 4. Teste de Pagamento (Stripe)

```bash
# Criar booking (autenticado)
curl -X POST https://api.quintou.com/bookings \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "space_id": "uuid-do-espaco",
    "date": "2026-08-01",
    "start_time": "14:00",
    "end_time": "18:00",
    "num_guests": 10
  }'

# Criar payment intent
curl -X POST https://api.quintou.com/payments/create-intent \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booking_id": "uuid-do-booking"
  }'

# Verificar se client_secret é real (começa com "pi_")
```

---

## 📊 MONITORAMENTO

### 1. Logs

```bash
# Docker
docker-compose logs -f api

# Kubernetes
kubectl logs -f deployment/quintou-backend

# Grep erros
kubectl logs deployment/quintou-backend | grep ERROR
```

### 2. Sentry (Recomendado)

```bash
# Instale
pip install sentry-sdk[fastapi]

# Configure em app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://your-dsn@sentry.io/project",
    integrations=[FastApiIntegration()],
    environment="production",
    traces_sample_rate=0.1
)
```

### 3. Métricas

- **Latência:** Tempo de resposta das APIs
- **Taxa de erro:** % de requests com status 5xx
- **Uso de CPU/Memória:** Monitorar container
- **Database connections:** Pool size
- **Stripe webhooks:** Taxa de sucesso

---

## 🔄 ROLLBACK

### Docker

```bash
# Voltar para versão anterior
docker tag quintou-backend:latest quintou-backend:backup
docker pull quintou-backend:v1.0
docker tag quintou-backend:v1.0 quintou-backend:latest
docker-compose up -d
```

### Kubernetes

```bash
# Ver histórico
kubectl rollout history deployment/quintou-backend

# Rollback
kubectl rollout undo deployment/quintou-backend

# Rollback para versão específica
kubectl rollout undo deployment/quintou-backend --to-revision=2
```

### Banco de Dados

```bash
# Reverter migração
alembic downgrade -1

# Voltar para revisão específica
alembic downgrade 99e2d648c27b
```

---

## 🚨 TROUBLESHOOTING

### Problema: Webhook do Stripe falha

**Sintoma:** Bookings não confirmam após pagamento

**Solução:**
```bash
# 1. Verifique se STRIPE_WEBHOOK_SECRET está correto
echo $STRIPE_WEBHOOK_SECRET

# 2. Teste o endpoint manualmente
stripe trigger checkout.session.completed

# 3. Verifique logs
grep "stripe" logs/app.log

# 4. Verifique assinatura
curl -X POST https://api.quintou.com/payments/webhook \
  -H "stripe-signature: test"
```

### Problema: Emails não são enviados

**Sintoma:** Reset de senha não chega

**Solução:**
```bash
# 1. Verifique provider configurado
# Deve ser "sendgrid", "smtp", ou "console"

# 2. Teste SendGrid
curl -X POST https://api.sendgrid.com/v3/mail/send \
  -H "Authorization: Bearer $SENDGRID_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{...}'

# 3. Verifique logs
grep "email" logs/app.log
```

### Problema: CPF duplicado permitido

**Sintoma:** Múltiplos usuários com mesmo CPF

**Solução:**
```bash
# Verificar se correção foi aplicada
grep "cpf_check" app/services/auth_service.py

# Deve mostrar a validação implementada
```

---

## 📝 CHECKLIST DE DEPLOY

### Antes do Deploy

- [ ] Todas as variáveis de ambiente configuradas
- [ ] Secret key gerada (256 bits)
- [ ] Banco de dados criado
- [ ] Stripe account verificado
- [ ] Webhook do Stripe configurado
- [ ] S3 bucket criado e CORS configurado
- [ ] SendGrid ou SMTP configurado
- [ ] Firebase credentials baixadas
- [ ] Domínio do frontend configurado
- [ ] SSL/TLS configurado (HTTPS)

### Durante o Deploy

- [ ] Build da imagem Docker
- [ ] Upload das credenciais Firebase
- [ ] Aplicar migrações do Alembic
- [ ] Verificar health endpoint
- [ ] Testar autenticação
- [ ] Testar reset de senha
- [ ] Testar criação de booking
- [ ] Testar pagamento Stripe
- [ ] Testar webhook Stripe

### Depois do Deploy

- [ ] Monitoramento configurado (Sentry)
- [ ] Logs sendo coletados
- [ ] Backups agendados
- [ ] Alertas configurados
- [ ] Documentação atualizada
- [ ] Equipe treinada
- [ ] Plano de rollback pronto

---

## 🎯 PRÓXIMOS PASSOS

1. **CI/CD Pipeline**
   - GitHub Actions ou GitLab CI
   - Testes automatizados
   - Deploy automático em staging

2. **Testes de Carga**
   - k6 ou Locust
   - Simular 1000+ usuários simultâneos
   - Identificar gargalos

3. **Otimizações**
   - Cache (Redis)
   - CDN para imagens
   - Database indexing
   - Query optimization

4. **Segurança**
   - Rate limiting
   - DDoS protection
   - Security headers
   - Audit logging

---

**Documento criado por Kiro AI**  
**Última atualização:** 13/07/2026

Para suporte: tech@quintou.com
