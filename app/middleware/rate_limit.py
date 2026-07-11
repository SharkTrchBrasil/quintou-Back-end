from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple
import time

# Implementação super simples em memória para desenvolvimento.
# Em produção, deve-se usar Redis.
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.clients: Dict[str, Tuple[int, float]] = {}

    async def dispatch(self, request: Request, call_next):
        # Exemplo simples, não usar isso em prod multi-worker
        client_ip = request.client.host
        current_time = time.time()
        
        if client_ip in self.clients:
            count, start_time = self.clients[client_ip]
            if current_time - start_time < 60:
                if count >= self.requests_per_minute:
                    # Em FastAPI Middlewares não podemos lançar HTTPException diretamente 
                    # de forma fácil sem tratar, mas para o exemplo serve a ideia.
                    from fastapi.responses import JSONResponse
                    return JSONResponse(status_code=429, content={"detail": "Too many requests"})
                self.clients[client_ip] = (count + 1, start_time)
            else:
                self.clients[client_ip] = (1, current_time)
        else:
            self.clients[client_ip] = (1, current_time)
            
        response = await call_next(request)
        return response
