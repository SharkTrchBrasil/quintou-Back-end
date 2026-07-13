from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.middleware.rate_limit import RateLimitMiddleware

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Marketplace de aluguel de espaços por hora",
    )

    # Configuração de CORS
    origins = settings.CORS_ORIGINS
    if isinstance(origins, str):
        origins = [origin.strip() for origin in origins.split(",")]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate Limiting - 60 requests per minute per IP
    # TODO: Em produção, usar Redis + slowapi ou similar para cluster multi-worker
    app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

    # Rota raiz/health
    @app.get("/", tags=["Health"])
    async def health_check():
        return {"status": "ok", "app": settings.PROJECT_NAME, "version": settings.VERSION}

    from app.routers import include_routers
    include_routers(app)
    from app.exceptions import setup_exception_handlers
    setup_exception_handlers(app)

    return app

app = create_app()
