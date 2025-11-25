from typing import AsyncGenerator, Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.database import session_factory

from repositories.config import settings
from repositories.user_rep import UserRepository
from repositories.member_rep import OrganizationMemberRepository
from models import UserModel, OrganizationMemberModel
from models.constants import Permission


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db_session),
) -> UserModel:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный токен",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_organization_id(x_organization_id: int = Header(None)) -> int:
    if x_organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Отсутствует заголовок X-Organization-ID"
        )
    return x_organization_id


async def get_current_member(
    current_user: UserModel = Depends(get_current_user),
    organization_id: int = Depends(get_organization_id),
    db: AsyncSession = Depends(get_db_session),
) -> OrganizationMemberModel:
    """Возвращает объект участника организации."""
    repo = OrganizationMemberRepository(db)
    member = await repo.get_member(current_user.id, organization_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь участником этой организации."
        )
    return member


def require_permission_dep(permission: Permission):
    """Dependency для проверки прав доступа участника организации."""
    async def dependency(
        member: OrganizationMemberModel = Depends(get_current_member),
        db: AsyncSession = Depends(get_db_session),
        obj_owner_id: int | None = None
    ):
        repo = OrganizationMemberRepository(db)
        allowed = await repo.check_permission(member, permission, obj_owner_id)
        if not allowed:
            raise HTTPException(status_code=403, detail="Permission denied")
        return member
    return dependency
