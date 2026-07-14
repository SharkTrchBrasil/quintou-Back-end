"""
Logging configuration for the application
"""
import logging
import sys
from typing import Any
import structlog
from app.config import settings


def setup_logging():
    """
    Configura logging estruturado com structlog.
    
    Em desenvolvimento: logs coloridos e legíveis
    Em produção: logs em JSON para integração com ferramentas de monitoramento
    """
    
    # Determina nível de log baseado no ambiente
    log_level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO
    
    # Configura logging padrão do Python
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Configura processadores do structlog
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if settings.ENVIRONMENT == "development":
        # Desenvolvimento: output colorido e legível
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        # Produção: output em JSON
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Reduz verbosidade de bibliotecas externas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    logger = structlog.get_logger()
    logger.info(
        "Logging configured",
        environment=settings.ENVIRONMENT,
        log_level=logging.getLevelName(log_level)
    )


def get_logger(name: str = None) -> Any:
    """
    Obtém um logger estruturado.
    
    Args:
        name: Nome do logger (geralmente __name__)
    
    Returns:
        Logger estruturado
    """
    return structlog.get_logger(name)
