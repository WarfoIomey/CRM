from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.dependencies import (
    get_db_session,
    get_current_user,
    get_organization_id,
    require_permission_dep
)
from services.deals_service import DealService
from repositories.deals_rep import DealsRepository
from models import OrganizationMemberModel
from models.constants import Permission


router = APIRouter(prefix="/analytics/deals", tags=["Аналитика"])


@router.get(
    "/summary",
    summary="Сводка по сделкам",
)
async def get_summary_of_deal(
    days: int = 30,
    current_user=Depends(get_current_user),
    organization_id: int = Depends(get_organization_id),
    member: OrganizationMemberModel = Depends(
        require_permission_dep(Permission.READ_ORGANIZATION)
    ),
    db: AsyncSession = Depends(get_db_session),
):
    deal_repo = DealsRepository(db)
    deal_service = DealService(deal_repo)
    return await deal_service.get_summary(
        organization_id=organization_id,
        days=days
    )


@router.get("/funnel", summary="Воронка продаж",)
async def get_deals_funnel(
    current_user=Depends(get_current_user),
    organization_id: int = Depends(get_organization_id),
    member: OrganizationMemberModel = Depends(
        require_permission_dep(Permission.READ_ORGANIZATION)
    ),
    db: AsyncSession = Depends(get_db_session),
):
    deal_repo = DealsRepository(db)
    deal_service = DealService(deal_repo)
    return await deal_service.get_funnel(
        organization_id=organization_id,
    )
