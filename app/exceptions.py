from fastapi import Request, status
from fastapi.responses import JSONResponse

class BusinessException(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.detail = detail
        self.status_code = status_code

async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

def setup_exception_handlers(app):
    app.add_exception_handler(BusinessException, business_exception_handler)
