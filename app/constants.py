"""
Constantes globais da aplicação Quintou
"""
from decimal import Decimal

# ========== TAXAS DA PLATAFORMA ==========

# Taxa cobrada do HÓSPEDE (adicionada ao valor total)
# Ex: Reserva de R$100 → Hóspede paga R$110
PLATFORM_GUEST_FEE_PERCENTAGE = Decimal('0.10')  # 10%

# Taxa retida do ANFITRIÃO (descontada do valor que ele recebe)
# Ex: Reserva de R$100 → Anfitrião recebe R$85
PLATFORM_HOST_FEE_PERCENTAGE = Decimal('0.15')  # 15%

# ========== CÁLCULO DE REPASSES ==========
#
# Exemplo completo com base de R$100:
# 
# Hóspede paga:     R$ 100 (base) + R$ 10 (10% taxa) = R$ 110
# Anfitrião recebe: R$ 100 (base) - R$ 15 (15% taxa) = R$ 85
# Plataforma fica:  R$ 110 - R$ 85 = R$ 25
#
# A plataforma retém: 10% + 15% = 25% do valor base
#
# ========== STRIPE CONNECT SPLIT ==========
#
# No Stripe, usamos Destination Charges:
# - amount: R$ 110 (valor total que o hóspede paga)
# - application_fee_amount: R$ 25 (taxa retida pela plataforma)
# - transfer_data.destination: stripe_account_id do anfitrião
# - Resultado: Anfitrião recebe R$ 85 automaticamente
#
# ==========================================

# Outros limites e constantes
MAX_UPLOAD_SIZE_MB = 10  # Para imagens
MAX_VIDEO_SIZE_MB = 100
PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 1
