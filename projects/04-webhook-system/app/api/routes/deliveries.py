from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.delivery import Delivery, DeliveryAttempt, OutboundEvent
from app.schemas.delivery import (
    DeliveryAttemptRead,
    DeliveryDetail,
    DeliveryList,
    DeliveryRead,
    OutboundEventCreate,
)
from app.services.dispatcher import Dispatcher

router = APIRouter(tags=["deliveries"])


@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def publish_event(payload: OutboundEventCreate, session: AsyncSession = Depends(get_session)) -> dict:
    """Not in the original endpoint table, but required to make the
    outbound side reachable over HTTP: publishes an internal domain event
    and fans it out to matching subscriptions as pending deliveries."""
    dispatcher = Dispatcher(session)
    event = await dispatcher.dispatch(event_type=payload.event_type, payload=payload.payload)
    await session.commit()
    return {"event_id": event.id}


@router.get("/subscriptions/{subscription_id}/deliveries", response_model=DeliveryList)
async def list_subscription_deliveries(
    subscription_id: str,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> DeliveryList:
    query = select(Delivery).where(Delivery.subscription_id == subscription_id)
    if status_filter:
        query = query.where(Delivery.status == status_filter)

    count_result = await session.execute(select(func.count()).select_from(query.subquery()))
    total = int(count_result.scalar_one())

    query = query.order_by(Delivery.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(query)
    items = [DeliveryRead.model_validate(d) for d in result.scalars().all()]
    return DeliveryList(items=items, total=total, limit=limit, offset=offset)


@router.get("/deliveries/{delivery_id}", response_model=DeliveryDetail)
async def get_delivery(delivery_id: str, session: AsyncSession = Depends(get_session)) -> DeliveryDetail:
    delivery = await session.get(Delivery, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="delivery not found")

    result = await session.execute(
        select(DeliveryAttempt)
        .where(DeliveryAttempt.delivery_id == delivery_id)
        .order_by(DeliveryAttempt.attempt_number)
    )
    attempts = [DeliveryAttemptRead.model_validate(a) for a in result.scalars().all()]
    return DeliveryDetail(**DeliveryRead.model_validate(delivery).model_dump(), attempts=attempts)


@router.post("/deliveries/{delivery_id}/redeliver", response_model=DeliveryRead)
async def redeliver(delivery_id: str, session: AsyncSession = Depends(get_session)) -> DeliveryRead:
    delivery = await session.get(Delivery, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="delivery not found")

    delivery.status = "pending"
    delivery.attempt_count = 0
    delivery.next_attempt_at = datetime.now(timezone.utc)
    delivery.last_error = None
    delivery.last_status_code = None
    await session.commit()
    await session.refresh(delivery)
    return DeliveryRead.model_validate(delivery)


@router.get("/dead-letters", response_model=DeliveryList)
async def list_dead_letters(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> DeliveryList:
    query = select(Delivery).where(Delivery.status == "dead_letter")
    count_result = await session.execute(select(func.count()).select_from(query.subquery()))
    total = int(count_result.scalar_one())

    query = query.order_by(Delivery.updated_at.desc()).limit(limit).offset(offset)
    result = await session.execute(query)
    items = [DeliveryRead.model_validate(d) for d in result.scalars().all()]
    return DeliveryList(items=items, total=total, limit=limit, offset=offset)
