from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import OrganizationMemberModel
from models.constants import MemberRole, Permission


class OrganizationMemberRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        member: OrganizationMemberModel
    ) -> OrganizationMemberModel:
        self.session.add(member)
        await self.session.commit()
        await self.session.refresh(member)
        return member

    async def get_member(
        self,
        user_id: int,
        organization_id: int
    ) -> OrganizationMemberModel | None:
        """Возвращает членство пользователя в организации."""
        result = await self.session.execute(
            select(OrganizationMemberModel)
            .where(OrganizationMemberModel.user_id == user_id)
            .where(OrganizationMemberModel.organization_id == organization_id)
        )
        return result.scalars().first()

    async def check_permission(
        self,
        member: OrganizationMemberModel,
        permission: Permission,
        obj_owner_id: int | None = None
    ) -> bool:
        """
        Проверяет, имеет ли член организации право на действие.

        Правила:
        - OWNER и ADMIN — полный доступ.
        - MANAGER — полный доступ, кроме WRITE/READ_ORG_SETTINGS.
        - MEMBER — READ разрешено всем, WRITE/DELETE только для своих объектов.
        """
        if member.role in [MemberRole.OWNER, MemberRole.ADMIN]:
            return True

        if member.role == MemberRole.MANAGER:
            if permission in [
                Permission.WRITE_ORG_SETTINGS,
                Permission.READ_ORG_SETTINGS
            ]:
                return False
            return True

        if member.role == MemberRole.MEMBER:
            if permission.name.startswith("READ"):
                return True
            if obj_owner_id is None or obj_owner_id != member.user_id:
                return False
            allowed_permissions = {
                Permission.WRITE_CONTACT,
                Permission.WRITE_DEAL,
                Permission.WRITE_TASK,
            }
            return permission in allowed_permissions

        return False
