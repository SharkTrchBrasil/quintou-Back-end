import uuid
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.models.review import Review, ReviewType
from app.models.booking import Booking, BookingStatus
from app.models.space import Space
from app.schemas.review import ReviewCreate

class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_space_reviews(self, space_id: uuid.UUID, skip: int = 0, limit: int = 20) -> Tuple[List[Review], int]:
        query = select(Review).where(
            Review.space_id == space_id,
            Review.type == ReviewType.GUEST_TO_HOST
        ).order_by(Review.created_at.desc())
        
        result = await self.db.execute(query.offset(skip).limit(limit))
        reviews = result.scalars().all()
        
        from sqlalchemy import func
        count_query = select(func.count(Review.id)).where(
            Review.space_id == space_id,
            Review.type == ReviewType.GUEST_TO_HOST
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        return list(reviews), total

    async def create_review(self, user_id: uuid.UUID, review_in: ReviewCreate) -> Review:
        # Busca a reserva
        query = select(Booking).where(Booking.id == review_in.booking_id)
        result = await self.db.execute(query)
        booking = result.scalars().first()
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking não encontrada")
            
        if booking.status != BookingStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Apenas reservas completadas podem ser avaliadas")
            
        # Define quem é quem
        is_guest = booking.guest_id == user_id
        
        # O Space tem o host_id
        space_result = await self.db.execute(select(Space).where(Space.id == booking.space_id))
        space = space_result.scalars().first()
        if not space:
            raise HTTPException(status_code=404, detail="Espaço não encontrado")
            
        is_host = space.host_id == user_id
        
        if not is_guest and not is_host:
            raise HTTPException(status_code=403, detail="Você não faz parte desta reserva")
            
        review_type = ReviewType.GUEST_TO_HOST if is_guest else ReviewType.HOST_TO_GUEST
        reviewee_id = space.host_id if is_guest else booking.guest_id
        
        # Evitar avaliação duplicada
        dup_query = select(Review).where(
            Review.booking_id == booking.id,
            Review.reviewer_id == user_id
        )
        dup_result = await self.db.execute(dup_query)
        if dup_result.scalars().first():
            raise HTTPException(status_code=400, detail="Você já avaliou esta reserva")
            
        # Cria a avaliação
        review = Review(
            booking_id=booking.id,
            reviewer_id=user_id,
            reviewee_id=reviewee_id,
            space_id=booking.space_id if is_guest else None,
            type=review_type,
            rating=review_in.rating,
            comment=review_in.comment,
            event_type=review_in.event_type,
            cleanliness_rating=review_in.cleanliness_rating if is_guest else None,
            accuracy_rating=review_in.accuracy_rating if is_guest else None,
            communication_rating=review_in.communication_rating if is_guest else None,
            value_rating=review_in.value_rating if is_guest else None
        )
        
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        
        # Atualiza a média do espaço (apenas se for guest avaliando o host/space)
        if is_guest:
            await self._update_space_rating(space.id)
            
        return review
        
    async def _update_space_rating(self, space_id: uuid.UUID):
        # Calcula a nova média
        from sqlalchemy import func
        avg_query = select(func.avg(Review.rating), func.count(Review.id)).where(
            Review.space_id == space_id,
            Review.type == ReviewType.GUEST_TO_HOST
        )
        avg_result = await self.db.execute(avg_query)
        avg_rating, total_reviews = avg_result.one()
        
        # Atualiza o espaço
        space_query = select(Space).where(Space.id == space_id)
        space_result = await self.db.execute(space_query)
        space = space_result.scalars().first()
        
        if space:
            space.average_rating = float(avg_rating) if avg_rating else 0.0
            space.total_reviews = int(total_reviews) if total_reviews else 0
            await self.db.commit()
