from uuid import UUID
from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from app.models.booking import Booking, BookingStatus, BookingAddon
from app.models.space import Space, SpaceAddon, AddonPricingType, ListingType, ListingPricingMode, BlockedDate, AvailabilityException, CustomPricing
from app.models.promotion import SpacePromotion, PromotionType
from app.schemas.booking import BookingCreate
from app.utils.i18n import _
from app.constants import PLATFORM_GUEST_FEE_PERCENTAGE, PLATFORM_HOST_FEE_PERCENTAGE

class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def check_availability(self, space_id: UUID, date_req: date, start_time: time, end_time: time, lock: bool = False) -> bool:
        """
        Check if a space is available for the given date and time range.
        
        Args:
            space_id: The space to check
            date_req: The date to check
            start_time: Start time of the booking
            end_time: End time of the booking
            lock: If True, uses SELECT FOR UPDATE to lock rows (prevents race conditions)
        
        Returns:
            True if available, False if there's a conflict
        """
        # Check Blocked Dates
        blocked = await self.db.execute(
            select(BlockedDate).where(
                BlockedDate.space_id == space_id,
                BlockedDate.date == date_req.isoformat()
            )
        )
        if blocked.scalars().first():
            return False

        # Get space for buffer_minutes
        space_query = select(Space.buffer_minutes).where(Space.id == space_id)
        space_result = await self.db.execute(space_query)
        buffer_minutes = space_result.scalar_one_or_none() or 0
        
        # Calculate start and end with buffer
        start_with_buffer = (datetime.combine(date_req, start_time) - timedelta(minutes=buffer_minutes)).time()
        end_with_buffer = (datetime.combine(date_req, end_time) + timedelta(minutes=buffer_minutes)).time()

        query = select(Booking).where(
            Booking.space_id == space_id,
            Booking.date == date_req,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            Booking.start_time < end_with_buffer,
            Booking.end_time > start_with_buffer
        )
        
        if lock:
            # Apply SELECT FOR UPDATE to lock conflicting bookings
            # This prevents race conditions during booking creation
            query = query.with_for_update()
        
        result = await self.db.execute(query)
        conflict = result.scalars().first()
        return not bool(conflict)
        
    def calculate_hours(self, start_time: time, end_time: time) -> int:
        start_dt = datetime.combine(datetime.today(), start_time)
        end_dt = datetime.combine(datetime.today(), end_time)
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)
        diff = end_dt - start_dt
        return int(diff.total_seconds() // 3600) + (1 if diff.total_seconds() % 3600 > 0 else 0)

    async def create(self, guest_id: UUID, booking_in: BookingCreate) -> Booking:
        # Load space with pricing tiers, promotions, and custom pricing
        query = select(Space).options(
            selectinload(Space.pricing_tiers),
            selectinload(Space.promotions),
            selectinload(Space.custom_pricing)
        ).where(Space.id == booking_in.space_id)
        result = await self.db.execute(query)
        space = result.scalars().first()
        
        if not space:
            raise HTTPException(status_code=404, detail=_("space_not_found"))
        
        # Valida que o espaço está ativo e aprovado
        if not space.is_active or not space.is_approved:
            raise HTTPException(status_code=400, detail="Este espaço não está disponível para reservas.")
            
        if space.host_id == guest_id:
            raise HTTPException(status_code=400, detail="Host cannot book own space.")
        
        # Valida que a data não é no passado
        from datetime import date as date_type
        today = date_type.today()
        if booking_in.date < today:
            raise HTTPException(status_code=400, detail=_("past_date_not_allowed"))
        
        # Valida horários
        if booking_in.start_time >= booking_in.end_time:
            raise HTTPException(status_code=400, detail=_("invalid_time"))
        
        # Valida componentes de convidados
        total_guests = booking_in.num_adults + booking_in.num_children + booking_in.num_infants
        if total_guests != booking_in.num_guests:
            raise HTTPException(
                status_code=400, 
                detail=f"Soma de adultos, crianças e bebês ({total_guests}) deve ser igual ao total de convidados ({booking_in.num_guests})"
            )
        
        # Valida valores não negativos
        if booking_in.num_adults < 0 or booking_in.num_children < 0 or booking_in.num_infants < 0 or booking_in.num_pets < 0:
            raise HTTPException(status_code=400, detail="Números de convidados e pets não podem ser negativos")
        
        # Pelo menos 1 adulto é obrigatório
        if booking_in.num_adults < 1:
            raise HTTPException(status_code=400, detail="Pelo menos 1 adulto é obrigatório")
        
        # Valida pets se o espaço não permite
        if booking_in.num_pets > 0 and not space.allows_pets:
            raise HTTPException(status_code=400, detail="Este espaço não aceita pets")
        
        # Valida crianças se o espaço não permite
        if booking_in.num_children > 0 and not space.allows_children:
            raise HTTPException(status_code=400, detail="Este espaço não aceita crianças")
        
        # Valida bebês se o espaço não permite
        if booking_in.num_infants > 0 and not space.allows_infants:
            raise HTTPException(status_code=400, detail="Este espaço não aceita bebês")
        
        # Check availability with pessimistic lock to prevent race conditions
        # This locks any conflicting bookings until our transaction commits
        if not await self.check_availability(
            space.id, 
            booking_in.date, 
            booking_in.start_time, 
            booking_in.end_time,
            lock=True  # Enable SELECT FOR UPDATE
        ):
            raise HTTPException(status_code=409, detail=_("booking_conflict"))
        
        hours = self.calculate_hours(booking_in.start_time, booking_in.end_time)
        
        if hours < space.min_hours or hours > space.max_hours:
            raise HTTPException(status_code=400, detail=f"Booking must be between {space.min_hours} and {space.max_hours} hours.")
            
        if space.max_guests and booking_in.num_guests > space.max_guests:
            raise HTTPException(status_code=400, detail=f"Max guests allowed is {space.max_guests}.")
        
        # Valida endereço de entrega para equipamentos
        from app.models.space import ListingType
        if space.listing_type == ListingType.EQUIPMENT and space.delivery_available:
            if not booking_in.delivery_address:
                raise HTTPException(
                    status_code=400, 
                    detail="Endereço de entrega é obrigatório para equipamentos com entrega."
                )

        # Calcular preço base de acordo com o pricing_mode
        base_price = space.price  # Valor base genérico
        
        # 1. Custom Pricing for specific date
        custom_price_found = False
        date_str = booking_in.date.isoformat()
        if space.custom_pricing:
            for cp in space.custom_pricing:
                if cp.date == date_str:
                    base_price = cp.price_per_hour
                    custom_price_found = True
                    break
        
        # 2. Se não tem custom price, verifica weekend / holiday
        if not custom_price_found:
            is_weekend = booking_in.date.weekday() >= 5 # 5=Sat, 6=Sun
            if is_weekend and space.price_per_hour_weekend:
                base_price = space.price_per_hour_weekend
            # TODO: Holiday integration
            
        # 3. Pricing tiers (por faixa de convidados) - só se aplicável
        if space.pricing_tiers:
            tier_found = False
            for tier in space.pricing_tiers:
                if tier.min_guests <= booking_in.num_guests <= tier.max_guests:
                    base_price = tier.price_per_hour  # Reusa campo existente como preço do tier
                    tier_found = True
                    break
            
            # Se há pricing tiers mas nenhum atende, erro
            if not tier_found and space.pricing_tiers:
                raise HTTPException(
                    status_code=400,
                    detail=f"Número de convidados ({booking_in.num_guests}) não se encaixa em nenhuma faixa de preço disponível."
                )
        
        # Desconto de dia de semana
        if booking_in.date.weekday() < 5 and space.weekday_discount_percent > 0:
            discount_mult = Decimal((100 - space.weekday_discount_percent) / 100)
            base_price = base_price * discount_mult

        # Calcular subtotal de acordo com o modo de preço
        if space.pricing_mode == ListingPricingMode.PER_HOUR:
            # Piscina: R$50/hr x 5 horas = R$250
            subtotal = base_price * Decimal(hours)
        elif space.pricing_mode == ListingPricingMode.PER_DAY:
            # Pula-pula: R$150/dia x 1 dia = R$150 (mínimo 1 dia)
            # Se reservar das 8h às 20h = 1 diária. Se cruzar a meia-noite = 2 diárias
            days = max(1, (hours + 23) // 24)  # Arredonda para cima
            subtotal = base_price * Decimal(days)
        else:  # FIXED
            # DJ: R$1.500 o pacote (não importa quantas horas)
            subtotal = base_price
        
        # Processar addons
        addons_total = Decimal('0.00')
        booking_addons_db = []
        if booking_in.selected_addons:
            addon_ids = [a.addon_id for a in booking_in.selected_addons]
            addons_query = select(SpaceAddon).where(SpaceAddon.id.in_(addon_ids), SpaceAddon.space_id == space.id)
            addons_result = await self.db.execute(addons_query)
            valid_addons = {a.id: a for a in addons_result.scalars().all()}
            
            for req_addon in booking_in.selected_addons:
                if req_addon.addon_id not in valid_addons:
                    raise HTTPException(status_code=400, detail=f"Invalid addon: {req_addon.addon_id}")
                    
                space_addon = valid_addons[req_addon.addon_id]
                
                # Valida que o addon está ativo
                if not space_addon.is_active:
                    raise HTTPException(status_code=400, detail=f"Addon '{space_addon.name}' não está disponível.")
                
                # Valida quantidade
                if req_addon.quantity <= 0:
                    raise HTTPException(status_code=400, detail=f"Quantidade do addon '{space_addon.name}' deve ser maior que zero.")
                
                # Calcular preço com base no tipo
                if space_addon.pricing_type == AddonPricingType.FLAT:
                    # Preço único indiferente da quantidade (ex: Taxa de Limpeza de $50)
                    addon_tot = space_addon.price
                    req_addon.quantity = 1 # Força quantidade 1
                elif space_addon.pricing_type == AddonPricingType.PER_HOUR:
                    # Preço por hora indiferente da quantidade (ex: Shower a $20/hr)
                    addon_tot = space_addon.price * Decimal(hours)
                    req_addon.quantity = 1 # Força quantidade 1
                else: # PER_UNIT
                    # Multiplica preço pela quantidade informada (ex: Cadeira a $3/cada)
                    addon_tot = space_addon.price * Decimal(req_addon.quantity)

                addons_total += addon_tot
                
                db_b_addon = BookingAddon(
                    addon_id=space_addon.id,
                    quantity=req_addon.quantity,
                    unit_price=space_addon.price,
                    total_price=addon_tot
                )
                booking_addons_db.append(db_b_addon)

        # Aplicar Promoções (ex: Grand Opening Discount)
        total_discount = Decimal('0.00')
        now = datetime.now(timezone.utc)
        if space.promotions:
            for promo in space.promotions:
                if not promo.is_active:
                    continue
                if promo.start_date and promo.start_date > now:
                    continue
                if promo.end_date and promo.end_date < now:
                    continue
                if promo.min_hours and hours < promo.min_hours:
                    continue
                if promo.min_guests and booking_in.num_guests < promo.min_guests:
                    continue
                
                # Aplica desconto no subtotal das horas (não afeta addons geralmente)
                if promo.type == PromotionType.PERCENTAGE:
                    discount = subtotal * (promo.value / Decimal('100.00'))
                else:
                    discount = promo.value
                
                total_discount += discount
                
        subtotal_after_discount = max(Decimal('0.00'), subtotal - total_discount)

        # Taxa de entrega (para equipamentos)
        delivery_fee = Decimal('0.00')
        if space.listing_type == ListingType.EQUIPMENT and space.delivery_available and booking_in.delivery_address:
            delivery_fee = space.delivery_fee or Decimal('0.00')
            
            # Valida que delivery_fee não é negativo
            if delivery_fee < 0:
                delivery_fee = Decimal('0.00')

        # Taxas da plataforma (usando constantes padronizadas)
        service_fee = (subtotal_after_discount + addons_total) * PLATFORM_GUEST_FEE_PERCENTAGE  # 10% taxa do guest
        host_fee = (subtotal_after_discount + addons_total) * PLATFORM_HOST_FEE_PERCENTAGE      # 15% taxa do host
        
        # Valida que valores finais não são negativos
        service_fee = max(Decimal('0.00'), service_fee)
        host_fee = max(Decimal('0.00'), host_fee)
        
        total_price = subtotal_after_discount + addons_total + delivery_fee + service_fee
        host_payout = subtotal_after_discount + addons_total + delivery_fee - host_fee
        
        # Garante que host_payout não seja negativo
        host_payout = max(Decimal('0.00'), host_payout)
        
        deposit_status = "HELD" if space.security_deposit > 0 else "NONE"
        
        db_booking = Booking(
            space_id=space.id,
            guest_id=guest_id,
            date=booking_in.date,
            start_time=booking_in.start_time,
            end_time=booking_in.end_time,
            total_hours=hours,
            num_guests=booking_in.num_guests,
            num_adults=booking_in.num_adults,
            num_children=booking_in.num_children,
            num_infants=booking_in.num_infants,
            num_pets=booking_in.num_pets,
            guest_message=booking_in.guest_message,
            event_type=booking_in.event_type,
            subtotal=subtotal,
            addons_total=addons_total,
            delivery_fee=delivery_fee,
            delivery_address=booking_in.delivery_address,
            service_fee=service_fee,
            host_fee=host_fee,
            total_price=total_price,
            host_payout=host_payout,
            deposit_amount=space.security_deposit,
            deposit_status=deposit_status,
            status=BookingStatus.PENDING if space.requires_approval else BookingStatus.CONFIRMED
        )
        
        self.db.add(db_booking)
        await self.db.flush()
        
        for ba in booking_addons_db:
            ba.booking_id = db_booking.id
            self.db.add(ba)
            
        await self.db.commit()
        
        # Reload with eager loading to avoid MissingGreenlet
        return await self._get_with_relations(db_booking.id)
        
    async def _get_with_relations(self, booking_id: UUID) -> Booking:
        """Internal helper to load a booking with all relations eagerly."""
        query = select(Booking).options(
            selectinload(Booking.space).selectinload(Space.images),
            selectinload(Booking.space).selectinload(Space.category),
            selectinload(Booking.guest),
            selectinload(Booking.addons)
        ).where(Booking.id == booking_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get(self, booking_id: UUID, user_id: UUID) -> Booking:
        query = select(Booking).options(
            selectinload(Booking.space).selectinload(Space.images),
            selectinload(Booking.space).selectinload(Space.category),
            selectinload(Booking.guest),
            selectinload(Booking.addons)
        ).where(Booking.id == booking_id)
        result = await self.db.execute(query)
        booking = result.scalars().first()
        
        if not booking:
            raise HTTPException(status_code=404, detail=_("booking_not_found"))
            
        if booking.guest_id != user_id and booking.space.host_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this booking.")
            
        return booking

    async def list_guest_bookings(self, guest_id: UUID, limit: int = 20, offset: int = 0):
        query = select(Booking).options(
            selectinload(Booking.space).selectinload(Space.images),
            selectinload(Booking.space).selectinload(Space.category),
            selectinload(Booking.guest),
            selectinload(Booking.addons)
        ).where(Booking.guest_id == guest_id).order_by(Booking.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def list_host_bookings(self, host_id: UUID, limit: int = 20, offset: int = 0):
        query = select(Booking).join(Space).options(
            selectinload(Booking.space).selectinload(Space.images),
            selectinload(Booking.space).selectinload(Space.category),
            selectinload(Booking.guest),
            selectinload(Booking.addons)
        ).where(Space.host_id == host_id).order_by(Booking.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_status(self, booking_id: UUID, user_id: UUID, new_status: BookingStatus, reason: str = None) -> Booking:
        booking = await self.get(booking_id, user_id)
        
        # Validation for state transitions
        is_host = booking.space.host_id == user_id
        is_guest = booking.guest_id == user_id
        
        # Obter payment relacionado (para estorno se necessário)
        from app.models.payment import Payment, PaymentStatus
        payment_query = select(Payment).where(Payment.booking_id == booking_id)
        payment_result = await self.db.execute(payment_query)
        payment = payment_result.scalar_one_or_none()
        
        if new_status == BookingStatus.CONFIRMED:
            if not is_host: raise HTTPException(status_code=403, detail="Only host can confirm.")
            if booking.status != BookingStatus.PENDING: raise HTTPException(status_code=400, detail="Booking is not pending.")
            
        elif new_status == BookingStatus.CANCELLED_BY_HOST:
            if not is_host: raise HTTPException(status_code=403, detail="Only host can cancel as host.")
            if booking.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED_BY_GUEST, BookingStatus.CANCELLED_BY_HOST]:
                raise HTTPException(status_code=400, detail="Cannot cancel booking in current state.")
            booking.cancellation_reason = reason
            booking.cancelled_at = datetime.now(timezone.utc)
            
            # Reembolso de 100% para o Guest
            if payment and payment.status == PaymentStatus.COMPLETED and payment.stripe_payment_intent_id:
                from app.services import stripe_service
                try:
                    refund_result = stripe_service.process_refund(payment.stripe_payment_intent_id)
                    payment.status = PaymentStatus.REFUNDED
                    payment.refunded_at = datetime.now(timezone.utc)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Error processing refund: {str(e)}")
            
        elif new_status == BookingStatus.CANCELLED_BY_GUEST:
            if not is_guest: raise HTTPException(status_code=403, detail="Only guest can cancel as guest.")
            if booking.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED_BY_GUEST, BookingStatus.CANCELLED_BY_HOST]:
                raise HTTPException(status_code=400, detail="Cannot cancel booking in current state.")
            booking.cancellation_reason = reason
            booking.cancelled_at = datetime.now(timezone.utc)
            # Lógica de reembolso baseada na política de cancelamento do espaço
            if payment and payment.status == PaymentStatus.COMPLETED and payment.stripe_payment_intent_id:
                from app.services import stripe_service
                from app.models.space import CancellationPolicy
                
                # Calcular horas até o check-in
                booking_dt = datetime.combine(booking.date, booking.start_time)
                now_dt = datetime.now()
                hours_until_checkin = (booking_dt - now_dt).total_seconds() / 3600.0
                
                refund_amount = None # None significa 100% na nossa stripe_service
                policy = booking.space.cancellation_policy
                hours_before = booking.space.cancellation_hours_before or 24
                
                if policy == CancellationPolicy.FLEXIVEL:
                    if hours_until_checkin < hours_before:
                        refund_amount = float(booking.total_price) * 0.5 # 50%
                elif policy == CancellationPolicy.MODERADA:
                    if hours_until_checkin < 120: # Menos de 5 dias
                        refund_amount = float(booking.total_price) * 0.5 # 50%
                elif policy == CancellationPolicy.RIGOROSA:
                    if hours_until_checkin >= 336: # 14 dias ou mais
                        refund_amount = None # 100%
                    elif hours_until_checkin >= 168: # Entre 7 e 14 dias
                        refund_amount = float(booking.total_price) * 0.5 # 50%
                    else:
                        refund_amount = 0.0 # Sem reembolso se menos de 7 dias
                
                try:
                    if refund_amount != 0.0:
                        refund_result = stripe_service.process_refund(
                            payment.stripe_payment_intent_id, 
                            amount=refund_amount
                        )
                        payment.status = PaymentStatus.REFUNDED
                        payment.refunded_at = datetime.now(timezone.utc)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Error processing refund: {str(e)}")
            
        elif new_status == BookingStatus.COMPLETED:
            if booking.status != BookingStatus.CONFIRMED:
                raise HTTPException(status_code=400, detail="Only confirmed bookings can be completed.")
            # In a real app, this might be a cron job checking the end_time
            
        else:
            raise HTTPException(status_code=400, detail=f"Invalid status transition to {new_status.value}")
            
        booking.status = new_status
        await self.db.commit()
        await self.db.refresh(booking)
        return booking
