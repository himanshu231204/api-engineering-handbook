from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_session
from app.models.subscription import Subscription
from app.schemas.subscription import (
    SecretRotated,
    SubscriptionCreate,
    SubscriptionCreated,
    SubscriptionRead,
    SubscriptionUpdate,
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def _generate_secret() -> str:
    return secrets.token_hex(32)


@router.post("", response_model=SubscriptionCreated, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    payload: SubscriptionCreate, session: AsyncSession = Depends(get_session)
) -> SubscriptionCreated:
    secret = _generate_secret()
    subscription = Subscription(
        customer_id=payload.customer_id,
        target_url=payload.target_url,
        event_types=payload.event_types,
        signing_secret=secret,
        status="active",
    )
    session.add(subscription)
    await session.flush()
    await session.refresh(subscription)
    await session.commit()
    return SubscriptionCreated(**SubscriptionRead.model_validate(subscription).model_dump(), signing_secret=secret)


@router.get("", response_model=list[SubscriptionRead])
async def list_subscriptions(
    customer_id: str, session: AsyncSession = Depends(get_session)
) -> list[SubscriptionRead]:
    result = await session.execute(select(Subscription).where(Subscription.customer_id == customer_id))
    return [SubscriptionRead.model_validate(s) for s in result.scalars().all()]


async def _get_or_404(session: AsyncSession, subscription_id: str) -> Subscription:
    subscription = await session.get(Subscription, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subscription not found")
    return subscription


@router.patch("/{subscription_id}", response_model=SubscriptionRead)
async def update_subscription(
    subscription_id: str, payload: SubscriptionUpdate, session: AsyncSession = Depends(get_session)
) -> SubscriptionRead:
    subscription = await _get_or_404(session, subscription_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(subscription, field, value)
    await session.commit()
    await session.refresh(subscription)
    return SubscriptionRead.model_validate(subscription)


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(subscription_id: str, session: AsyncSession = Depends(get_session)) -> None:
    subscription = await session.get(Subscription, subscription_id)
    if subscription is not None:
        await session.delete(subscription)
        await session.commit()


@router.post("/{subscription_id}/rotate-secret", response_model=SecretRotated)
async def rotate_secret(subscription_id: str, session: AsyncSession = Depends(get_session)) -> SecretRotated:
    subscription = await _get_or_404(session, subscription_id)
    new_secret = _generate_secret()
    subscription.previous_secret = subscription.signing_secret
    subscription.signing_secret = new_secret
    subscription.secret_rotated_at = datetime.now(timezone.utc)
    await session.commit()

    grace_until = subscription.secret_rotated_at + timedelta(minutes=settings.secret_rotation_grace_minutes)
    return SecretRotated(signing_secret=new_secret, previous_secret_valid_until=grace_until)
