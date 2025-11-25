from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.core import RefreshTokenModel


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def delete_by_user(self, user_id: int):
        await self.session.execute(
            delete(RefreshTokenModel).where(
                RefreshTokenModel.user_id == user_id
            )
        )
        await self.session.commit()

    async def create_token(
        self,
        user_id: int,
        token: str,
        expires_at: datetime
    ):
        refresh = RefreshTokenModel(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            revoked=False
        )
        self.session.add(refresh)
        await self.session.commit()
        return refresh

    async def get_valid(self, token: str):
        result = await self.session.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.token == token,
                RefreshTokenModel.revoked == False,
                RefreshTokenModel.expires_at > datetime.utcnow()
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, token: str):
        obj = await self.get_valid(token)
        if not obj:
            return
        obj.revoked = True
        await self.session.commit()
