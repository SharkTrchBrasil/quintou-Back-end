"""
Security headers middleware
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adiciona headers de segurança em todas as respostas.
    
    Headers incluídos:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: força HTTPS (apenas em produção)
    - Content-Security-Policy: política básica de CSP
    """
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # Previne MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Previne clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Proteção XSS (legado, mas ainda útil)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Remove header Server para não expor tecnologia
        if "Server" in response.headers:
            del response.headers["Server"]
        
        # HSTS - Force HTTPS (apenas em produção com HTTPS)
        from app.config import settings
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy básico
        # Para APIs, CSP é menos crítico mas ainda útil
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
        
        # Permissões de recursos
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response
