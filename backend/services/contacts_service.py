from repositories.contacts_rep import ContactsRepository
from api.v1.schemas.contacts_schemas import ContactsSchema
from models import ContactModel, OrganizationMemberModel
from models.constants import MemberRole


class ContactService:
    """Сервис для работы с контактами."""

    def __init__(
        self,
        con_repo: ContactsRepository,
    ):
        self.con_repo = con_repo

    async def get_user_contacts(
        self,
        user_id: int,
        organization_id: int,
        member: OrganizationMemberModel,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        owner_id: int | None = None
    ) -> list[ContactsSchema]:
        """Получить организации, в которых состоит пользователь."""
        if member.role not in (
            MemberRole.OWNER,
            MemberRole.ADMIN,
            MemberRole.MANAGER
        ):
            owner_id = user_id
        contacts = await self.con_repo.get_contacts_by_user(
            organization_id=organization_id,
            user_id=user_id,
            search=search,
            owner_id=owner_id,
            limit=page_size,
            offset=(page - 1) * page_size
        )
        return [
            ContactsSchema(
                id=field.id,
                owner_id=field.owner_id,
                organization_id=field.organization_id,
                name=field.name,
                email=field.email,
                phone=field.phone,
                created_at=field.created_at,
            )
            for field in contacts
        ]

    async def create_contact(
        self,
        name: str,
        email: str,
        phone: str,
        current_user_id: int,
        organization_id: int,
    ) -> ContactsSchema:
        """Создать контакт."""
        contact = ContactModel(
            organization_id=organization_id,
            owner_id=current_user_id,
            name=name,
            email=email,
            phone=phone,
        )
        contact = await self.con_repo.create(contact)
        return ContactsSchema.model_validate(contact)
