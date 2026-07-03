from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

bearer = HTTPBearer(auto_error=False)

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def _user_from_token(token: str, db: AsyncSession) -> User:
    try:
        payload = decode_token(token)
    except Exception as exc:  # noqa: BLE001
        raise _CREDENTIALS_ERROR from exc
    if payload.get("type") != "access":
        raise _CREDENTIALS_ERROR
    sub = payload.get("sub")
    if not sub:
        raise _CREDENTIALS_ERROR
    user = await db.get(User, uuid.UUID(sub))
    if user is None:
        raise _CREDENTIALS_ERROR
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise _CREDENTIALS_ERROR
    return await _user_from_token(credentials.credentials, db)


async def user_from_query_token(token: str, db: AsyncSession) -> User:
    """Resolve a user from a token passed as a query param (for SSE/EventSource)."""
    return await _user_from_token(token, db)
