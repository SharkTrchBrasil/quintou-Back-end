# ✅ Auditoria de Variáveis de Ambiente - Coolify vs Backend

## 📋 Comparação Completa

| Variável no Coolify | Esperada no Backend | Status | Observação |
|---------------------|---------------------|--------|------------|
| `DATABASE_URL` | ✅ `DATABASE_URL` | ✅ OK | Formato correto |
| `SECRET_KEY` | ✅ `SECRET_KEY` | ✅ OK | Usado para JWT |
| `AWS_ACCESS_KEY_ID` | ✅ `AWS_ACCESS_KEY_ID` | ✅ OK | S3 uploads |
| `AWS_REGION` | ✅ `AWS_REGION` | ✅ OK | |
| `S3_BUCKET_NAME` | ✅ `S3_BUCKET_NAME` | ✅ OK | |
| `AWS_SECRET_ACCESS_KEY` | ✅ `AWS_SECRET_ACCESS_KEY` | ✅ OK | |
| `CPFHUB_API_KEY` | ✅ `CPFHUB_API_KEY` | ✅ OK | Validação CPF |
| `MAPBOX_ACCESS_TOKEN` | ✅ `MAPBOX_ACCESS_TOKEN` | ✅ OK | Geocoding |
| `STRIPE_SECRET_KEY` | ✅ `STRIPE_SECRET_KEY` | ✅ OK | Pagamentos |
| `STRIPE_WEBHOOK_SECRET` | ✅ `STRIPE_WEBHOOK_SECRET` | ✅ OK | Webhooks |
| `STRIPE_PUBLISHABLE_KEY` | ❌ NÃO USADO | ⚠️ | Apenas frontend precisa |
| `DIDIT_API_KEY` | ✅ `DIDIT_API_KEY` | ✅ OK | KYC |
| `DIDIT_WEBHOOK_SECRET` | ✅ `DIDIT_WEBHOOK_SECRET` | ✅ OK | |
| `DIDIT_WORKFLOW_ID` | ✅ `DIDIT_WORKFLOW_ID` | ✅ OK | |

---

## ❌ VARIÁVEIS FALTANDO NO COOLIFY

**CRÍTICAS (precisam ser adicionadas)**:

```bash
# Redis (obrigatório para rate limiting e cache)
REDIS_URL=redis://seu-redis-host:6379/0

# Configuração de ambiente
ENVIRONMENT=production
CORS_ORIGINS=https://app.quintou.com,https://quintou.com

# JWT
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (escolha um)
# Opção 1: SendGrid (recomendado)
SENDGRID_API_KEY=SG.xxxxx
EMAIL_FROM=noreply@quintou.com

# Opção 2: SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=senha_app
SMTP_TLS=true
EMAIL_FROM=noreply@quintou.com

# Frontend URL (para links de reset de senha)
FRONTEND_URL=https://app.quintou.com
```

---

## ⚠️ VARIÁVEIS NO COOLIFY QUE NÃO SÃO USADAS PELO BACKEND

### `STRIPE_PUBLISHABLE_KEY`
- ❌ **Backend NÃO precisa disso**
- ✅ **Apenas o frontend/app mobile precisa**
- 📝 **Ação**: Pode remover do backend ou deixar (será ignorado)

---

## 🔧 CORREÇÕES NECESSÁRIAS NO COOLIFY

### 1. Adicionar Redis

O backend **REQUER Redis** para funcionar:

```bash
REDIS_URL=redis://seu-redis:6379/0
```

**Opções**:
- ✅ Usar Redis do Coolify (se tiver)
- ✅ Usar Redis Cloud gratuito: https://redis.com/try-free/
- ✅ Usar Upstash Redis: https://upstash.com/

**Como adicionar no Coolify**:
1. Vá em "Resources" → "Add Resource" → "Redis"
2. Ou use external Redis e adicione a URL

---

### 2. Adicionar Variáveis de Configuração

```bash
# Adicione estas no Coolify:
ENVIRONMENT=production
CORS_ORIGINS=https://app.quintou.com
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
FRONTEND_URL=https://app.quintou.com
```

---

### 3. Configurar Email

**Escolha UMA opção**:

#### Opção A: SendGrid (Recomendado)
```bash
SENDGRID_API_KEY=SG.sua_api_key
EMAIL_FROM=noreply@quintou.com
```

#### Opção B: SMTP (Gmail, Outlook, etc)
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_de_app
SMTP_TLS=true
EMAIL_FROM=seu_email@gmail.com
```

---

## 📝 VARIÁVEIS COMPLETAS PARA O COOLIFY

Copie e cole todas essas variáveis no seu painel do Coolify:

```bash
# ============================================
# OBRIGATÓRIAS
# ============================================

# Database
DATABASE_URL=postgresql+asyncpg://phfxiox7o2hkuobb1il2:5432/postgres

# JWT Auth
SECRET_KEY=P2hmLIUA3suLJFklfM6g1...  # (já tem)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis (ADICIONAR!)
REDIS_URL=redis://seu-redis:6379/0

# AWS S3
AWS_ACCESS_KEY_ID=AKIAVI34XZYEIC...  # (já tem)
AWS_SECRET_ACCESS_KEY=E8fXFvvS...  # (já tem)
AWS_REGION=us-east-1  # (já tem)
S3_BUCKET_NAME=quintou  # (já tem)

# Stripe
STRIPE_SECRET_KEY=sk_live_51H2zZL...  # (já tem)
STRIPE_WEBHOOK_SECRET=  # (vazio no print - ADICIONAR!)

# ============================================
# RECOMENDADAS
# ============================================

# Ambiente
ENVIRONMENT=production
CORS_ORIGINS=https://app.quintou.com,https://quintou.com
FRONTEND_URL=https://app.quintou.com

# Email (SendGrid OU SMTP)
SENDGRID_API_KEY=SG.xxxxx
EMAIL_FROM=noreply@quintou.com

# ============================================
# OPCIONAIS (já tem)
# ============================================

# CPF Validation
CPFHUB_API_KEY=65be919e82a080f0...  # (já tem)

# Geocoding
MAPBOX_ACCESS_TOKEN=pk.eyJ1Ijo1cj...  # (já tem)

# KYC
DIDIT_API_KEY=ZmpJNGq479cXLsJGa4...  # (já tem)
DIDIT_WEBHOOK_SECRET=600hfJz9L0...  # (já tem)
DIDIT_WORKFLOW_ID=37bf3e88-0679-...  # (já tem)

# ============================================
# NÃO USADA PELO BACKEND (pode remover)
# ============================================
# STRIPE_PUBLISHABLE_KEY=pk_live_...  # Frontend only
```

---

## 🚨 PROBLEMAS IDENTIFICADOS NO PRINT

### 1. `STRIPE_WEBHOOK_SECRET` está VAZIO
```bash
STRIPE_WEBHOOK_SECRET=
```
❌ **CRÍTICO**: Webhooks do Stripe vão falhar!

**Como obter**:
1. Acesse Stripe Dashboard
2. Developers → Webhooks
3. Adicione endpoint: `https://api.quintou.com/payments/webhook`
4. Copie o `whsec_...` e adicione no Coolify

---

### 2. Falta `REDIS_URL`
❌ **CRÍTICO**: App vai crashar ao iniciar!

**Erro que você verá**:
```
ConnectionError: Error connecting to Redis
```

**Solução**: Adicionar Redis (ver seção 1 acima)

---

### 3. Falta configuração de Email
⚠️ **IMPORTANTE**: Usuários não vão receber emails (reset de senha, confirmações)

**Solução**: Adicionar SendGrid ou SMTP (ver seção 3 acima)

---

## ✅ CHECKLIST DE VERIFICAÇÃO

Antes de fazer deploy, confirme:

- [ ] `DATABASE_URL` está correto e acessível
- [ ] `SECRET_KEY` é forte (min 32 chars, aleatório)
- [ ] `REDIS_URL` está configurado e acessível
- [ ] `STRIPE_WEBHOOK_SECRET` está preenchido (não vazio!)
- [ ] `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY` estão corretos
- [ ] `S3_BUCKET_NAME` existe e tem permissões corretas
- [ ] `ENVIRONMENT=production` está setado
- [ ] `CORS_ORIGINS` tem apenas seus domínios
- [ ] Email está configurado (SendGrid OU SMTP)
- [ ] `FRONTEND_URL` aponta para seu app

---

## 🧪 TESTANDO AS VARIÁVEIS

Depois de adicionar todas as variáveis, teste:

### 1. Health Check
```bash
curl https://api.quintou.com/health
```

Deve retornar:
```json
{
  "status": "healthy",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "s3": "configured",
    "stripe": "configured"
  }
}
```

### 2. Verifique Logs
No Coolify, veja os logs e procure por erros como:
- ❌ `ConnectionError: Redis`
- ❌ `ConfigError: SECRET_KEY`
- ❌ `AWS Error`

---

## 📋 TEMPLATE PARA COPIAR/COLAR NO COOLIFY

```bash
DATABASE_URL=postgresql+asyncpg://phfxiox7o2hkuobb1il2:5432/postgres
SECRET_KEY=P2hmLIUA3suLJFklfM6g1...
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
REDIS_URL=redis://seu-redis:6379/0
AWS_ACCESS_KEY_ID=AKIAVI34XZYEIC...
AWS_SECRET_ACCESS_KEY=E8fXFvvS...
AWS_REGION=us-east-1
S3_BUCKET_NAME=quintou
STRIPE_SECRET_KEY=sk_live_51H2zZL...
STRIPE_WEBHOOK_SECRET=whsec_ADICIONAR_AQUI
CPFHUB_API_KEY=65be919e82a080f0...
MAPBOX_ACCESS_TOKEN=pk.eyJ1Ijo1cj...
DIDIT_API_KEY=ZmpJNGq479cXLsJGa4...
DIDIT_WEBHOOK_SECRET=600hfJz9L0...
DIDIT_WORKFLOW_ID=37bf3e88-0679-...
ENVIRONMENT=production
CORS_ORIGINS=https://app.quintou.com
FRONTEND_URL=https://app.quintou.com
SENDGRID_API_KEY=SG.xxxxx
EMAIL_FROM=noreply@quintou.com
```

---

## 🎯 RESUMO

**Status Atual**: ⚠️ **FALTANDO VARIÁVEIS CRÍTICAS**

**Variáveis OK**: 11/18  
**Variáveis Faltando**: 7  
**Variáveis Críticas Faltando**: 2 (Redis, Email)

**Ação Imediata**:
1. ✅ Adicionar `REDIS_URL`
2. ✅ Preencher `STRIPE_WEBHOOK_SECRET`
3. ✅ Adicionar configuração de Email
4. ✅ Adicionar variáveis de configuração (ENVIRONMENT, CORS, etc)

Depois disso, seu backend estará **100% funcional**! 🚀
