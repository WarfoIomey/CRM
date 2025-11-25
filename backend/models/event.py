from fastapi import HTTPException
from sqlalchemy import event, select

from .core import UserModel
from .crm import ContactModel, DealModel


@event.listens_for(ContactModel, "before_delete")
def prevent_contact_delete_if_deals(mapper, connection, target):
    has_deal = connection.execute(
        select(DealModel.id).where(DealModel.contact_id == target.id).limit(1)
    ).fetchone()
    if has_deal:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить контакт — к нему привязаны сделки."
        )


@event.listens_for(UserModel, "before_delete")
def prevent_user_delete_if_has_contacts_with_deals(mapper, connection, target):
    contacts = connection.execute(
        select(ContactModel.id).where(ContactModel.owner_id == target.id)
    ).fetchall()
    if not contacts:
        return
    contact_ids = [c[0] for c in contacts]
    has_deal = connection.execute(
        select(DealModel.id).where(DealModel.contact_id.in_(
            contact_ids
        )).limit(1)
    ).fetchone()
    if has_deal:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить пользователя — у его контактов есть сделки."
        )