
from models import ActivityModel
from models.constants import ActivityType
from repositories.activities_rep import ActivitiesRepository
from api.v1.schemas.activities_schemas import ActivitiesSchema


class ActivityService:
    """Сервис для работы с активностями."""

    def __init__(
        self,
        activity_repo: ActivitiesRepository,
    ):
        self.activity_repo = activity_repo

    async def get_activities_deal(
        self,
        deal_id: int,
        organization_id: int,
    ) -> list[ActivitiesSchema]:
        """Получить активности сделки."""
        activities = await self.activity_repo.get_activities(
            organization_id=organization_id,
            deal_id=deal_id
        )
        return [
            ActivitiesSchema.model_validate(act) for act in activities
            ]

    async def create_activity(
        self,
        deal_id: int,
        type: ActivityType,
        payload: dict,
        author_id: int | None = None
    ) -> ActivitiesSchema:
        """Создание активности."""
        activity = await self.activity_repo.create(
            ActivityModel(
                deal_id=deal_id,
                type=type,
                payload=payload,
                author_id=author_id
            )
        )
        return ActivitiesSchema.model_validate(activity)

    async def create_activity_comment(
        self,
        deal_id: int,
        payload: dict,
        author_id: int
    ) -> ActivitiesSchema:
        """Создать активность с типом comment."""
        activity = ActivityModel(
            deal_id=deal_id,
            type=ActivityType.COMMENT,
            payload=payload,
            author_id=author_id
        )
        activity = await self.activity_repo.create(activity)
        return ActivitiesSchema.model_validate(activity)
