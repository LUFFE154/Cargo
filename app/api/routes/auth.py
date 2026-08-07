from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_auth_service, get_current_token
from app.api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.application.auth_service import AuthService
from app.application.exceptions import AuthenticationError, ConflictError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    try:
        result = await auth_service.register(
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
        )
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return TokenResponse(access_token=result.access_token, token_type=result.token_type)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, auth_service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    try:
        result = await auth_service.login(email=payload.email, password=payload.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=result.access_token, token_type=result.token_type)


@router.get("/me")
async def me(token: str = Depends(get_current_token), auth_service: AuthService = Depends(get_auth_service)) -> dict[str, str | bool]:
    user = await auth_service.get_current_user(token)
    return {"user_id": str(user.user_id), "email": user.email, "is_admin": user.is_admin}
