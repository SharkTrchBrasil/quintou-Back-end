from uuid import UUID
from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserUpdate, UserResponse
from app.models.user import User
from app.dependencies import get_current_user
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Usuários"])

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy.sql import func
    current_user.last_seen_at = func.now()
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    return await user_service.update(current_user.id, user_in)

@router.put("/me/become-host", response_model=UserResponse)
async def become_host(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    return await user_service.become_host(current_user.id)

from fastapi_cache.decorator import cache

@router.get("/{user_id}", response_model=UserResponse)
@cache(expire=300)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    return await user_service.get(user_id)

@router.put("/me/fcm-token")
async def update_fcm_token(
    fcm_token: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    current_user.firebase_token = fcm_token
    await db.commit()
    return {"status": "ok"}

from fastapi import UploadFile, File, HTTPException
from app.services.upload_service import UploadService

@router.post("/me/address-proof", response_model=UserResponse)
async def upload_address_proof(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Faz upload do comprovante de endereço do usuário e salva a URL no perfil.
    """
    if not file.content_type.startswith("image/") and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Formato de arquivo inválido. Envie imagem ou PDF.")
        
    upload_service = UploadService()
    try:
        url = await upload_service.upload_file(file, folder=f"address_proofs/{current_user.id}")
        
        current_user.address_proof_url = url
        await db.commit()
        await db.refresh(current_user)
        
        return current_user
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao fazer upload do arquivo.")
