from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.inbound_event import InboundEvent
from app.schemas.delivery import InboundEventRead
from app.services.inbound_service import InboundService

router = APIRouter(tags=["inbound"])


@router.post("/webhooks/inbound/{source}", status_code=status.HTTP_200_OK)
async def receive_inbound_webhook(
    source: str,
    request: Request,
    x_webhook_signature: str = Header(...),
    x_webhook_timestamp: int = Header(...),
    x_event_id: str = Header(..., alias="X-Event-Id"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    raw_body = await request.body()
    service = InboundService(session)

    signature_valid = service.verify_signature(
        payload_bytes=raw_body, signature=x_webhook_signature, timestamp=x_webhook_timestamp
    )
    if not signature_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or stale signature")

    try:
        payload = await request.json()
    except Exception as exc:  # noqa: BLE001 - malformed body is a client error either way
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="body must be valid JSON") from exc

    event, created = await service.record_event(
        source=source, provider_event_id=x_event_id, payload=payload, signature_valid=True
    )
    await session.commit()
    return {"received": True, "event_id": event.id, "duplicate": not created}


@router.get("/webhooks/inbound/events", response_model=list[InboundEventRead])
async def list_inbound_events(
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[InboundEventRead]:
    result = await session.execute(select(InboundEvent).order_by(InboundEvent.received_at.desc()).limit(limit))
    return [InboundEventRead.model_validate(e) for e in result.scalars().all()]
