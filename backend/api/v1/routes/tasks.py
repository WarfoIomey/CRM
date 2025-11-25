from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.dependencies import (
    get_db_session,
    get_current_user,
    get_organization_id,
    require_permission_dep
)
from api.v1.schemas.tasks_schemas import TasksSchema, TaskCreateSchema
from services.tasks_service import TaskService
from repositories.tasks_rep import TasksRepository
from models import OrganizationMemberModel
from models.constants import Permission


router = APIRouter(prefix="/tasks", tags=["Задачи"])


@router.get(
    "/",
    response_model=list[TasksSchema],
    summary="Получение задач",
)
async def get_user_tasks(
    current_user=Depends(get_current_user),
    organization_id: int = Depends(get_organization_id),
    member: OrganizationMemberModel = Depends(
        require_permission_dep(Permission.READ_TASK)
    ),
    db: AsyncSession = Depends(get_db_session),
    deal_id: Optional[int] = None,
    only_open: Optional[bool] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
):
    """Получить задачи сделок организации."""
    task_repo = TasksRepository(db)
    task_service = TaskService(task_repo)
    return await task_service.get_tasks(
        organization_id=organization_id,
        deal_id=deal_id,
        only_open=only_open,
        due_before=due_before,
        due_after=due_after
    )


@router.post(
    "/",
    response_model=TasksSchema,
    summary="Создание задачи",
    )
async def create_task(
    body: TaskCreateSchema,
    current_user=Depends(get_current_user),
    organization_id: int = Depends(get_organization_id),
    member: OrganizationMemberModel = Depends(
        require_permission_dep(Permission.WRITE_TASK)
    ),
    db: AsyncSession = Depends(get_db_session),
):
    """Создать сделку."""
    task_repo = TasksRepository(db)
    task_service = TaskService(task_repo)
    return await task_service.create_task(
        deal_id=body.deal_id,
        title=body.title,
        description=body.description,
        due_date=body.due_date,
        organization_id=organization_id,
        user_role=member.role,
        user_id=current_user.id,
    )
