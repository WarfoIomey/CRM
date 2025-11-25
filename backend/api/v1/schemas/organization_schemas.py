from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from models.constants import MemberRole


class OrganizationSchema(BaseModel):
    """Схема списка организаций, в которых состоит текущий пользователь."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True
    )

    id: int = Field(..., title="ID организации")
    name: str = Field(..., title="Название организации")
    created_at: datetime = Field(..., title="Дата и время создания организации")


class OrganizationMemberSchema(BaseModel):
    """Схема участника организации."""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True
    )

    user_id: int = Field(..., description="ID пользователя")
    role: str = Field(
        default=MemberRole.MEMBER,
        title="Роль участника в организации"
    )
