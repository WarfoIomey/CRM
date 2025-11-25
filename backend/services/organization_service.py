from repositories.organization_rep import OrganizationRepository
from api.v1.schemas.organization_schemas import (
    OrganizationSchema,
)


class OrganizationService:
    """Сервис для работы с организациями."""

    def __init__(self, org_repo: OrganizationRepository):
        self.org_repo = org_repo

    async def get_user_organizations(
        self,
        user_id: int
    ) -> list[OrganizationSchema]:
        """Получить организации, в которых состоит пользователь."""
        organizations = await self.org_repo.get_organizations_by_user(user_id)
        return [
            OrganizationSchema.model_validate(org) for org in organizations
        ]
