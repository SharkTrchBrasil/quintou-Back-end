import stripe
from app.config import settings
from app.constants import PLATFORM_GUEST_FEE_PERCENTAGE, PLATFORM_HOST_FEE_PERCENTAGE

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_connect_account(email: str, first_name: str, last_name: str, cpf: str) -> str:
    """
    Cria uma conta conectada na Stripe (tipo Express) para o anfitrião.
    """
    account = stripe.Account.create(
        type="express",
        country="BR",
        email=email,
        business_type="individual",
        individual={
            "first_name": first_name,
            "last_name": last_name,
            "id_number": cpf,
        },
        capabilities={
            "transfers": {"requested": True},
        },
    )
    return account.id

def generate_onboarding_link(account_id: str, return_url: str, refresh_url: str) -> str:
    """
    Gera o link temporário para a tela hospedada pela Stripe (Onboarding KYC).
    """
    account_link = stripe.AccountLink.create(
        account=account_id,
        refresh_url=refresh_url,
        return_url=return_url,
        type="account_onboarding",
    )
    return account_link.url

def check_onboarding_status(account_id: str) -> bool:
    """
    Verifica se o anfitrião já terminou de preencher todos os dados exigidos.
    """
    account = stripe.Account.retrieve(account_id)
    if len(account.requirements.currently_due) == 0:
        return True
    return False

def create_stripe_customer(email: str, name: str) -> str:
    """
    Creates a customer on Stripe for the guest.
    """
    customer = stripe.Customer.create(
        email=email,
        name=name
    )
    return customer.id

def create_booking_checkout_session(
    customer_id: str, 
    base_amount: float, 
    currency: str, 
    booking_id: str,
    host_account_id: str,
    success_url: str, 
    cancel_url: str
) -> str:
    """
    Creates a Stripe Checkout session to pay for a space booking.
    Usa "Destination Charges" (transfer_data) para transferir o valor para o anfitrião
    já descontando a taxa da plataforma (application_fee_amount).
    """
    
    # Hóspede paga = Valor Base + 10%
    total_charged_to_guest = base_amount * (1 + float(PLATFORM_GUEST_FEE_PERCENTAGE))
    
    # Anfitrião recebe = Valor Base - 15%
    host_earnings = base_amount * (1 - float(PLATFORM_HOST_FEE_PERCENTAGE))
    
    # A plataforma (Quintou) retém a diferença entre o que o hóspede pagou e o que o anfitrião recebeu.
    # Ex: Base 100 -> Hóspede paga 110. Anfitrião recebe 85. Quintou retém 25.
    application_fee = total_charged_to_guest - host_earnings
    
    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': currency,
                'product_data': {
                    'name': f'Reserva de Espaço - {booking_id}',
                    'description': 'Valor da reserva + taxa de serviço',
                },
                'unit_amount': int(total_charged_to_guest * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        payment_intent_data={
            'application_fee_amount': int(application_fee * 100),
            'transfer_data': {
                'destination': host_account_id,
            },
        },
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            'booking_id': booking_id,
            'base_amount': str(base_amount),
            'host_earnings': str(host_earnings),
            'application_fee': str(application_fee),
        }
    )
    return session.url
