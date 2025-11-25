from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.dependencies import (
    get_db_session,
    get_current_user,
    get_organization_id,
    require_permission_dep
)
from repositories.organization_rep import OrganizationRepository
from repositories.member_rep import OrganizationMemberRepository
from models import OrganizationMemberModel
from models.constants import Permission
from services.organization_service import OrganizationService
from services.organization_member_service import OrganizationMemberService
from api.v1.schemas.organization_schemas import (
    OrganizationSchema,
    OrganizationMemberSchema
)


router = APIRouter(prefix="/organizations", tags=["Организации"])


@router.get(
    "/me",
    response_model=list[OrganizationSchema],
    summary="Список организаций",
)
async def get_user_organizations(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Возвращает список организаций в которых состоит текущий пользователь."""
    org_repo = OrganizationRepository(db)
    org_service = OrganizationService(org_repo)
    return await org_service.get_user_organizations(current_user.id)


@router.post(
    "/organization-members",
    response_model=OrganizationMemberSchema,
    summary="Добавление участника в организацию",
)
async def added_organization_member(
    body: OrganizationMemberSchema,
    organization_id: int = Depends(get_organization_id),
    member: OrganizationMemberModel = Depends(
        require_permission_dep(Permission.WRITE_ORG_SETTINGS)
    ),
    db: AsyncSession = Depends(get_db_session)
):
    """Добавляет пользователя в организацию."""
    org_member_repo = OrganizationMemberRepository(db)
    org_service = OrganizationMemberService(org_member_repo)
    return await org_service.add_member_to_organization(
        organization_id=organization_id,
        user_id=body.user_id,
        role=body.role
    )
