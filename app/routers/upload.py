from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from app.dependencies import get_current_user, get_current_host
from app.models.user import User
from app.models.space import Space, SpaceImage
from app.services.upload_service import UploadService
from app.schemas.space import SpaceImageResponse
from sqlalchemy.future import select

router = APIRouter(prefix="/upload", tags=["Uploads"])


@router.post("/spaces/{space_id}/media", response_model=List[SpaceImageResponse])
async def upload_space_media(
    space_id: UUID,
    images: List[UploadFile] = File(default=[]),
    video: Optional[UploadFile] = File(None),
    current_host: User = Depends(get_current_host),
    db: AsyncSession = Depends(get_db)
):
    """Upload de imagens e vídeo para um espaço existente."""
    # Verify space exists and belongs to host
    result = await db.execute(select(Space).where(Space.id == space_id))
    space = result.scalars().first()
    if not space:
        raise HTTPException(status_code=404, detail="Espaço não encontrado")
    if space.host_id != current_host.id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    upload_service = UploadService()
    uploaded_images = []

    # Delete existing placeholder images first
    existing = await db.execute(
        select(SpaceImage).where(SpaceImage.space_id == space_id)
    )
    for old_img in existing.scalars().all():
        # Try to delete from S3 if it's a real URL
        if old_img.url and 's3.' in old_img.url:
            await upload_service.delete_file(old_img.url)
        await db.delete(old_img)

    # Upload images
    for idx, image in enumerate(images):
        if image and image.filename:
            url = await upload_service.upload_file(
                image,
                folder=f"spaces/{space_id}/images",
                max_size_mb=10,
                allowed_types=['image/jpeg', 'image/png', 'image/webp', 'image/gif']
            )
            if url:
                db_image = SpaceImage(
                    space_id=space_id,
                    url=url,
                    media_type="IMAGE",
                    is_cover=(idx == 0),
                    order=idx
                )
                db.add(db_image)
                uploaded_images.append(db_image)

    # Upload video
    if video and video.filename:
        video_url = await upload_service.upload_file(
            video,
            folder=f"spaces/{space_id}/videos",
            max_size_mb=100,
            allowed_types=['video/mp4', 'video/quicktime', 'video/webm', 'video/x-m4v']
        )
        if video_url:
            db_video = SpaceImage(
                space_id=space_id,
                url=video_url,
                media_type="VIDEO",
                is_cover=False,
                order=len(uploaded_images)
            )
            db.add(db_video)
            uploaded_images.append(db_video)

    await db.commit()

    # Refresh to get IDs
    for img in uploaded_images:
        await db.refresh(img)

    return uploaded_images
