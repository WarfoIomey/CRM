from datetime import date
from typing import Sequence, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    TaskModel,
    DealModel,
)


class TasksRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> TaskModel:
        obj = TaskModel(**data)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_deal_in_org(self, deal_id: int, org_id: int):
        """Проверка, что сделка принадлежит организации."""
        result = await self.session.execute(
            select(DealModel).where(
                DealModel.id == deal_id,
                DealModel.organization_id == org_id
            )
        )
        return result.scalar_one_or_none()

    async def get_tasks(
        self,
        organization_id: int,
        deal_id: Optional[int] = None,
        only_open: Optional[bool] = None,
        due_before: Optional[date] = None,
        due_after: Optional[date] = None,
    ) -> Sequence[TaskModel]:
        """Получить список задач организации."""
        query = select(TaskModel).join(DealModel).where(
            DealModel.organization_id == organization_id
        )
        if deal_id:
            query = query.where(DealModel.id == deal_id)
        if only_open is True:
            query = query.where(TaskModel.is_done.is_(False))
        if due_after is not None:
            query = query.where(TaskModel.due_date >= due_after)
        if due_before is not None:
            query = query.where(TaskModel.due_date <= due_before)
        result = await self.session.execute(query)
        return result.scalars().all()
