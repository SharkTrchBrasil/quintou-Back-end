"""
Filtro Anti-Contato para o Chat
===========================================================

Detecta e bloqueia tentativas de compartilhar informações de contato
(telefone, email, WhatsApp, redes sociais, PIX, links) nas mensagens.

Isso garante que todas as negociações passem pela plataforma Quintou.
"""

import re
import logging

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════
# PADRÕES DE DETECÇÃO
# ══════════════════════════════════════════════════════════════════

# Telefones brasileiros em vários formatos
_PHONE_PATTERNS = [
    r'\(?\d{2}\)?\s*9\s*\d{4}[\s\-]?\d{4}',
    r'\+?55\s*\(?\d{2}\)?\s*9?\s*\d{4}[\s\-]?\d{4}',
    r'\b\d{8,13}\b',
    r'\b\d\s+\d\s+\d\s+\d\s+\d\s+\d\s+\d\s+\d',
]

# Emails
_EMAIL_PATTERN = r'[a-zA-Z0-9._%+\-]+\s*[@＠]\s*[a-zA-Z0-9.\-]+\s*\.\s*[a-zA-Z]{2,}'

# WhatsApp keywords
_WHATSAPP_KEYWORDS = [
    r'\bwhatsapp\b', r'\bwhats\s*app\b', r'\bwhats\b', r'\bwpp\b',
    r'\bzap\b', r'\bzapzap\b', r'\bwhatszap\b', r'\bwhatzap\b',
    r'\bchama\s+no\s+zap\b', r'\bmeu\s+whats\b', r'\bmeu\s+zap\b',
    r'\bme\s+chama\s+no\s+whats\b', r'\bchama\s+no\s+whats\b',
    r'\bmanda\s+msg\b', r'\bmanda\s+mensagem\b',
    r'\bno\s+zap\b', r'\bpelo\s+zap\b', r'\bpelo\s+whats\b',
]

# Redes sociais
_SOCIAL_MEDIA_PATTERNS = [
    r'@[a-zA-Z0-9_.]{3,}',
    r'\binstagram\b', r'\binsta\b', r'\big\b(?:\s*:)',
    r'\btelegram\b', r'\btelegran\b',
    r'\bfacebook\b', r'\bface\b(?:\s*:)',
    r'\btiktok\b', r'\btik\s*tok\b',
    r'\btwitter\b', r'\bx\.com\b',
    r'\blinkedin\b',
    r'\bme\s+segue\b', r'\bme\s+chama\s+no\s+insta\b',
    r'\bme\s+chama\s+no\s+telegram\b',
    r'\bme\s+add\b', r'\bme\s+adiciona\b',
    r'\bsigam?\s+no\s+insta\b',
]

# Links/URLs
_URL_PATTERNS = [
    r'https?://',
    r'\bwww\.',
    r'\b[a-zA-Z0-9\-]+\.(com|com\.br|net|org|io|me|app|link|dev|site|online|store)\b',
]

# PIX
_PIX_PATTERNS = [
    r'\bchave\s+pix\b', r'\bmeu\s+pix\b', r'\bpix\s*:', r'\bfaz\s+pix\b',
    r'\bpaga\s+no\s+pix\b', r'\bpix\s+é\b', r'\bpix\s+e\b',
    r'\btransfere\s+pix\b', r'\benvia\s+pix\b',
]

def _build_combined_pattern():
    all_patterns = []
    all_patterns.extend(_PHONE_PATTERNS)
    all_patterns.append(_EMAIL_PATTERN)
    all_patterns.extend(_WHATSAPP_KEYWORDS)
    all_patterns.extend(_SOCIAL_MEDIA_PATTERNS)
    all_patterns.extend(_URL_PATTERNS)
    all_patterns.extend(_PIX_PATTERNS)
    
    combined = '|'.join(f'(?:{p})' for p in all_patterns)
    return re.compile(combined, re.IGNORECASE)

def _build_number_words_pattern():
    word = r'(?:zero|um|uma|dois|duas|tres|três|quatro|cinco|seis|meia|sete|sette|oito|nove)'
    return re.compile(
        rf'{word}[\s,]+{word}[\s,]+{word}[\s,]+{word}',
        re.IGNORECASE
    )

_CONTACT_REGEX = _build_combined_pattern()
_NUMBER_WORDS_REGEX = _build_number_words_pattern()

def contains_contact_info(text: str) -> bool:
    if not text:
        return False
    
    normalized = text.replace('＠', '@').replace('（', '(').replace('）', ')')
    normalized = normalized.replace('．', '.').replace('，', ',')
    
    emoji_numbers = {
        '0️⃣': '0', '1️⃣': '1', '2️⃣': '2', '3️⃣': '3', '4️⃣': '4',
        '5️⃣': '5', '6️⃣': '6', '7️⃣': '7', '8️⃣': '8', '9️⃣': '9'
    }
    for emoji, num in emoji_numbers.items():
        normalized = normalized.replace(emoji, num)
        
    clean_text = re.sub(r'[\.\-\_\*\#\!\?\$\%\&\|]', '', normalized)
    
    leet_map = {
        '0': 'o', '3': 'e', '4': 'a', '5': 's', '1': 'i', '@': 'a'
    }
    leet_text = clean_text.lower()
    for leet, letter in leet_map.items():
        leet_text = leet_text.replace(leet, letter)
    
    if _CONTACT_REGEX.search(normalized):
        return True
    
    if _CONTACT_REGEX.search(clean_text):
        return True
    
    if _CONTACT_REGEX.search(leet_text):
        return True
    
    if _NUMBER_WORDS_REGEX.search(normalized):
        return True
    
    return False

def sanitize_for_notification(text: str) -> str:
    if not text:
        return text
    
    sanitized = text
    for pattern in _PHONE_PATTERNS:
        sanitized = re.sub(pattern, '***TELEFONE***', sanitized, flags=re.IGNORECASE)
    
    sanitized = re.sub(_EMAIL_PATTERN, '***EMAIL***', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'@[a-zA-Z0-9_.]{3,}', '***@PERFIL***', sanitized)
    
    return sanitized
