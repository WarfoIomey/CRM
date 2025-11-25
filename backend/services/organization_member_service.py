from fastapi import HTTPException
from repositories.member_rep import OrganizationMemberRepository
from api.v1.schemas.organization_schemas import (
    OrganizationMemberSchema
)
from models import OrganizationMemberModel, UserModel
from models.constants import MemberRole


class OrganizationMemberService:
    """Сервис для работы."""

    def __init__(self, org_repo: OrganizationMemberRepository):
        self.org_repo = org_repo

    async def add_member_to_organization(
        self,
        organization_id: int,
        user_id: int,
        role: str = MemberRole.MEMBER,
    ) -> OrganizationMemberSchema:
        """Добавить участника в организацию."""
        user = await self.org_repo.session.get(UserModel, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f'Пользователь с id={user_id} не найден'
            )
        existing_member = await self.org_repo.get_member(
            user_id,
            organization_id
        )
        if existing_member:
            raise HTTPException(
                status_code=400,
                detail='Участник уже состоит в организации'
            )
        member = OrganizationMemberModel(
            user_id=user_id,
            organization_id=organization_id,
            role=role
        )
        member = await self.org_repo.create(member)
        return OrganizationMemberSchema.model_validate(member)
