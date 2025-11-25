from typing import Sequence

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    ContactModel,
)


class ContactsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, contact: ContactModel) -> ContactModel:
        self.session.add(contact)
        await self.session.commit()
        await self.session.refresh(contact)
        return contact

    async def get_contacts_by_user(
        self,
        organization_id: int,
        user_id: int,
        search: str | None = None,
        owner_id: int | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> Sequence[ContactModel]:
        """Получить список контактов, в которых состоит пользователь."""
        query = select(ContactModel).where(
            ContactModel.organization_id == organization_id
        )
        if owner_id is not None:
            query = query.where(ContactModel.owner_id == owner_id)
        else:
            query = query.where(ContactModel.owner_id == user_id)
        if search:
            query = query.where(
                or_(
                    ContactModel.name.ilike(f"%{search}%"),
                    ContactModel.email.ilike(f"%{search}%"),
                )
            )
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
