from pydantic import BaseModel, EmailStr, Field
from pydantic import ConfigDict


class AuthRegisterSchema(BaseModel):
    """Схема для регистрации пользователя."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(
        ...,
        min_length=8,
        description="Пароль пользователя, минимум 8 символов"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Имя пользователя"
    )
    organization_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Название организации"
    )


class AuthLoginSchema(BaseModel):
    """Схема для аутентификации пользователя."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., description="Пароль пользователя")


class TokenSchema(BaseModel):
    """Схема для JWT токена."""

    model_config = ConfigDict(extra="forbid")

    access_token: str = Field(..., description="JWT токен доступа")
    refresh_token: str = Field(
        ...,
        description="JWT токен обновления, возвращается только при логине"
    )
    token_type: str = Field("bearer", description="Тип токена, обычно 'bearer'")


class RefreshTokenSchema(BaseModel):
    """Схема для обновления JWT токена."""

    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(..., description="JWT токен обновления")
