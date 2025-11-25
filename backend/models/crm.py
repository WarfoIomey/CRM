from datetime import date, datetime
from typing import TYPE_CHECKING
import re

from sqlalchemy import (
    DateTime,
    Date,
    Index,
    String,
    Text,
    func,
    ForeignKey,
    Enum as SQLEnum,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.dialects.postgresql import JSONB

from repositories.database import Base
from .constants import (
    ActivityType,
    Currency,
    StatusDeal,
    StageDeal,
    LENGTH_EMAIL,
    LENGTH_NAME_USER,
    LENGTH_PHONE,
    LENGTH_TITLE_DEAL,
    LENGTH_TITLE_TASK,
)

if TYPE_CHECKING:
    from .core import UserModel, OrganizationModel


class ContactModel(Base):
    __tablename__ = 'contacts'

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey('organizations.id', ondelete='CASCADE'),
    )
    name: Mapped[str] = mapped_column(
        String(LENGTH_NAME_USER),
        nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(LENGTH_EMAIL),
        nullable=False
    )
    phone: Mapped[str] = mapped_column(String(LENGTH_PHONE), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    owner: Mapped['UserModel'] = relationship(
        'UserModel',
        foreign_keys=[owner_id]
    )
    organization: Mapped['OrganizationModel'] = relationship(
        'OrganizationModel'
    )
    deals: Mapped[list['DealModel']] = relationship(
        back_populates='contact',
    )

    __table_args__ = (
        UniqueConstraint(
            'organization_id',
            'email',
            name='uq_organization_contact_email'
        ),
        Index('ix_contacts_organization_name', 'organization_id', 'name'),
        Index('ix_contacts_organization_phone', 'organization_id', 'phone'),
    )

    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            raise ValueError("Invalid email format")
        return email


class DealModel(Base):
    __tablename__ = 'deals'

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
    )
    contact_id: Mapped[int] = mapped_column(
        ForeignKey('contacts.id'),
        nullable=False,
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(LENGTH_TITLE_DEAL),
        nullable=False
    )
    amount: Mapped[float] = mapped_column(nullable=False)
    currency: Mapped[Currency] = mapped_column(
        SQLEnum(Currency),
        nullable=False
    )
    status: Mapped[StatusDeal] = mapped_column(
        SQLEnum(StatusDeal),
        default=StatusDeal.NEW,
        nullable=False
    )
    stage: Mapped[StageDeal] = mapped_column(
        SQLEnum(StageDeal),
        default=StageDeal.QUALIFICATION,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    organization: Mapped['OrganizationModel'] = relationship(
        back_populates='deals'
    )
    contact: Mapped['ContactModel'] = relationship(back_populates='deals')
    owner: Mapped['UserModel'] = relationship(back_populates='deals')
    tasks: Mapped[list['TaskModel']] = relationship(
        back_populates='deal',
        cascade="all, delete-orphan"
    )
    activities: Mapped[list['ActivityModel']] = relationship(
        back_populates='deal',
        cascade="all, delete-orphan"
    )

    @validates('status')
    def validate_won_status(self, key, status):
        if status == StatusDeal.WON and self.amount <= 0:
            raise ValueError("Cannot close deal with status 'won' when amount <= 0")
        return status


class TaskModel(Base):
    __tablename__ = 'tasks'

    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[int] = mapped_column(
        ForeignKey('deals.id', ondelete='CASCADE'),
        nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(LENGTH_TITLE_TASK),
        nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=True)
    is_done: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    deal: Mapped['DealModel'] = relationship(
        'DealModel',
        back_populates='tasks'
    )

    __table_args__ = (
        Index('ix_tasks_deal_id', 'deal_id'),
        Index('ix_tasks_due_date', 'due_date'),
        Index('ix_tasks_is_done', 'is_done'),
    )

    def mark_done(self):
        """Пометить задачу как выполненную."""
        self.is_done = True


class ActivityModel(Base):
    __tablename__ = 'activities'

    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[int] = mapped_column(
        ForeignKey('deals.id', ondelete='CASCADE'),
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=True
    )
    type: Mapped[ActivityType] = mapped_column(
        SQLEnum(ActivityType),
        default=ActivityType.STATUS_CHANGE,
        nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=True) 
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    deal: Mapped['DealModel'] = relationship(
        'DealModel',
        back_populates='activities'
    )
    author: Mapped['UserModel'] = relationship(
        'UserModel',
        back_populates='activities'
    )
