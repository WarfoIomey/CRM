from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.dependencies import (
    get_db_session,
    get_current_user,
    get_organization_id,
    require_permission_dep
)
from api.v1.schemas.contacts_schemas import ContactsSchema, ContactCreateSchema
from services.contacts_service import ContactService
from repositories.contacts_rep import ContactsRepository
from models import OrganizationMemberModel
from models.constants import Permission


router = APIRouter(prefix="/contacts", tags=["Контакты"])


@router.get(
    "/",
    response_model=list[ContactsSchema],
    summary="Получение контактов",
)
async def get_user_contacts(
    current_user=Depends(get_current_user),
    organization_id: int = Depends(get_organization_id),
    member: OrganizationMemberModel = Depends(
        require_permission_dep(Permission.READ_CONTACT)
    ),
    db: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    owner_id: int | None = Query(None)
):
    """Получить контакты организации, текущего пользователя."""
    contact_repo = ContactsRepository(db)
    contact_service = ContactService(contact_repo)
    return await contact_service.get_user_contacts(
        organization_id=organization_id,
        user_id=current_user.id,
        member=member,
        page=page,
        page_size=page_size,
        search=search,
        owner_id=owner_id
    )


@router.post(
    "/",
    response_model=ContactsSchema,
    summary="Создание контакта",
)
async def create_contact(
    body: ContactCreateSchema,
    current_user=Depends(get_current_user),
    organization_id: int = Depends(get_organization_id),
    member: OrganizationMemberModel = Depends(
        require_permission_dep(Permission.WRITE_CONTACT)
    ),
    db: AsyncSession = Depends(get_db_session),
):
    """Создать контакт."""
    contact_repo = ContactsRepository(db)
    contact_service = ContactService(contact_repo)
    return await contact_service.create_contact(
        name=body.name,
        email=body.email,
        phone=body.phone,
        current_user_id=current_user.id,
        organization_id=organization_id,
    )
