import json
from typing import Dict, Any

# Estrutura super simples de i18n
# Para um app mais complexo, pode-se usar Babel ou gettext
_translations: Dict[str, Dict[str, str]] = {
    "pt-BR": {
        "user_not_found": "Usuário não encontrado.",
        "space_not_found": "Espaço não encontrado.",
        "invalid_credentials": "Email ou senha incorretos.",
        "email_already_exists": "Email já cadastrado.",
        "cpf_already_exists": "CPF já cadastrado.",
        "phone_already_exists": "Telefone já cadastrado.",
        "booking_conflict": "O espaço já está reservado nesse horário.",
        "invalid_booking_status": "Status de reserva inválido para esta ação."
    },
    "en-US": {
        "user_not_found": "User not found.",
        "space_not_found": "Space not found.",
        "invalid_credentials": "Incorrect email or password.",
        "email_already_exists": "Email already registered.",
        "cpf_already_exists": "CPF already registered.",
        "phone_already_exists": "Phone already registered.",
        "booking_conflict": "The space is already booked for this time.",
        "invalid_booking_status": "Invalid booking status for this action."
    }
}

def _(key: str, locale: str = "pt-BR") -> str:
    """Retorna a tradução baseada na chave e locale."""
    lang = _translations.get(locale, _translations["pt-BR"])
    return lang.get(key, key)
