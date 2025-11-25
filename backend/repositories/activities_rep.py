from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    ActivityModel
)


class ActivitiesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, activity: ActivityModel) -> ActivityModel:
        self.session.add(activity)
        await self.session.commit()
        await self.session.refresh(activity)
        return activity

    async def get_activities(
        self,
        organization_id: int,
        deal_id: int,
    ) -> Sequence[ActivityModel]:
        """Получить списка активностей сделки."""
        result = await self.session.execute(
            select(ActivityModel)
            .where(
                ActivityModel.deal_id == deal_id,
                ActivityModel.deal.has(organization_id=organization_id)
            )
        )
        return result.scalars().all()
