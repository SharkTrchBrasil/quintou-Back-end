from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from asgi_correlation_id import CorrelationIdMiddleware
import redis.asyncio as redis
from app.config import settings
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi.middleware.gzip import GZipMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.utils.logger import setup_logging
import contextlib

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar Redis para rate limiter
    redis_connection = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis_connection), prefix="fastapi-cache")
    
    yield
    
    # Clean up Redis connection
    await redis_connection.close()

def create_app() -> FastAPI:
    setup_logging()
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Marketplace de aluguel de espaços por hora",
        lifespan=lifespan,
    )
    
    # Configura exception handlers
    from app.exceptions import setup_exception_handlers
    setup_exception_handlers(app)

    # Configuração de CORS
    origins = settings.CORS_ORIGINS
    if isinstance(origins, str):
        origins = [origin.strip() for origin in origins.split(",")]
    
    # Em produção, valida que origins não contém "*"
    if settings.ENVIRONMENT == "production" and "*" in origins:
        import logging
        logging.getLogger(__name__).warning(
            "CORS wildcard (*) detected in production. This is insecure!"
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],  # Expõe correlation ID
        max_age=3600,  # Cache preflight por 1 hora
    )

    # GZip compression for responses > 1000 bytes
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Correlation ID middleware
    app.add_middleware(CorrelationIdMiddleware)

    # Rota raiz/health
    @app.get("/", tags=["Health"])
    async def health_check():
        return {"status": "ok", "app": settings.PROJECT_NAME, "version": settings.VERSION}
    
    @app.get("/health", tags=["Health"])
    async def health_check_detailed():
        """Health check detalhado para monitoramento"""
        import time
        from sqlalchemy import text
        from app.database import get_db
        
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "app": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "checks": {}
        }
        
        # Check Database
        try:
            async for db in get_db():
                await db.execute(text("SELECT 1"))
                health_status["checks"]["database"] = "healthy"
                break
        except Exception as e:
            health_status["checks"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
        
        # Check Redis
        try:
            redis_connection = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
            await redis_connection.ping()
            await redis_connection.close()
            health_status["checks"]["redis"] = "healthy"
        except Exception as e:
            health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check S3
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            health_status["checks"]["s3"] = "configured"
        else:
            health_status["checks"]["s3"] = "not_configured"
        
        # Check Stripe
        if settings.STRIPE_SECRET_KEY:
            health_status["checks"]["stripe"] = "configured"
        else:
            health_status["checks"]["stripe"] = "not_configured"
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        return JSONResponse(content=health_status, status_code=status_code)

    from app.routers import include_routers
    include_routers(app)

    return app

app = create_app()
