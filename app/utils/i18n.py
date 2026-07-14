"""
Internationalization utilities
Sistema simples de tradução para mensagens de erro
"""

# Dicionário de traduções PT-BR
TRANSLATIONS = {
    "space_not_found": "Espaço não encontrado",
    "booking_not_found": "Reserva não encontrada",
    "email_already_exists": "Email já cadastrado no sistema",
    "invalid_credentials": "Email ou senha incorretos",
    "user_not_found": "Usuário não encontrado",
    "unauthorized": "Não autorizado",
    "forbidden": "Acesso negado",
    "payment_failed": "Falha no processamento do pagamento",
    "booking_conflict": "Conflito de horário. Este espaço já está reservado para o horário solicitado",
    "invalid_token": "Token inválido ou expirado",
    "space_not_available": "Espaço não disponível para o período solicitado",
    "insufficient_balance": "Saldo insuficiente",
    "invalid_date": "Data inválida",
    "invalid_time": "Horário inválido",
    "past_date_not_allowed": "Não é possível fazer reservas para datas passadas",
    "max_guests_exceeded": "Número de convidados excede o limite do espaço",
    "min_hours_not_met": "Reserva não atende o mínimo de horas exigido",
    "max_hours_exceeded": "Reserva excede o máximo de horas permitido",
}


def _(key: str) -> str:
    """
    Função de tradução simples.
    
    Args:
        key: Chave da tradução
    
    Returns:
        Texto traduzido ou a própria chave se não encontrar
    """
    return TRANSLATIONS.get(key, key)


def add_translation(key: str, value: str):
    """
    Adiciona uma nova tradução dinamicamente.
    
    Args:
        key: Chave da tradução
        value: Texto traduzido
    """
    TRANSLATIONS[key] = value


def get_translation(key: str, default: str = None) -> str:
    """
    Obtém uma tradução com fallback.
    
    Args:
        key: Chave da tradução
        default: Valor padrão se não encontrar
    
    Returns:
        Texto traduzido ou default
    """
    return TRANSLATIONS.get(key, default or key)
