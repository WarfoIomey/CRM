from datetime import datetime
from typing import TYPE_CHECKING
import re

import bcrypt
from sqlalchemy import (
    DateTime,
    String,
    func,
    ForeignKey,
    Enum as SQLEnum,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from repositories.database import Base
from .constants import (
    MemberRole,
    Permission,
    LENGTH_NAME_ORGANIZATION,
    LENGTH_EMAIL,
    LENGTH_NAME_USER,
)

if TYPE_CHECKING:
    from .crm import ContactModel, DealModel, ActivityModel


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    token: Mapped[str] = mapped_column(nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    revoked: Mapped[bool] = mapped_column(default=False)

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="refresh_tokens"
    )


class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(LENGTH_EMAIL),
        unique=True,
        nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    name: Mapped[str] = mapped_column(
        String(LENGTH_NAME_USER),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    organization_memberships: Mapped[
        list['OrganizationMemberModel']
    ] = relationship(
        back_populates='user',
        cascade="all, delete-orphan"
    )

    contacts: Mapped[list['ContactModel']] = relationship(
        back_populates='owner',
    )

    deals: Mapped[list['DealModel']] = relationship(
        back_populates='owner',
        cascade="all, delete-orphan"
    )

    activities: Mapped[list['ActivityModel']] = relationship(
        back_populates='author',
        cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list['RefreshTokenModel']] = relationship(
        "RefreshTokenModel", back_populates="user"
    )

    def set_password(self, password: str):
        """Хеширование пароля."""
        salt = bcrypt.gensalt()
        self.hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            salt
        ).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Проверка пароля."""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.hashed_password.encode('utf-8')
        )

    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            raise ValueError("Invalid email format")
        return email


class OrganizationModel(Base):
    __tablename__ = 'organizations'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(LENGTH_NAME_ORGANIZATION),
        unique=True,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    members: Mapped[list['OrganizationMemberModel']] = relationship(
        back_populates='organization',
        cascade="all, delete-orphan"
    )

    contacts: Mapped[list['ContactModel']] = relationship(
        back_populates='organization',
        cascade="all, delete-orphan"
    )

    deals: Mapped[list['DealModel']] = relationship(
        back_populates='organization',
        cascade="all, delete-orphan"
    )


class OrganizationMemberModel(Base):
    __tablename__ = 'organization_members'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
    )
    role: Mapped[MemberRole] = mapped_column(
        SQLEnum(MemberRole),
        nullable=False
    )

    organization: Mapped['OrganizationModel'] = relationship(
        back_populates='members'
    )
    user: Mapped['UserModel'] = relationship(
        back_populates='organization_memberships'
    )
    permissions: Mapped[
        list['OrganizationMemberPermissionModel']
    ] = relationship(
        'OrganizationMemberPermissionModel',
        back_populates='member',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        UniqueConstraint(
            'organization_id',
            'user_id',
            name='uq_organization_user'
        ),
    )


class OrganizationMemberPermissionModel(Base):
    __tablename__ = 'organization_member_permissions'

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey('organization_members.id', ondelete='CASCADE'),
        nullable=False,
    )
    permission: Mapped[Permission] = mapped_column(
        SQLEnum(Permission),
        nullable=False
    )

    member: Mapped['OrganizationMemberModel'] = relationship(
        back_populates='permissions'
    )
