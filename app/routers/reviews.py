from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.review import ReviewCreate, ReviewResponse
from app.models.user import User
from app.dependencies import get_current_user
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Avaliações"])

@router.post("", response_model=ReviewResponse, status_code=201)
async def create_review(
    review_in: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    review_service = ReviewService(db)
    return await review_service.create(current_user.id, review_in)

@router.get("/space/{space_id}", response_model=list[ReviewResponse])
async def list_space_reviews(
    space_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    review_service = ReviewService(db)
    return await review_service.list_by_space(space_id, limit, offset)

@router.get("/user/{user_id}", response_model=list[ReviewResponse])
async def list_user_reviews(
    user_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    review_service = ReviewService(db)
    return await review_service.list_by_user(user_id, limit, offset)
