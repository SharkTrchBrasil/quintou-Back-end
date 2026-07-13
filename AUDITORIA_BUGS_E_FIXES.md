# 🔍 AUDITORIA COMPLETA - QUINTOU BACKEND

**Data:** 13 de Julho de 2026  
**Versão:** 1.0  
**Status:** ⚠️ CRÍTICO - Requer correções imediatas antes de produção

---

## 📋 SUMÁRIO EXECUTIVO

O **Quintou** é uma plataforma marketplace de aluguel de espaços e equipamentos por hora/dia, similar ao Airbnb mas focada em reservas de curto prazo (piscinas, churrasqueiras, salões de festa, equipamentos, etc.). A arquitetura está bem estruturada usando FastAPI + SQLAlchemy Async + PostgreSQL, mas possui **problemas críticos que impedem o uso em produção**.

### ⚠️ PROBLEMAS CRÍTICOS IDENTIFICADOS

| # | Problema | Severidade | Impacto | Status |
|---|----------|-----------|---------|--------|
| 1 | Sistema de pagamento totalmente MOCKADO | 🔴 CRÍTICO | Nenhum pagamento real é processado | ❌ |
| 2 | Reset de senha não implementado | 🔴 CRÍTICO | Usuários não podem recuperar acesso | ❌ |
| 3 | CPF e Telefone não validados (duplicação) | 🟠 ALTO | Múltiplas contas com mesmo CPF/telefone | ❌ |
| 4 | Rating médio não calculado após reviews | 🟠 ALTO | Ratings sempre zerados | ❌ |
| 5 | Webhook do Stripe não atualiza bookings | 🟠 ALTO | Status de pagamento dessincroni

zado | ❌ |
| 6 | Cálculo de taxa inconsistente | 🟡 MÉDIO | Guest: 15%, Host: 10% vs código: Guest: 10%, Host: 15% | ❌ |
| 7 | Falta integração de email | 🟡 MÉDIO | Sem notificações por email | ❌ |
| 8 | FCM opcional sem fallback | 🟡 MÉDIO | Notificações push podem falhar silenciosamente | ❌ |
| 9 | Mapbox geocoding opcional | 🟢 BAIXO | Busca por localização pode falhar | ❌ |
| 10 | Migrações desatualizadas | 🟢 BAIXO | Schema do BD não reflete modelos | ❌ |

---

## 🔴 PROBLEMA #1: SISTEMA DE PAGAMENTO MOCKADO (CRÍTICO)

### Localização
- **Arquivo:** `app/services/payment_service.py`
- **Linhas:** 18-49

### Descrição
O sistema de pagamentos está **completamente mockado**. Nenhuma integração real com o Stripe PaymentIntent está funcionando.

### Código Atual (MOCKADO)
```python
# payment_service.py - LINHA 30-47
# payment_intent = stripe.PaymentIntent.create(
#     amount=amount_cents,
#     currency="brl",
#     # Em Split payment (Connect):
#     # transfer_data={"destination": host.stripe_account_id},
#     # application_fee_amount=int(booking.service_fee * 100) + int(booking.host_fee * 100),
#     metadata={"booking_id": str(booking.id)}
# )

# Mock de resposta
client_secret = "pi_mocked_secret"

# Registra no BD
db_payment = Payment(
    booking_id=booking.id,
    payer_id=payer_id,
    amount=booking.total_price,
    platform_fee=booking.service_fee + booking.host_fee,
    host_amount=booking.host_payout,
    status=PaymentStatus.PENDING,
    stripe_payment_intent_id="pi_mocked"  # ❌ FAKE ID
)
```

### Impacto
- ❌ Nenhum pagamento real é processado
- ❌ Client secret falso retornado ao frontend
- ❌ Payment Intent ID fake salvo no banco
- ❌ Stripe nunca recebe as transações
- ❌ Hosts não recebem pagamentos

### Solução Necessária
✅ Implementar integração real usando `stripe.PaymentIntent.create()` com:
- Destination Charges (Stripe Connect)
- Split payment para host
- Application fee para plataforma
- Metadata com booking_id

---

## 🔴 PROBLEMA #2: RESET DE SENHA NÃO IMPLEMENTADO (CRÍTICO)

### Localização
- **Arquivo:** `app/services/auth_service.py`
- **Linhas:** 97-110

### Descrição
Endpoints de esqueci senha/resetar senha existem mas **não fazem nada**.

### Código Atual
```python
async def forgot_password(self, forgot_in: ForgotPasswordRequest):
    user = await self.get_user_by_email(forgot_in.email)
    if not user:
        # Avoid user enumeration by returning generic success
        return {"message": "If an account exists, a reset link was sent."}
        
    # TODO: Generate reset token and send email  ❌ NÃO IMPLEMENTADO
    return {"message": "If an account exists, a reset link was sent."}

async def reset_password(self, reset_in: ResetPasswordRequest):
    # TODO: Validate reset token, get user, update password  ❌ NÃO IMPLEMENTADO
    # This is a stub since we don't have email/token sending implemented yet
    raise HTTPException(status_code=501, detail="Not implemented")
```

### Impacto
- ❌ Usuários não conseguem recuperar senhas esquecidas
- ❌ Suporte precisa resetar manualmente no banco
- ❌ Má experiência do usuário

### Solução Necessária
✅ Implementar sistema completo:
1. Gerar token de reset (JWT ou UUID com expiração)
2. Salvar token no banco (tabela `password_reset_tokens`)
3. Enviar email com link de reset
4. Validar token no endpoint de reset
5. Atualizar senha hasheada

---

## 🟠 PROBLEMA #3: CPF E TELEFONE NÃO VALIDADOS (ALTO)

### Localização
- **Arquivo:** `app/services/auth_service.py`
- **Linha:** 29

### Descrição
Existe um comentário TODO mas a validação de unicidade **não está implementada**.

### Código Atual
```python
async def register(self, user_in: UserCreate) -> User:
    # Verifica se já existe
    existing = await self.get_user_by_email(user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_("email_already_exists")
        )
        
    # TODO: Adicionar verificação de CPF e Telefone únicos aqui  ❌
```

### Impacto
- ❌ Múltiplos usuários podem usar mesmo CPF
- ❌ Múltiplos usuários podem usar mesmo telefone
- ❌ Fraudes e contas duplicadas
- ❌ Problemas com KYC e validação da Receita Federal

### Solução Necessária
✅ Adicionar validações:
```python
if user_in.cpf:
    existing_cpf = await self.db.execute(
        select(User).where(User.cpf == user_in.cpf)
    )
    if existing_cpf.scalars().first():
        raise HTTPException(400, detail="CPF já cadastrado")

if user_in.phone:
    existing_phone = await self.db.execute(
        select(User).where(User.phone == user_in.phone)
    )
    if existing_phone.scalars().first():
        raise HTTPException(400, detail="Telefone já cadastrado")
```

---

## 🟠 PROBLEMA #4: RATING MÉDIO NÃO CALCULADO (ALTO)

### Localização
- **Arquivo:** `app/services/review_service.py`
- **Linha:** 66

### Descrição
Após criar uma review, o sistema **não atualiza** o `average_rating` e `total_reviews` do usuário/espaço.

### Código Atual
```python
self.db.add(db_review)
await self.db.commit()
await self.db.refresh(db_review)

# TODO: Atualizar average_rating assincronamente (em background task)  ❌

return db_review
```

### Impacto
- ❌ `User.average_rating` sempre fica 0.0
- ❌ `User.total_reviews` sempre fica 0
- ❌ `Space.average_rating` não existe mas seria necessário
- ❌ Sistema de reputação não funciona
- ❌ Ordenação por rating quebrada

### Solução Necessária
✅ Após criar review, calcular e atualizar:
```python
# Para reviews de Guest -> Host (avalia anfitrião)
if review_type == ReviewType.GUEST_TO_HOST:
    host = await self.db.get(User, reviewee_id)
    reviews_count = await self.db.execute(
        select(func.count(Review.id), func.avg(Review.rating))
        .where(Review.reviewee_id == reviewee_id, Review.type == ReviewType.GUEST_TO_HOST)
    )
    count, avg = reviews_count.first()
    host.total_reviews = count or 0
    host.average_rating = float(avg or 0.0)
    
# Para reviews de Host -> Guest (avalia hóspede)
elif review_type == ReviewType.HOST_TO_GUEST:
    guest = await self.db.get(User, reviewee_id)
    reviews_count = await self.db.execute(
        select(func.count(Review.id), func.avg(Review.rating))
        .where(Review.reviewee_id == reviewee_id, Review.type == ReviewType.HOST_TO_GUEST)
    )
    count, avg = reviews_count.first()
    guest.total_reviews = count or 0
    guest.average_rating = float(avg or 0.0)

await self.db.commit()
```

---

## 🟠 PROBLEMA #5: WEBHOOK STRIPE NÃO ATUALIZA BOOKINGS (ALTO)

### Localização
- **Arquivo:** `app/routers/payments.py`
- **Linhas:** 76-84

### Descrição
O webhook do Stripe recebe o evento `checkout.session.completed` mas **não atualiza o status da reserva**.

### Código Atual
```python
elif event['type'] == 'checkout.session.completed':
    session = event['data']['object']
    booking_id = session.get('metadata', {}).get('booking_id')
    
    # Aqui você buscaria a Booking pelo booking_id e atualizaria o status para PAGO
    # booking = db.query(Booking).filter(Booking.id == booking_id).first()
    # booking.status = 'CONFIRMED'
    # db.commit()
    pass  ❌ NÃO FAZ NADA
```

### Impacto
- ❌ Pagamento completado no Stripe mas booking fica PENDING
- ❌ Host não sabe que foi pago
- ❌ Guest não recebe confirmação
- ❌ Dessincronização entre Stripe e banco de dados

### Solução Necessária
✅ Implementar atualização real:
```python
elif event['type'] == 'checkout.session.completed':
    session = event['data']['object']
    booking_id = session.get('metadata', {}).get('booking_id')
    
    if booking_id:
        booking = await db.get(Booking, UUID(booking_id))
        if booking:
            booking.status = BookingStatus.CONFIRMED
            
            # Atualizar payment
            payment = await db.execute(
                select(Payment).where(Payment.booking_id == booking.id)
            )
            payment_record = payment.scalars().first()
            if payment_record:
                payment_record.status = PaymentStatus.COMPLETED
                payment_record.stripe_payment_intent_id = session.get('payment_intent')
            
            await db.commit()
            
            # Enviar notificações
            await notification_service.create_notification(
                user_id=booking.guest_id,
                type="BOOKING_CONFIRMED",
                title="Pagamento confirmado!",
                body=f"Sua reserva foi confirmada.",
                data={"booking_id": str(booking.id)}
            )
```

---

## 🟡 PROBLEMA #6: INCONSISTÊNCIA NAS TAXAS DA PLATAFORMA (MÉDIO)

### Localização
- **Arquivos:** 
  - `app/services/stripe_service.py` (linhas 8-9)
  - `app/services/booking_service.py` (linha 139-140)

### Descrição
As taxas estão **invertidas** entre os dois arquivos.

### Código Atual

**stripe_service.py:**
```python
HOST_FEE_PERCENTAGE = 0.15  # Anfitrião paga 15%
GUEST_FEE_PERCENTAGE = 0.10  # Hóspede paga 10%
```

**booking_service.py:**
```python
service_fee = (subtotal_after_discount + addons_total) * Decimal('0.15') # 15% taxa do guest ❌
host_fee = (subtotal_after_discount + addons_total) * Decimal('0.10')    # 10% taxa do host ❌
```

### Impacto
- ❌ Cálculos de comissão incorretos
- ❌ Repasse para hosts errado
- ❌ Receita da plataforma inconsistente
- ❌ Possível prejuízo financeiro

### Solução Necessária
✅ Definir as taxas corretas e usar constantes:
```python
# config.py ou constants.py
PLATFORM_GUEST_FEE = Decimal('0.10')  # 10% do guest
PLATFORM_HOST_FEE = Decimal('0.15')   # 15% do host

# booking_service.py
from app.config import PLATFORM_GUEST_FEE, PLATFORM_HOST_FEE

service_fee = (subtotal_after_discount + addons_total) * PLATFORM_GUEST_FEE
host_fee = (subtotal_after_discount + addons_total) * PLATFORM_HOST_FEE
```

---

## 🟡 PROBLEMA #7: FALTA SERVIÇO DE EMAIL (MÉDIO)

### Descrição
Não existe nenhum serviço de envio de emails configurado.

### Impacto
- ❌ Não pode enviar emails de reset de senha
- ❌ Não pode enviar confirmações de booking
- ❌ Não pode enviar recibos
- ❌ Não pode enviar notificações importantes

### Solução Necessária
✅ Implementar EmailService usando:
- **SendGrid** (recomendado para produção)
- **AWS SES** (se já usa AWS)
- **SMTP** (Gmail, Outlook, etc.)

```python
# app/services/email_service.py
import sendgrid
from sendgrid.helpers.mail import Mail
from app.config import settings

class EmailService:
    def __init__(self):
        self.client = sendgrid.SendGridAPIClient(settings.SENDGRID_API_KEY)
    
    async def send_password_reset(self, to_email: str, reset_link: str):
        message = Mail(
            from_email='noreply@quintou.com',
            to_emails=to_email,
            subject='Redefina sua senha - Quintou',
            html_content=f'<a href="{reset_link}">Clique aqui</a>'
        )
        self.client.send(message)
    
    async def send_booking_confirmation(self, to_email: str, booking):
        # Template de confirmação
        pass
```

---

## 🟡 PROBLEMA #8: FCM OPCIONAL SEM FALLBACK (MÉDIO)

### Localização
- **Arquivo:** `app/services/firebase_service.py`

### Descrição
Se as credenciais do Firebase não existirem, o serviço **falha silenciosamente** sem tentar outras formas de notificação.

### Código Atual
```python
def __init__(self):
    try:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        logger.warning(f"Firebase initialization failed: {e}")  ⚠️ Só loga
```

### Impacto
- ❌ Notificações push não chegam
- ❌ Usuário não sabe de bookings/mensagens
- ❌ Experiência degradada

### Solução Necessária
✅ Implementar fallback:
```python
async def send_notification(self, user_id: UUID, notification_data):
    # Tenta FCM primeiro
    if self.fcm_available:
        try:
            return await self._send_fcm(user_id, notification_data)
        except:
            logger.error("FCM failed, trying email fallback")
    
    # Fallback para email
    await email_service.send_notification_email(user_id, notification_data)
```

---

## 🟢 PROBLEMA #9: MAPBOX GEOCODING OPCIONAL (BAIXO)

### Localização
- **Arquivo:** `app/services/space_service.py`
- **Linha:** (geocoding na criação de espaço)

### Descrição
Se a API key do Mapbox não estiver configurada, o geocoding **falha silenciosamente** e as coordenadas ficam `null`.

### Impacto
- ⚠️ Busca por localização não funciona
- ⚠️ Mapa não mostra o espaço
- ⚠️ Cálculo de distância quebrado

### Solução Necessária
✅ Opções:
1. Tornar Mapbox obrigatório (recomendado)
2. Usar Google Geocoding API como fallback
3. Rejeitar criação de espaço sem coordenadas válidas

---

## 🟢 PROBLEMA #10: MIGRAÇÕES DESATUALIZADAS (BAIXO)

### Localização
- **Arquivo:** `alembic/versions/99e2d648c27b_initial_migration.py`

### Descrição
A migração inicial mostra campos antigos que foram modificados nos models.

### Exemplos:
- `User.fcm_token` não está na migração
- `Conversation.last_message_preview` não está na migração
- `Conversation.host_unread_count` / `guest_unread_count` não estão
- `Space.category` mudou de ENUM para `category_id` UUID FK

### Impacto
- ⚠️ Banco de dados pode estar com schema diferente dos models
- ⚠️ Novos campos não existem
- ⚠️ Possíveis erros em runtime

### Solução Necessária
✅ Gerar nova migração:
```bash
alembic revision --autogenerate -m "sync_models_with_db"
alembic upgrade head
```

---

## 📊 ESTATÍSTICAS DA AUDITORIA

### Cobertura de Código Analisada
- ✅ 100% dos models
- ✅ 100% dos services
- ✅ 100% dos routers
- ✅ 100% dos schemas
- ✅ Migrações do Alembic
- ✅ Configuração e dependencies

### Resumo de Problemas
- **🔴 Críticos:** 2 problemas
- **🟠 Altos:** 3 problemas
- **🟡 Médios:** 3 problemas
- **🟢 Baixos:** 2 problemas
- **TOTAL:** 10 problemas identificados

### Tempo Estimado de Correção
- Críticos: ~16 horas
- Altos: ~12 horas
- Médios: ~8 horas
- Baixos: ~4 horas
- **TOTAL:** ~40 horas (1 semana de trabalho)

---

## ✅ PLANO DE AÇÃO RECOMENDADO

### Fase 1: Correções Críticas (Prioridade Máxima)
1. ✅ Implementar integração real com Stripe PaymentIntent
2. ✅ Implementar sistema de reset de senha completo
3. ✅ Adicionar validação de CPF e telefone únicos

### Fase 2: Correções Altas (Antes de Produção)
4. ✅ Implementar cálculo de rating médio
5. ✅ Corrigir webhook do Stripe
6. ✅ Padronizar taxas da plataforma

### Fase 3: Melhorias Médias (Pós-Launch)
7. ✅ Implementar serviço de email
8. ✅ Adicionar fallback de notificações
9. ✅ Tornar Mapbox obrigatório

### Fase 4: Melhorias Baixas (Backlog)
10. ✅ Atualizar migrações do Alembic

---

## 🎯 PRÓXIMOS PASSOS

1. **Revisar e aprovar este documento**
2. **Priorizar correções com equipe de produto**
3. **Implementar correções em ordem de prioridade**
4. **Testar cada correção em ambiente de staging**
5. **Documentar mudanças no changelog**
6. **Deploy gradual em produção**

---

**Documento gerado automaticamente por Kiro AI**  
**Última atualização:** 13/07/2026
