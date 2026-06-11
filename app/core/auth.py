"""JWT utilities and Google OAuth token verification."""

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


class JWTDecodeError(Exception):
    """Raised when token decoding or validation fails."""


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def _fallback_encode(payload: dict, secret: str, algorithm: str) -> str:
    if algorithm != "HS256":
        raise RuntimeError(f"Unsupported JWT_ALGORITHM={algorithm!r} without python-jose")
    normalized = {
        key: int(value.timestamp()) if isinstance(value, datetime) else value
        for key, value in payload.items()
    }
    header = {"typ": "JWT", "alg": "HS256"}
    signing_input = ".".join(
        [
            _b64url_encode(json.dumps(header, separators=(",", ":")).encode()),
            _b64url_encode(json.dumps(normalized, separators=(",", ":")).encode()),
        ]
    )
    signature = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def _fallback_decode(token: str, secret: str, algorithms: list[str]) -> dict:
    if "HS256" not in algorithms:
        raise JWTDecodeError("Unsupported JWT algorithm")
    try:
        header_part, payload_part, signature_part = token.split(".")
        signing_input = f"{header_part}.{payload_part}"
        expected = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url_encode(expected), signature_part):
            raise JWTDecodeError("Invalid JWT signature")
        header = json.loads(_b64url_decode(header_part))
        if header.get("alg") != "HS256":
            raise JWTDecodeError("Invalid JWT algorithm")
        payload = json.loads(_b64url_decode(payload_part))
    except (ValueError, json.JSONDecodeError) as exc:
        raise JWTDecodeError("Invalid JWT") from exc
    exp = payload.get("exp")
    if exp is not None and datetime.now(timezone.utc).timestamp() > float(exp):
        raise JWTDecodeError("JWT expired")
    return payload


def create_access_token(user_id: str, email: str, name: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRE_DAYS)
    payload = {"sub": user_id, "email": email, "name": name, "exp": expire}
    try:
        from jose import jwt
    except ImportError:
        return _fallback_encode(payload, settings.JWT_SECRET, settings.JWT_ALGORITHM)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        from jose import JWTError, jwt
    except ImportError as exc:
        try:
            return _fallback_decode(token, settings.JWT_SECRET, [settings.JWT_ALGORITHM])
        except JWTDecodeError as fallback_exc:
            raise fallback_exc from exc
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise JWTDecodeError(str(exc)) from exc


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict | None:
    if not credentials:
        return None
    try:
        return decode_access_token(credentials.credentials)
    except JWTDecodeError:
        return None


async def require_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        return decode_access_token(credentials.credentials)
    except JWTDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
