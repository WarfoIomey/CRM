from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict, field_validator


class TasksSchema(BaseModel):
    """Схема задач."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True
    )

    id: int = Field(..., title="ID задачи")
    deal_id: int = Field(..., title="ID сделки")
    title: str = Field(..., title="Название сделки")
    description: str = Field(..., title="Описание задачи")
    due_date: date = Field(..., title="Дата и время выполнения задачи")
    is_done: bool = Field(..., title="Статус задачи")
    created_at: datetime = Field(..., title="Дата и время создания сделки")


class TaskCreateSchema(BaseModel):
    """Схема создания задачи."""

    model_config = ConfigDict(
        extra="forbid"
    )

    deal_id: int
    title: str
    description: str
    due_date: date

    @field_validator("due_date")
    def check_due_date(cls, value):
        if value < date.today():
            raise ValueError("Дата завершения не может быть в прошлом")
        return value
