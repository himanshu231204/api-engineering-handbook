"""Admin-only routes, demonstrating RBAC enforcement end to end."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.user import UserOut
from app.security.dependencies import require_role
from app.services.auth_service import AuthService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
async def list_users(
    _admin=Depends(require_role("admin")), session: AsyncSession = Depends(get_session)
) -> list[UserOut]:
    service = AuthService(session)
    users = await service.list_users()
    return [UserOut.model_validate(u) for u in users]
