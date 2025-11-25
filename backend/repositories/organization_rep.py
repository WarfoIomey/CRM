from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    OrganizationModel,
    OrganizationMemberModel,
    OrganizationMemberPermissionModel,
    UserModel
)
from models.core import MemberRole, Permission


class OrganizationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_organization(
        self,
        name: str,
        owner: UserModel
    ) -> OrganizationModel:
        """
        Создаёт организацию и добавляет владельца с ролью 'OWNER'.
        """
        org = OrganizationModel(name=name)
        self.session.add(org)
        await self.session.commit()
        await self.session.flush()
        membership = OrganizationMemberModel(
            user_id=owner.id,
            organization_id=org.id,
            role=MemberRole.OWNER
        )
        self.session.add(membership)
        await self.session.flush()
        permission = OrganizationMemberPermissionModel(
            member_id=membership.id,
            permission=Permission.ALL_PERMISSIONS,
        )
        self.session.add(permission)
        await self.session.commit()
        await self.session.refresh(org)
        await self.session.refresh(membership)
        await self.session.refresh(permission)
        return org

    async def get_organizations_by_user(
        self,
        user_id: int
    ) -> Sequence[OrganizationModel]:
        """
        Возвращает список организаций, в которых состоит пользователь.
        """
        result = await self.session.execute(
            select(OrganizationModel)
            .join(OrganizationMemberModel)
            .where(OrganizationMemberModel.user_id == user_id)
        )
        return result.scalars().all()

    async def get_by_name(
        self,
        name: str
    ) -> OrganizationModel | None:
        """
        Возвращает организацию по названию.
        """
        result = await self.session.execute(
            select(OrganizationModel)
            .where(OrganizationModel.name == name)
        )
        return result.scalars().first()
