# 🛠️ COMANDOS ÚTEIS - QUINTOU BACKEND

Referência rápida de comandos para desenvolvimento e operação.

---

## 🚀 DESENVOLVIMENTO

### Iniciar Servidor

```bash
# Desenvolvimento (com auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Com log detalhado
uvicorn app.main:app --reload --log-level debug

# Produção (múltiplos workers)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Ambiente Virtual

```bash
# Criar
python -m venv venv

# Ativar (Windows)
venv\Scripts\activate

# Ativar (Linux/Mac)
source venv/bin/activate

# Desativar
deactivate

# Instalar dependências
pip install -r requirements.txt

# Atualizar requirements
pip freeze > requirements.txt
```

---

## 🗄️ BANCO DE DADOS

### PostgreSQL

```bash
# Conectar ao banco
psql -U postgres -d quintou

# Criar banco
createdb quintou

# Deletar banco
dropdb quintou

# Dump do banco
pg_dump quintou > backup.sql

# Restaurar backup
psql quintou < backup.sql

# Ver todas as tabelas
\dt

# Descrever tabela
\d users

# Sair
\q
```

### Alembic (Migrações)

```bash
# Ver status atual
alembic current

# Ver histórico
alembic history

# Criar nova migração (auto)
alembic revision --autogenerate -m "descrição"

# Criar migração (manual)
alembic revision -m "descrição"

# Aplicar todas as migrações
alembic upgrade head

# Aplicar uma migração
alembic upgrade +1

# Reverter última migração
alembic downgrade -1

# Reverter para revisão específica
alembic downgrade 99e2d648c27b

# Ver SQL sem aplicar
alembic upgrade head --sql
```

---

## 🧪 TESTES

### Verificação de Correções

```bash
# Script automatizado
python verify_fixes.py

# Com output colorido
python verify_fixes.py | more
```

### Testes Manuais

```bash
# Health check
curl http://localhost:8000/health

# Registrar usuário
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@quintou.com",
    "password": "Test123!",
    "full_name": "Test User",
    "cpf": "12345678900",
    "phone": "11999999999"
  }'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@quintou.com",
    "password": "Test123!"
  }'

# Esquecer senha
curl -X POST http://localhost:8000/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@quintou.com"}'

# Endpoint autenticado
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN"
```

### Pytest

```bash
# Rodar todos os testes
pytest

# Com coverage
pytest --cov=app

# Teste específico
pytest tests/test_auth.py

# Com output detalhado
pytest -v

# Parar no primeiro erro
pytest -x
```

---

## 💳 STRIPE

### Stripe CLI

```bash
# Instalar
# Windows: scoop install stripe
# Mac: brew install stripe/stripe-cli/stripe
# Linux: https://stripe.com/docs/stripe-cli

# Login
stripe login

# Escutar webhooks localmente
stripe listen --forward-to localhost:8000/payments/webhook

# Trigger eventos manualmente
stripe trigger checkout.session.completed
stripe trigger payment_intent.succeeded
stripe trigger account.updated

# Ver logs
stripe logs tail

# Testar API keys
stripe config --list
```

### Testar Pagamentos

```bash
# Criar Payment Intent
curl -X POST http://localhost:8000/payments/create-intent \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"booking_id": "uuid-da-reserva"}'

# Verificar resposta
# client_secret deve começar com "pi_" (não "pi_mocked")
```

---

## 📧 EMAIL

### Testar Envio

```bash
# Via API
curl -X POST http://localhost:8000/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@quintou.com"}'

# Verificar logs
tail -f logs/app.log | grep email

# Modo console
# Email será impresso no terminal onde o servidor está rodando
```

### SendGrid

```bash
# Testar API key
curl -X POST https://api.sendgrid.com/v3/mail/send \
  -H "Authorization: Bearer $SENDGRID_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "personalizations": [{"to": [{"email": "test@example.com"}]}],
    "from": {"email": "noreply@quintou.com"},
    "subject": "Test",
    "content": [{"type": "text/plain", "value": "Test email"}]
  }'
```

---

## 🐳 DOCKER

### Build e Run

```bash
# Build da imagem
docker build -t quintou-backend:latest .

# Build com tag específica
docker build -t quintou-backend:v2.0 .

# Run container
docker run -d -p 8000:8000 --name quintou-api quintou-backend:latest

# Run com .env
docker run -d -p 8000:8000 --env-file .env quintou-backend:latest

# Ver logs
docker logs -f quintou-api

# Entrar no container
docker exec -it quintou-api /bin/bash

# Parar container
docker stop quintou-api

# Remover container
docker rm quintou-api

# Ver imagens
docker images

# Remover imagem
docker rmi quintou-backend:latest
```

### Docker Compose

```bash
# Iniciar todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Logs de um serviço específico
docker-compose logs -f api

# Parar serviços
docker-compose down

# Rebuild e restart
docker-compose up -d --build

# Executar comando em serviço
docker-compose exec api alembic upgrade head

# Ver status
docker-compose ps
```

---

## ☸️ KUBERNETES

### Deployment

```bash
# Apply manifests
kubectl apply -f secrets.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Ver pods
kubectl get pods

# Ver logs
kubectl logs -f deployment/quintou-backend

# Logs de pod específico
kubectl logs -f quintou-backend-xxxxx

# Entrar no pod
kubectl exec -it quintou-backend-xxxxx -- /bin/bash

# Port forward
kubectl port-forward deployment/quintou-backend 8000:8000

# Ver status do deployment
kubectl rollout status deployment/quintou-backend

# Histórico de deploys
kubectl rollout history deployment/quintou-backend

# Rollback
kubectl rollout undo deployment/quintou-backend

# Scale
kubectl scale deployment quintou-backend --replicas=5

# Ver events
kubectl get events --sort-by=.metadata.creationTimestamp
```

---

## 🔍 DEBUGGING

### Logs

```bash
# Ver logs do servidor
tail -f logs/app.log

# Grep por erros
tail -f logs/app.log | grep ERROR

# Grep por endpoint específico
tail -f logs/app.log | grep "/bookings"

# Ver últimas 100 linhas
tail -n 100 logs/app.log

# Seguir logs (Linux)
journalctl -u quintou-backend -f
```

### Database Queries

```sql
-- Ver todos os usuários
SELECT id, email, full_name, is_host FROM users;

-- Ver bookings recentes
SELECT b.id, s.title, u.full_name, b.status, b.total_price
FROM bookings b
JOIN spaces s ON b.space_id = s.id
JOIN users u ON b.guest_id = u.id
ORDER BY b.created_at DESC
LIMIT 10;

-- Ver payments pendentes
SELECT p.id, p.amount, p.status, b.id as booking_id
FROM payments p
JOIN bookings b ON p.booking_id = b.id
WHERE p.status = 'PENDING';

-- Ver rating médio de hosts
SELECT u.id, u.full_name, u.average_rating, u.total_reviews
FROM users u
WHERE u.is_host = true
ORDER BY u.average_rating DESC;

-- Ver tokens de reset expirados
SELECT * FROM password_reset_tokens
WHERE expires_at < NOW() AND used_at IS NULL;

-- Limpar tokens antigos
DELETE FROM password_reset_tokens
WHERE expires_at < NOW() - INTERVAL '7 days';
```

### Python Debug

```python
# Adicionar breakpoint
import pdb; pdb.set_trace()

# ou (Python 3.7+)
breakpoint()

# Print debug
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Variable: {variable}")

# IPython (mais features)
from IPython import embed; embed()
```

---

## 🔐 SEGURANÇA

### Gerar Secret Key

```python
# Python
import secrets
print(secrets.token_urlsafe(64))
```

```bash
# OpenSSL
openssl rand -base64 64
```

### Verificar Senhas

```python
# Python REPL
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash senha
hashed = pwd_context.hash("MinhaSenh@123")
print(hashed)

# Verificar senha
pwd_context.verify("MinhaSenh@123", hashed)  # True
```

### JWT Tokens

```python
# Python REPL
from jose import jwt
from datetime import datetime, timedelta

# Criar token
payload = {
    "sub": "user_id",
    "exp": datetime.utcnow() + timedelta(minutes=30)
}
token = jwt.encode(payload, "secret_key", algorithm="HS256")

# Decodificar token
decoded = jwt.decode(token, "secret_key", algorithms=["HS256"])
print(decoded)
```

---

## 📊 MONITORAMENTO

### Performance

```bash
# Ver uso de recursos
docker stats

# Ver uso de CPU/memória do container
docker stats quintou-api

# Ver processos Python
ps aux | grep python

# htop (se disponível)
htop

# Ver conexões de rede
netstat -an | grep 8000
```

### Health Checks

```bash
# Simples
curl http://localhost:8000/health

# Com timeout
curl --max-time 5 http://localhost:8000/health

# Loop contínuo
while true; do
  curl -s http://localhost:8000/health | jq
  sleep 5
done

# Verificar se está UP
curl -f http://localhost:8000/health || echo "Service DOWN"
```

---

## 🔄 GIT

### Workflow Comum

```bash
# Ver status
git status

# Ver diff
git diff

# Adicionar arquivos
git add .
git add app/services/payment_service.py

# Commit
git commit -m "fix: corrige integração Stripe PaymentIntent"

# Push
git push origin main

# Pull
git pull origin main

# Criar branch
git checkout -b feature/nova-funcionalidade

# Trocar de branch
git checkout main

# Merge branch
git merge feature/nova-funcionalidade

# Ver log
git log --oneline

# Desfazer commit (mantém mudanças)
git reset --soft HEAD~1

# Desfazer mudanças não commitadas
git checkout -- .
```

---

## 🧹 MANUTENÇÃO

### Limpeza

```bash
# Limpar __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} +

# Limpar .pyc
find . -type f -name "*.pyc" -delete

# Limpar logs antigos
find logs/ -type f -mtime +30 -delete

# Limpar Docker
docker system prune -a
```

### Backup

```bash
# Backup do banco
pg_dump quintou > backup_$(date +%Y%m%d).sql

# Backup com gzip
pg_dump quintou | gzip > backup_$(date +%Y%m%d).sql.gz

# Backup de arquivos
tar -czf backup_$(date +%Y%m%d).tar.gz app/ alembic/ .env

# Upload para S3
aws s3 cp backup.sql.gz s3://quintou-backups/
```

---

## 📦 DEPENDÊNCIAS

### pip

```bash
# Instalar pacote
pip install nome-do-pacote

# Instalar versão específica
pip install nome-do-pacote==1.2.3

# Atualizar pacote
pip install --upgrade nome-do-pacote

# Desinstalar
pip uninstall nome-do-pacote

# Listar instalados
pip list

# Listar desatualizados
pip list --outdated

# Atualizar requirements.txt
pip freeze > requirements.txt

# Instalar do requirements.txt
pip install -r requirements.txt
```

---

## 🎯 PRODUÇÃO

### Deploy

```bash
# Pull última versão
git pull origin main

# Atualizar dependências
pip install -r requirements.txt

# Aplicar migrações
alembic upgrade head

# Restart serviço (systemd)
sudo systemctl restart quintou-backend

# Restart Docker
docker-compose restart api

# Restart Kubernetes
kubectl rollout restart deployment/quintou-backend

# Verificar health
curl https://api.quintou.com/health
```

### Rollback

```bash
# Git
git checkout main
git reset --hard HEAD~1
git push origin main --force

# Docker
docker pull quintou-backend:v1.9
docker tag quintou-backend:v1.9 quintou-backend:latest
docker-compose up -d

# Kubernetes
kubectl rollout undo deployment/quintou-backend

# Alembic
alembic downgrade -1
```

---

## 💡 DICAS

### Atalhos Úteis

```bash
# Alias para .bashrc ou .zshrc
alias qstart="uvicorn app.main:app --reload"
alias qtest="pytest -v"
alias qlogs="tail -f logs/app.log"
alias qdb="psql -U postgres -d quintou"
alias qmigrate="alembic upgrade head"
```

### Variáveis de Ambiente

```bash
# Carregar .env (bash)
export $(cat .env | xargs)

# Verificar variável
echo $DATABASE_URL
echo $STRIPE_SECRET_KEY

# Usar .env com comando
env $(cat .env | xargs) uvicorn app.main:app
```

---

**Última atualização:** 13/07/2026  
**Mantenha este arquivo atualizado com novos comandos úteis!**
