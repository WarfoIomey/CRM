from datetime import date
from typing import Optional

from fastapi import HTTPException
from repositories.tasks_rep import TasksRepository
from models.constants import MemberRole
from api.v1.schemas.tasks_schemas import TasksSchema


class TaskService:
    """Сервис для работы с задачами."""

    def __init__(
        self,
        task_repo: TasksRepository,
    ):
        self.task_repo = task_repo

    async def get_tasks(
        self,
        organization_id: int,
        deal_id: Optional[int] = None,
        only_open: Optional[bool] = None,
        due_before: Optional[date] = None,
        due_after: Optional[date] = None,
    ) -> list[TasksSchema]:
        """Получить задачи организации."""
        tasks = await self.task_repo.get_tasks(
            organization_id=organization_id,
            deal_id=deal_id,
            only_open=only_open,
            due_after=due_after,
            due_before=due_before,
        )
        return [TasksSchema.model_validate(t) for t in tasks]

    async def create_task(
        self,
        deal_id: int,
        title: str,
        description: str,
        due_date: date,
        organization_id: int,
        user_role: str,
        user_id: int,
    ) -> TasksSchema:
        """Создать сделку."""
        deal = await self.task_repo.get_deal_in_org(
            deal_id=deal_id,
            org_id=organization_id
        )
        if deal is None:
            raise HTTPException(400, "Deal not found in organization")
        if due_date < date.today():
            raise HTTPException(
                status_code=400,
                detail=f"Дата выполнения в прошлом: {due_date}"
            )
        if user_role == MemberRole.MEMBER:
            if deal.owner_id != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Вы не можете создавать задачи для чужой сделки"
                )
        if not title or not title.strip():
            raise HTTPException(
                status_code=400,
                detail="Название не может быть пустым"
            )

        if len(title) > 100:
            raise HTTPException(
                status_code=400,
                detail="Название не может превышать 100 символов"
            )

        if not description or not description.strip():
            raise HTTPException(
                status_code=400,
                detail="Описание не может быть пустым"
            )

        if len(description) > 300:
            raise HTTPException(
                status_code=400,
                detail="Длинна описание не может превышать 300 символов"
            )
        task = await self.task_repo.create({
            "deal_id": deal_id,
            "title": title,
            "description": description,
            "due_date": due_date
        })
        return TasksSchema.model_validate(task)
