from datetime import datetime, timedelta
from typing import Optional, Sequence

from sqlalchemy import asc, desc, select, false, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    DealModel,
    ContactModel,
)
from models.constants import MemberRole, StatusDeal, StageDeal


class DealsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, deal: DealModel) -> DealModel:
        self.session.add(deal)
        await self.session.commit()
        await self.session.refresh(deal)
        return deal

    async def get_by_id(
        self,
        deal_id: int
    ) -> Optional[DealModel]:
        result = await self.session.execute(
            select(DealModel).where(
                DealModel.id == deal_id
            )
        )
        return result.scalar_one_or_none()

    async def update(self, deal: DealModel) -> DealModel:
        self.session.add(deal)
        await self.session.commit()
        await self.session.refresh(deal)
        return deal

    async def get_contact_in_org(self, contact_id: int, org_id: int):
        """Проверка, что контакт принадлежит организации."""
        result = await self.session.execute(
            select(ContactModel).where(
                ContactModel.id == contact_id,
                ContactModel.organization_id == org_id
            )
        )
        return result.scalar_one_or_none()

    async def get_deals(
        self,
        organization_id: int,
        user_id: int,
        page: int,
        page_size: int,
        status: Optional[list[str]],
        min_amount: Optional[float],
        max_amount: Optional[float],
        stage: Optional[str],
        owner_id: Optional[int],
        order_by: str,
        order: str,
        user_role: str,
    ) -> Sequence[DealModel]:
        """Получить список сделок, в которых состоит пользователь."""
        stmt = select(DealModel).where(
            DealModel.organization_id == organization_id
        )
        if user_role == MemberRole.MEMBER:
            stmt = stmt.where(DealModel.owner_id == user_id)
        else:
            if owner_id:
                stmt = stmt.where(DealModel.owner_id == owner_id)
        if status:
            try:
                parsed_status = [StatusDeal(s) for s in status]
                stmt = stmt.where(DealModel.status.in_(parsed_status))
            except ValueError:
                stmt = stmt.where(false())
        if min_amount is not None:
            stmt = stmt.where(DealModel.amount >= min_amount)
        if max_amount is not None:
            stmt = stmt.where(DealModel.amount <= max_amount)
        if stage:
            try:
                parsed_stage = StageDeal(stage)
                stmt = stmt.where(DealModel.stage == parsed_stage)
            except ValueError:
                stmt = stmt.where(false())
        order_column = getattr(DealModel, order_by, DealModel.created_at)
        stmt = stmt.order_by(
            desc(order_column) if order == "desc" else asc(order_column)
        )
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_summary(self, organization_id: int, days: int = 30):
        """Получить сводку по сделкам для организации."""
        now = datetime.now()
        since_date = now - timedelta(days=days)
        stmt_status = (
            select(
                DealModel.status,
                func.count(DealModel.id).label("count"),
                func.sum(DealModel.amount).label("total")
            )
            .where(DealModel.organization_id == organization_id)
            .group_by(DealModel.status)
        )
        result_status = await self.session.execute(stmt_status)
        status_summary = [
            {
                "status": row.status.value,
                "count": row.count,
                "total": float(row.total or 0)
            }
            for row in result_status
        ]
        stmt_avg_won = (
            select(func.avg(DealModel.amount))
            .where(
                DealModel.organization_id == organization_id,
                DealModel.status == StatusDeal.WON
            )
        )
        result_avg_won = await self.session.execute(stmt_avg_won)
        avg_won = float(result_avg_won.scalar() or 0)
        stmt_new = (
            select(func.count(DealModel.id))
            .where(
                DealModel.organization_id == organization_id,
                DealModel.created_at >= since_date
            )
        )
        result_new = await self.session.execute(stmt_new)
        new_count = result_new.scalar() or 0
        return {
            "status_summary": status_summary,
            "avg_won_amount": avg_won,
            "new_deals_last_days": new_count
        }

    async def get_funnel(self, organization_id: int):
        """
        Возвращает данные для воронки продаж:
        - количество сделок по стадиям и статусам
        - конверсия между стадиями
        """
        stmt = (
            select(
                DealModel.stage,
                DealModel.status,
                func.count(DealModel.id).label("count")
            )
            .where(DealModel.organization_id == organization_id)
            .group_by(DealModel.stage, DealModel.status)
        )
        result = await self.session.execute(stmt)
        funnel_data: dict[str, dict[str, int]] = {}
        for row in result:
            stage = row.stage.value
            status = row.status.value
            funnel_data.setdefault(stage, {})[status] = row.count
        stages_order = [
            "qualification",
            "proposal",
            "negotiation",
            "closed"
        ]

        conversion: dict[str, float | None] = {}

        for i in range(1, len(stages_order)):
            prev_stage = stages_order[i - 1]
            curr_stage = stages_order[i]

            prev_count = sum(funnel_data.get(prev_stage, {}).values())
            curr_count = sum(funnel_data.get(curr_stage, {}).values())

            if prev_count > 0:
                conversion[curr_stage] = round(
                    curr_count / prev_count * 100,
                    2
                )
            else:
                conversion[curr_stage] = None

        return {"funnel": funnel_data, "conversion": conversion}
