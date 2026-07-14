# 💳 Fluxo Completo de Pagamento - Quintou

## 📱 Fluxo do App Mobile/Frontend

### 1️⃣ Usuário Visualiza Espaço
```
GET /spaces/{space_id}
```
**Response**:
```json
{
  "id": "uuid",
  "title": "Piscina Linda",
  "price": 100.00,
  "pricing_mode": "PER_HOUR",
  "max_guests": 20,
  "min_hours": 2,
  "max_hours": 8,
  "security_deposit": 500.00,
  "addons": [
    {
      "id": "uuid",
      "name": "Churrasqueira",
      "price": 50.00,
      "pricing_type": "FLAT"
    }
  ]
}
```

---

### 2️⃣ Usuário Seleciona Data, Horário e Addons

**UI deve coletar**:
- Data (date)
- Horário início (start_time)
- Horário fim (end_time)
- Número de convidados (num_guests, num_adults, num_children, num_infants, num_pets)
- Addons selecionados (opcional)
- Endereço de entrega (se for EQUIPMENT com delivery)
- Mensagem para o host (opcional)

---

### 3️⃣ App Cria o Booking
```http
POST /bookings
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "space_id": "uuid-do-espaço",
  "date": "2026-08-15",
  "start_time": "14:00:00",
  "end_time": "20:00:00",
  "num_guests": 15,
  "num_adults": 10,
  "num_children": 5,
  "num_infants": 0,
  "num_pets": 0,
  "guest_message": "Festa de aniversário!",
  "event_type": "Birthday Party",
  "selected_addons": [
    {
      "addon_id": "uuid-do-addon",
      "quantity": 1
    }
  ],
  "delivery_address": "Rua Exemplo, 123" // apenas se necessário
}
```

**Response** (Status 201):
```json
{
  "id": "booking-uuid",
  "space_id": "uuid",
  "guest_id": "uuid",
  "date": "2026-08-15",
  "start_time": "14:00:00",
  "end_time": "20:00:00",
  "total_hours": 6,
  "num_guests": 15,
  "subtotal": 600.00,
  "addons_total": 50.00,
  "delivery_fee": 0.00,
  "service_fee": 65.00,      // 10% taxa do guest
  "host_fee": 97.50,         // 15% taxa do host
  "total_price": 715.00,     // O QUE O GUEST PAGA
  "host_payout": 552.50,     // O QUE O HOST RECEBE
  "deposit_amount": 500.00,
  "deposit_status": "HELD",
  "status": "PENDING",       // Aguardando pagamento
  "created_at": "2026-07-13T..."
}
```

**⚠️ IMPORTANTE**: Neste ponto, o booking foi criado mas **NÃO ESTÁ CONFIRMADO** até o pagamento.

---

### 4️⃣ App Inicia Pagamento

```http
POST /payments/create-intent
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "booking_id": "booking-uuid"
}
```

**Response** (Status 200):
```json
{
  "client_secret": "pi_xxx_secret_yyy",
  "payment_id": "payment-uuid",
  "amount": 715.00,
  "currency": "brl"
}
```

**O que acontece nos bastidores**:
1. ✅ Valida que booking existe e pertence ao usuário
2. ✅ Valida que host tem Stripe account configurada
3. ✅ Cria `PaymentIntent` no Stripe com:
   - Valor total: R$ 715,00 (convertido para centavos: 71500)
   - Application fee: R$ 162,50 (taxa da plataforma)
   - Destination: `stripe_account_id` do host
4. ✅ Salva `Payment` no banco com status `PENDING`
5. ✅ Retorna `client_secret` para o app

---

### 5️⃣ App Confirma Pagamento (Frontend)

**Opção A: Stripe Elements (Recomendado para web)**
```javascript
import { loadStripe } from '@stripe/stripe-js';

const stripe = await loadStripe('pk_test_...');

const { error } = await stripe.confirmPayment({
  elements, // Stripe Elements com cartão
  confirmParams: {
    return_url: 'quintou://payment-success',
  },
});
```

**Opção B: React Native Stripe SDK (Recomendado para mobile)**
```javascript
import { useStripe } from '@stripe/stripe-react-native';

const { confirmPayment } = useStripe();

const { error } = await confirmPayment(clientSecret, {
  paymentMethodType: 'Card',
  paymentMethodData: {
    billingDetails: {
      name: 'Nome do Cliente',
    },
  },
});

if (error) {
  Alert.alert('Erro', error.message);
} else {
  // Pagamento confirmado!
  navigation.navigate('BookingConfirmed', { bookingId });
}
```

---

### 6️⃣ Stripe Processa Pagamento

**O que acontece automaticamente**:

1. ✅ **Stripe valida cartão** e processa pagamento
2. ✅ **Stripe retém taxa da plataforma** (R$ 162,50)
3. ✅ **Stripe transfere para host** (R$ 552,50) - já descontada a taxa de 15%
4. ✅ **Stripe envia webhook** para `/payments/webhook`

---

### 7️⃣ Backend Recebe Webhook do Stripe

```http
POST /payments/webhook
Stripe-Signature: xxx

{
  "type": "payment_intent.succeeded",
  "data": {
    "object": {
      "id": "pi_xxx",
      "amount": 71500,
      "metadata": {
        "booking_id": "uuid"
      }
    }
  }
}
```

**O que o backend faz**:
1. ✅ Valida assinatura do webhook
2. ✅ Busca `Booking` pelo ID
3. ✅ Atualiza `Booking.status` para `CONFIRMED`
4. ✅ Atualiza `Payment.status` para `COMPLETED`
5. ✅ Salva `Payment.paid_at` com timestamp
6. ✅ Envia notificação push para **Guest**: "Reserva confirmada!"
7. ✅ Envia notificação push para **Host**: "Nova reserva recebida!"
8. ✅ Envia email de confirmação para ambos

---

### 8️⃣ App Mostra Confirmação

**GET /bookings/{booking_id}**
```json
{
  "id": "booking-uuid",
  "status": "CONFIRMED",  // ✅ Pagamento confirmado!
  "total_price": 715.00,
  "space": {
    "title": "Piscina Linda",
    "address": "..."
  },
  "created_at": "..."
}
```

**Telas que o app deve mostrar**:
- ✅ Confirmação de reserva
- ✅ QR Code ou código de acesso
- ✅ Detalhes do espaço
- ✅ Botão para chat com host
- ✅ Opção de cancelar (com política de reembolso)

---

## 🔄 Fluxos Alternativos

### Host Requer Aprovação (`requires_approval: true`)

1. Booking criado com status `PENDING`
2. **Pagamento NÃO é processado ainda**
3. Host recebe notificação: "Nova solicitação de reserva"
4. Host aprova: `PUT /bookings/{id}/confirm`
5. Aí sim o app inicia pagamento (passo 4 acima)

### Cancelamento pelo Guest

```http
PUT /bookings/{booking_id}/cancel
Authorization: Bearer {access_token}

{
  "reason": "Mudança de planos"
}
```

**O que acontece**:
1. ✅ Booking.status → `CANCELLED_BY_GUEST`
2. ✅ Se já pago, processa **reembolso** via Stripe
3. ✅ Payment.status → `REFUNDED`
4. ✅ Notifica host

### Cancelamento pelo Host

```http
PUT /bookings/{booking_id}/reject
Authorization: Bearer {access_token}
```

**O que acontece**:
1. ✅ Booking.status → `CANCELLED_BY_HOST`
2. ✅ **Reembolso 100%** para guest
3. ✅ Notifica guest

---

## 💰 Split de Valores

### Exemplo: Reserva de R$ 650,00

```
Valor base do espaço:        R$ 600,00  (6 horas × R$ 100/hr)
Addons:                      R$  50,00  (Churrasqueira)
───────────────────────────────────────
Subtotal:                    R$ 650,00

Taxa do Guest (10%):         R$  65,00  ← Guest paga
Taxa do Host (15%):          R$  97,50  ← Descontado do host
───────────────────────────────────────
Total que Guest paga:        R$ 715,00  ✅
Total que Host recebe:       R$ 552,50  ✅
Total que Plataforma fica:   R$ 162,50  (R$ 65 + R$ 97,50)
```

**No Stripe Connect**:
```javascript
stripe.PaymentIntent.create({
  amount: 71500,                    // R$ 715,00 em centavos
  currency: 'brl',
  application_fee_amount: 16250,    // R$ 162,50 em centavos
  transfer_data: {
    destination: host_stripe_account_id,  // Host recebe R$ 552,50
  }
})
```

---

## 🔐 Segurança

### Validações Implementadas

✅ Usuário autenticado (JWT token)  
✅ Booking pertence ao usuário  
✅ Host tem Stripe account configurada  
✅ Espaço está ativo e aprovado  
✅ Horário disponível (race condition protegida)  
✅ Data não é no passado  
✅ Número de convidados dentro do limite  
✅ Horas dentro do min/max  
✅ Webhook com assinatura validada  
✅ Valores calculados no backend (nunca confiar no frontend)  

---

## 🧪 Testando o Fluxo

### 1. Crie usuário e faça login
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "guest@test.com",
    "password": "Test@123456",
    "full_name": "Guest Test",
    "phone": "11987654321"
  }'
```

### 2. Crie um booking
```bash
curl -X POST http://localhost:8000/bookings \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "space_id": "uuid",
    "date": "2026-08-15",
    "start_time": "14:00:00",
    "end_time": "20:00:00",
    "num_guests": 10,
    "num_adults": 10,
    "num_children": 0,
    "num_infants": 0,
    "num_pets": 0
  }'
```

### 3. Crie payment intent
```bash
curl -X POST http://localhost:8000/payments/create-intent \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "booking_id": "booking-uuid"
  }'
```

### 4. Use Stripe Test Cards

**Sucesso**:
- Número: `4242 4242 4242 4242`
- Validade: Qualquer data futura
- CVC: Qualquer 3 dígitos

**Falha**:
- Número: `4000 0000 0000 0002` (cartão recusado)

---

## 📊 Estados do Booking

| Status | Descrição | Ação do App |
|--------|-----------|-------------|
| `PENDING` | Aguardando pagamento ou aprovação | Mostrar "Aguardando pagamento" |
| `CONFIRMED` | Pago e confirmado | Mostrar QR Code e detalhes |
| `CANCELLED_BY_GUEST` | Guest cancelou | Mostrar "Cancelado - Reembolsado" |
| `CANCELLED_BY_HOST` | Host cancelou | Mostrar "Cancelado pelo anfitrião" |
| `COMPLETED` | Já aconteceu | Permitir avaliação |
| `DISPUTED` | Em disputa | Mostrar "Em análise" |

---

## ❓ FAQ

**Q: O pagamento é processado imediatamente?**  
A: Sim, quando o guest confirma no Stripe.

**Q: O host recebe imediatamente?**  
A: Não. O Stripe retém por 7 dias (padrão) ou após o evento (configur
ável).

**Q: E se o cartão for recusado?**  
A: O booking permanece `PENDING` e o app deve mostrar erro e permitir tentar novamente.

**Q: Como funciona o reembolso?**  
A: Automático via Stripe quando host ou guest cancela. Valor volta para o cartão original em 5-10 dias.

**Q: E o depósito de segurança?**  
A: Ainda não implementado. Requer lógica adicional para "hold" e "capture" separados.

---

## 🚀 Próximas Melhorias

1. **Implementar Depósito de Segurança** (hold separado)
2. **Apple Pay / Google Pay**
3. **Parcelamento** (via Stripe installments)
4. **Pix** como método de pagamento
5. **Boleto** para quem não tem cartão
6. **Wallet** interna (saldo em conta)

---

**Status**: ✅ **FUNCIONAL E PRONTO PARA USO**

**Última atualização**: 13/07/2026
