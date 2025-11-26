from datetime import datetime
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    constr,
    EmailStr
)


class ContactsSchema(BaseModel):
    """Схема контактов."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True
    )

    id: int = Field(..., title="ID контакта")
    owner_id: int = Field(..., title="ID владельца контакта")
    organization_id: int = Field(..., title="ID организации")
    name: str = Field(..., title="Имя контакта")
    email: str = Field(..., title="Email контакта")
    phone: str = Field(..., title="Телефон контакта")
    created_at: datetime = Field(..., title="Дата и время создания контакта")


class ContactCreateSchema(BaseModel):
    """Схема создания контакта."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    email: EmailStr
    phone: str = Field(..., min_length=1)
