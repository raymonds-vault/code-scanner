"""Google OAuth sign-in and JWT endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token, require_user
from app.core.config import get_settings
from app.core.dependencies import get_db
from app.repositories.user_repo import get_or_create_user

router = APIRouter(tags=["Auth"], prefix="/auth")


class GoogleTokenRequest(BaseModel):
    token: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/google", response_model=AuthResponse)
async def google_sign_in(
    body: GoogleTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    settings = get_settings()
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    def _verify_token() -> dict:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token
        return id_token.verify_oauth2_token(
            body.token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )

    try:
        info = await run_in_threadpool(_verify_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {exc}") from exc

    user = await get_or_create_user(
        db,
        google_id=info["sub"],
        email=info["email"],
        name=info.get("name", info["email"]),
        picture=info.get("picture"),
    )
    await db.commit()

    token = create_access_token(user.id, user.email, user.name)
    return AuthResponse(
        access_token=token,
        user={"id": user.id, "email": user.email, "name": user.name, "picture": user.picture},
    )


@router.get("/me")
async def get_me(current_user: dict = Depends(require_user)) -> dict:
    return current_user
