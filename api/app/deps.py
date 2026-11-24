from uuid import UUID

from fastapi import Header, HTTPException, status

from app.settings import get_settings


def current_user_id(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> UUID:
    s = get_settings()
    expected = (s.api_key or "").strip()
    if expected:
        if not x_api_key or x_api_key.strip() != expected:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key inválida")
    return s.default_user_id