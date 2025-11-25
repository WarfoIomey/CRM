from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.dependencies import get_db_session
from services.auth_service import AuthService
from api.v1.schemas.auth_schemas import (
    AuthRegisterSchema,
    AuthLoginSchema,
    RefreshTokenSchema,
    TokenSchema
)


router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post(
    "/register",
    response_model=TokenSchema,
    summary='Регистрация',
)
async def register(
    data: AuthRegisterSchema,
    session: AsyncSession = Depends(get_db_session)
):
    auth_service = AuthService(session)
    try:
        user, refresh_token = await auth_service.register_user(
            email=data.email,
            password=data.password,
            name=data.name,
            organization_name=data.organization_name
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    access_token = auth_service.create_access_token(user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post(
    "/refresh",
    response_model=TokenSchema,
    summary='Обновление токена'
)
async def refresh_token(
    data: RefreshTokenSchema,
    session: AsyncSession = Depends(get_db_session)
):
    auth_service = AuthService(session)
    try:
        access, refresh = await auth_service.refresh_access_token(
            data.refresh_token
        )
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer"
        }
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post(
    "/login",
    response_model=TokenSchema,
    summary='Авторизация'
)
async def login(
    data: AuthLoginSchema,
    session: AsyncSession = Depends(get_db_session)
):
    auth_service = AuthService(session)
    user = await auth_service.authenticate_user(data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    access = auth_service.create_access_token(user.id)
    refresh = await auth_service.create_refresh_token(user.id)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer"
    }
