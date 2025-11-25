from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

from models.constants import ActivityType


class ActivitiesSchema(BaseModel):
    """Схема активности сделки."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True
    )

    id: int = Field(..., title="ID активности")
    deal_id: int = Field(..., title="ID сделки")
    author_id: int = Field(..., title="ID Автора сделки")
    type:  ActivityType = Field(
        ...,
        title="Тип активности"
    )
    payload: dict | None = Field(..., title="Данные")
    created_at: datetime = Field(..., title="Дата и время создания сделки")
    

class ActivityCreateSchema(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
    )

    type: Literal[ActivityType.COMMENT]
    payload: dict
