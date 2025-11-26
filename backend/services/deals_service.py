from typing import Optional

from fastapi import HTTPException
from services.activity_service import ActivityService
from models import DealModel
from models.constants import (
    MemberRole,
    StageDeal,
    StatusDeal
)
from repositories.deals_rep import DealsRepository
from api.v1.schemas.deals_schemas import DealsSchema


class DealService:
    """Сервис для работы с сделками."""

    def __init__(
        self,
        deal_repo: DealsRepository,
        activity_service: Optional[ActivityService] = None
    ):
        self.deal_repo = deal_repo
        self.activity_service = activity_service

    async def get_user_deals(
        self,
        user_id: int,
        organization_id: int,
        page: int,
        page_size: int,
        order_by: str,
        order: str,
        user_role: str,
        status: Optional[list[str]] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        stage: Optional[str] = None,
        owner_id: Optional[int] = None,
    ) -> list[DealsSchema]:
        """Получить сделки, в которых состоит пользователь."""
        deals = await self.deal_repo.get_deals(
            organization_id=organization_id,
            user_id=user_id,
            page=page,
            page_size=page_size,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            stage=stage,
            owner_id=owner_id,
            order_by=order_by,
            order=order,
            user_role=user_role,
        )
        return [DealsSchema.model_validate(deal) for deal in deals]

    async def create_deal(
        self,
        contact_id: int,
        title: str,
        amount: float,
        currency: str,
        current_user_id: int,
        organization_id: int,
    ) -> DealsSchema:
        """Создать сделку."""
        contact = await self.deal_repo.get_contact_in_org(
            contact_id,
            organization_id
        )
        if contact is None:
            raise HTTPException(
                status_code=400,
                detail="Contact does not belong to this organization"
            )
        deal = DealModel(
            organization_id=organization_id,
            owner_id=current_user_id,
            contact_id=contact_id,
            title=title,
            amount=amount,
            currency=currency,
            status=StatusDeal.NEW,
            stage=StageDeal.QUALIFICATION
        )
        deal = await self.deal_repo.create(deal)
        return DealsSchema.model_validate(deal)

    async def update_deal(
        self,
        deal_id: int,
        user_role: str,
        organization_id: int,
        status: Optional[StatusDeal] = None,
        stage: Optional[StageDeal] = None,
        current_user_id: Optional[int] = None,
    ) -> DealsSchema:
        """Частичное обновление сделки."""
        deal = await self.deal_repo.get_by_id(deal_id)
        if not deal or deal.organization_id != organization_id:
            raise HTTPException(404, "Deal not found in organization")
        activities_to_create = []
        try:
            if status is not None and status != deal.status:
                act_type, payload = deal.status.get_activity_change(status)
                deal.status = status
                activities_to_create.append({
                    "type": act_type,
                    "payload": payload
                })
        except ValueError as e:
            raise HTTPException(400, str(e))
        if stage is not None and stage != deal.stage:
            if stage == StageDeal.CLOSED and deal.amount <= 0:
                raise HTTPException(400, "Cannot close deal with amount <= 0")
            if user_role == MemberRole.MEMBER:
                stages_order = [
                    StageDeal.QUALIFICATION,
                    StageDeal.PROPOSAL,
                    StageDeal.NEGOTIATION,
                    StageDeal.CLOSED
                ]
                current_index = stages_order.index(deal.stage)
                new_index = stages_order.index(stage)
                if new_index < current_index:
                    raise HTTPException(
                        403,
                        "Member cannot move stage backward"
                    )
                activity_type, payload = deal.stage.get_activity_change(stage)
                deal.stage = stage
                activities_to_create.append({
                    "type": activity_type,
                    "payload": payload
                })
            deal.stage = stage
        deal = await self.deal_repo.update(deal)
        for act in activities_to_create:
            if self.activity_service is not None:
                await self.activity_service.create_activity(
                    deal_id=deal.id,
                    type=act["type"],
                    payload=act["payload"],
                    author_id=current_user_id
                )
        return DealsSchema.model_validate(deal)

    async def get_summary(self, organization_id: int, days: int = 30):
        return await self.deal_repo.get_summary(organization_id, days)

    async def get_funnel(self, organization_id: int):
        return await self.deal_repo.get_funnel(organization_id)
