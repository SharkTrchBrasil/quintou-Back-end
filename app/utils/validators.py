import re
from typing import Optional

def validate_cpf(cpf: str) -> bool:
    """Valida um CPF brasileiro."""
    cpf = re.sub(r'[^0-9]', '', str(cpf))
    
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
        
    for i in range(9, 11):
        value = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != int(cpf[i]):
            return False
            
    return True

def validate_phone(phone: str) -> bool:
    """Valida um número de telefone brasileiro no formato +55 11 99999-9999."""
    pattern = re.compile(r'^\+55\s?(?:\(?[1-9]{2}\)?\s?)?(?:9\d{4}|\d{4})[-\s]?\d{4}$')
    return bool(pattern.match(phone))

def validate_cep(cep: str) -> bool:
    """Valida um CEP brasileiro."""
    pattern = re.compile(r'^\d{5}-?\d{3}$')
    return bool(pattern.match(cep))
