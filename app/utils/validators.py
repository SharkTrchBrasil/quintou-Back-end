"""
Validadores customizados para o sistema
"""
import re
from typing import Optional


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Valida a força da senha.
    
    Requisitos:
    - Mínimo 8 caracteres
    - Pelo menos uma letra maiúscula
    - Pelo menos uma letra minúscula
    - Pelo menos um número
    - Pelo menos um caractere especial
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Senha deve ter no mínimo 8 caracteres"
    
    if not re.search(r'[A-Z]', password):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    
    if not re.search(r'[a-z]', password):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    
    if not re.search(r'\d', password):
        return False, "Senha deve conter pelo menos um número"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Senha deve conter pelo menos um caractere especial"
    
    return True, None


def validate_cpf(cpf: str) -> tuple[bool, Optional[str]]:
    """
    Valida CPF usando algoritmo de dígitos verificadores.
    
    Args:
        cpf: CPF sem formatação (apenas números)
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Remove caracteres não numéricos
    cpf = ''.join(filter(str.isdigit, cpf))
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False, "CPF deve conter 11 dígitos"
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False, "CPF inválido"
    
    # Calcula primeiro dígito verificador
    sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit1 = 11 - (sum1 % 11)
    if digit1 >= 10:
        digit1 = 0
    
    if int(cpf[9]) != digit1:
        return False, "CPF inválido"
    
    # Calcula segundo dígito verificador
    sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit2 = 11 - (sum2 % 11)
    if digit2 >= 10:
        digit2 = 0
    
    if int(cpf[10]) != digit2:
        return False, "CPF inválido"
    
    return True, None


def validate_phone_br(phone: str) -> tuple[bool, Optional[str]]:
    """
    Valida telefone brasileiro.
    
    Formatos aceitos:
    - (11) 98765-4321
    - 11987654321
    - +5511987654321
    
    Args:
        phone: Telefone
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Remove caracteres não numéricos
    phone_clean = ''.join(filter(str.isdigit, phone))
    
    # Remove código do país se presente
    if phone_clean.startswith('55'):
        phone_clean = phone_clean[2:]
    
    # Celular: 11 dígitos (DDD + 9 + 8 dígitos)
    # Fixo: 10 dígitos (DDD + 8 dígitos)
    if len(phone_clean) not in [10, 11]:
        return False, "Telefone deve ter 10 ou 11 dígitos (com DDD)"
    
    # Valida DDD (11 a 99)
    ddd = int(phone_clean[:2])
    if ddd < 11 or ddd > 99:
        return False, "DDD inválido"
    
    # Valida celular (deve começar com 9)
    if len(phone_clean) == 11 and phone_clean[2] != '9':
        return False, "Celular deve começar com 9 após o DDD"
    
    return True, None


def sanitize_cpf(cpf: str) -> str:
    """Remove formatação do CPF"""
    return ''.join(filter(str.isdigit, cpf))


def sanitize_phone(phone: str) -> str:
    """Remove formatação do telefone"""
    phone_clean = ''.join(filter(str.isdigit, phone))
    # Remove código do país se presente
    if phone_clean.startswith('55'):
        phone_clean = phone_clean[2:]
    return phone_clean
