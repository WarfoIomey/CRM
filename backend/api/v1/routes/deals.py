from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.dependencies import (
    get_db_session,
    get_current_user,
    get_organization_id,
    require_permission_dep
)
from api.v1.schemas.activities_schemas import (
    ActivitiesSchema,
    ActivityCreateSchema
)
from api.v1.schemas.deals_schemas import (
    DealsSchema,
    DealCreateSchema,
    DealUpdateSchema
)
from services.activity_service import ActivityService
from services.deals_service import DealService
from repositories.activities_rep import ActivitiesRepository
from repositories.deals_rep import DealsRepository
from models import OrganizationMemberModel
from models.constants import Permission


router = APIRouter(prefix="/deals", tags=["Сделки"])


@router.get(
    "/",
    response_model=list[DealsSchema],
    summary="Получение сделок",
)
async def get_user_deals(
    current_user=Depends(get_current_user),
    organization_id: int = Depends(get_organization_id),
    member: OrganizationMemberModel = Depends(
        require_permission_dep(Permission.READ_DEAL)
    ),
    db: AsyncSession = Depends(get_db_session),
    page: int = 1,
    page_size: int = 20,
    status: Optional[list[str]] = Query(None),
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    stage: Optional[str] = None,
    owner_id: Optional[int] = None,
    order_by: str = "created_at",
    order: str = "desc"
):
    """Получить сделки организации, текущего пользователя."""
    deal_repo = DealsRepository(db)
    deal_service = DealService(deal_repo)
    return await deal_service.get_user_deals(
        user_id=current_user.id,
        organization_id=organization_id,
        page=page,
        page_size=page_size,
        status=status,
        min_amount=min_amount,
        max_amount=max_amount,
        stage=stage,
        owner_id=owner_id,
        order_by=order_by,
        order=order,
        user_role=member.role,
    )


@router.post(
    "/",
    response_model=DealsSchema,
    summary="Создание сделки",
)
async def create_deal(
    body: DealCreateSchema,
    current_user=Depends(get_current_user),
    organization_id: int = Depends(get_organization_id),
    member: OrganizationMemberModel = Depends(
        require_permission_dep(Permission.WRITE_DEAL)
    ),
    db: AsyncSession = Depends(get_db_session),
):
    """Создать сделку."""
    deal_repo = DealsRepository(db)
    deal_service = DealService(deal_repo)
    return await deal_service.create_deal(
        contact_id=body.contact_id,
        title=body.title,
        amount=body.amount,
        currency=body.currency,
        current_user_id=current_user.id,
        organization_id=organization_id,
    )


@router.patch(
    "/{deal_id}",
    response_model=DealsSchema,
    summary="Частичное изменение сделки",
)
async def update_deal(
    deal_id: int,
    body: DealUpdateSchema,
    current_user=Depends(get_current_user),
    organization_id: int = Depends(get_organization_id),
    member: OrganizationMemberModel = Depends(
        require_permission_dep(Permission.WRITE_DEAL)
    ),
    db: AsyncSession = Depends(get_db_session),
):
    """Частичное обновление сделки."""
    deal_repo = DealsRepository(db)
    activity_service = ActivityService(ActivitiesRepository(db))
    deal_service = DealService(deal_repo, activity_service)
    return await deal_service.update_deal(
        deal_id=deal_id,
        status=body.status,
        stage=body.stage,
        user_role=member.role,
        organization_id=organization_id,
        current_user_id=current_user.id
    )


@router.get(
    "/{deal_id}/activities",
    response_model=list[ActivitiesSchema],
    summary="Получение активностей сделки",
)
async def get_activities(
    deal_id: int,
    current_user=Depends(get_current_user),
    organization_id: int = Depends(get_organization_id),
    member: OrganizationMemberModel = Depends(
        require_permission_dep(Permission.READ_ACTIVITY)
    ),
    db: AsyncSession = Depends(get_db_session),
):
    activity_repo = ActivitiesRepository(db)
    activity_service = ActivityService(activity_repo)
    return await activity_service.get_activities_deal(
        deal_id=deal_id,
        organization_id=organization_id
    )


@router.post(
    "/{deal_id}/activities",
    response_model=ActivitiesSchema,
    summary="Создание активности по сделки",
)
async def create_activity(
    deal_id: int,
    activity_in: ActivityCreateSchema,
    current_user=Depends(get_current_user),
    organization_id: int = Depends(get_organization_id),
    member: OrganizationMemberModel = Depends(
        require_permission_dep(Permission.WRITE_ACTIVITY)
    ),
    db: AsyncSession = Depends(get_db_session),
):
    activity_repo = ActivitiesRepository(db)
    activity_service = ActivityService(activity_repo)
    if activity_in.type != "comment":
        raise HTTPException(
            status_code=400,
            detail="Only 'comment' type is allowed"
        )
    return await activity_service.create_activity_comment(
        deal_id=deal_id,
        payload=activity_in.payload,
        author_id=current_user.id
    )
