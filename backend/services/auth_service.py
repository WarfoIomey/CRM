from datetime import datetime, timedelta
import secrets
from typing import Optional, Tuple

from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.config import settings
from models import UserModel
from repositories.user_rep import UserRepository
from repositories.organization_rep import OrganizationRepository
from repositories.refresh_token_rep import RefreshTokenRepository


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.org_repo = OrganizationRepository(session)
        self.refresh_repo = RefreshTokenRepository(session)

    async def register_user(
        self, email: str, password: str, name: str, organization_name: str
    ) -> tuple[UserModel, str]:
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError("Пользователь с таким email уже существует")
        existing_org = await self.org_repo.get_by_name(organization_name)
        if existing_org:
            raise ValueError(f"Организация с названием '{organization_name}' уже существует")
        user = await self.user_repo.create_user(email, password, name)
        await self.org_repo.create_organization(organization_name, user)
        refresh_token = await self.create_refresh_token(user.id)
        return user, refresh_token

    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Optional[UserModel]:
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        if not user.check_password(password):
            return None
        return user

    def create_access_token(self, user_id: int) -> str:
        expire = datetime.now() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {"sub": str(user_id), "exp": expire}
        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return token

    async def create_refresh_token(self, user_id: int) -> str:
        await self.refresh_repo.delete_by_user(user_id)
        token = secrets.token_urlsafe(64)
        expires = datetime.now() + timedelta(days=30)
        await self.refresh_repo.create_token(user_id, token, expires)
        return token

    async def refresh_access_token(
        self,
        refresh_token: str
    ) -> Tuple[str, str]:
        stored = await self.refresh_repo.get_valid(refresh_token)
        if not stored or stored.expires_at < datetime.now():
            raise ValueError("Refresh token is invalid or expired")
        stored.revoked = True
        await self.session.commit()
        refresh = await self.create_refresh_token(stored.user_id)
        return (self.create_access_token(stored.user_id), refresh)
