from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.review import Review, ReviewType
from app.models.booking import Booking, BookingStatus
from app.models.space import Space
from app.models.user import User
from app.schemas.review import ReviewCreate
from app.utils.i18n import _

class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def create(self, reviewer_id: UUID, review_in: ReviewCreate) -> Review:
        # Busca booking com space carregado
        result = await self.db.execute(
            select(Booking).options(selectinload(Booking.space)).where(Booking.id == review_in.booking_id)
        )
        booking = result.scalars().first()
        
        if not booking:
            raise HTTPException(status_code=404, detail=_("booking_not_found", "Reserva não encontrada."))
            
        if booking.status != BookingStatus.COMPLETED:
            raise HTTPException(status_code=400, detail=_("invalid_booking_status"))
            
        # Determina o tipo e reviewee
        if reviewer_id == booking.guest_id:
            review_type = ReviewType.GUEST_TO_HOST
            reviewee_id = booking.space.host_id
        elif reviewer_id == booking.space.host_id:
            review_type = ReviewType.HOST_TO_GUEST
            reviewee_id = booking.guest_id
        else:
            raise HTTPException(status_code=403, detail="Apenas host e guest podem avaliar.")
            
        # Checa se já avaliou
        check_query = select(Review).where(
            Review.booking_id == booking.id,
            Review.reviewer_id == reviewer_id
        )
        existing = (await self.db.execute(check_query)).scalars().first()
        if existing:
            raise HTTPException(status_code=400, detail="Você já avaliou esta reserva.")

        db_review = Review(
            booking_id=booking.id,
            reviewer_id=reviewer_id,
            reviewee_id=reviewee_id,
            space_id=booking.space_id if review_type == ReviewType.GUEST_TO_HOST else None,
            type=review_type,
            rating=review_in.rating,
            comment=review_in.comment,
            cleanliness_rating=review_in.cleanliness_rating,
            accuracy_rating=review_in.accuracy_rating,
            communication_rating=review_in.communication_rating
        )
        
        self.db.add(db_review)
        await self.db.commit()
        await self.db.refresh(db_review)
        
        # TODO: Atualizar average_rating assincronamente (em background task)
        
        return db_review

    async def get(self, review_id: UUID) -> Review:
        query = select(Review).options(
            selectinload(Review.reviewer)
        ).where(Review.id == review_id)
        result = await self.db.execute(query)
        review = result.scalars().first()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        return review

    async def list_by_space(self, space_id: UUID, limit: int = 20, offset: int = 0) -> list[Review]:
        query = select(Review).options(
            selectinload(Review.reviewer)
        ).where(
            Review.space_id == space_id, 
            Review.type == ReviewType.GUEST_TO_HOST
        ).order_by(Review.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_user(self, user_id: UUID, limit: int = 20, offset: int = 0) -> list[Review]:
        query = select(Review).options(
            selectinload(Review.reviewer)
        ).where(
            Review.reviewee_id == user_id
        ).order_by(Review.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())
