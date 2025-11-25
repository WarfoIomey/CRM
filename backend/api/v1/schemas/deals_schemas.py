from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from models.constants import Currency, StageDeal, StatusDeal


class DealsSchema(BaseModel):
    """Схема сделок."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True
    )

    id: int = Field(..., title="ID сделки")
    owner_id: int = Field(..., title="ID владельца сделки")
    organization_id: int = Field(..., title="ID организации")
    contact_id: int = Field(..., title="ID контакта")
    title: str = Field(..., title="Название сделки")
    amount: float = Field(..., title="Сумма сделки")
    currency: Currency = Field(
        ...,
        title="Валюта"
    )
    status: StatusDeal = Field(..., title="Статус сделки")
    stage: StageDeal = Field(..., title="Стадия сделки")
    created_at: datetime = Field(..., title="Дата и время создания сделки")
    updated_at: datetime = Field(..., title="Дата и время изменения сделки")


class DealCreateSchema(BaseModel):
    """Схема для создания сделки."""

    model_config = ConfigDict(extra="forbid")

    contact_id: int
    title: str
    amount: float
    currency: Currency


class DealUpdateSchema(BaseModel):
    """Схема для обновления сделки."""

    model_config = ConfigDict(extra="forbid")

    status: Optional[StatusDeal] = None
    stage: Optional[StageDeal] = None
