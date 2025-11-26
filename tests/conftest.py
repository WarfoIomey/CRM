from datetime import date
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from dotenv import load_dotenv

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)
from sqlalchemy.pool import NullPool

from models import (
    DealModel,
    OrganizationModel,
    OrganizationMemberModel,
    ContactModel
)
from models.constants import Currency, StageDeal, StatusDeal
from repositories.database import Base
from api.v1.router import api_router
from api.v1.dependencies import get_db_session
from services.auth_service import AuthService
from services.activity_service import ActivityService
from services.contacts_service import ContactService
from services.deals_service import DealService
from services.organization_member_service import OrganizationMemberService
from services.organization_service import OrganizationService
from services.tasks_service import TaskService
from repositories.activities_rep import ActivitiesRepository
from repositories.contacts_rep import ContactsRepository
from repositories.deals_rep import DealsRepository
from repositories.member_rep import OrganizationMemberRepository
from repositories.organization_rep import OrganizationRepository
from repositories.tasks_rep import TasksRepository


load_dotenv()

DB_HOST: str = os.getenv('DB_HOST', 'localhost')
DB_PORT: str = os.getenv('DB_PORT', '5432')
DB_USER: str = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS: str = os.getenv('POSTGRES_PASSWORD', 'password')
DB_NAME: str = os.getenv('POSTGRES_DB', 'crm_db_test')
DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASS}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """
    Создаёт отдельный engine для всех тестов и поднимает таблицы.
    После выполнения сессии — удаляет.
    """
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        poolclass=NullPool,
        future=True
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Создаёт чистую сессию для каждого теста.
    """

    async_session = async_sessionmaker(
        db_engine,
        expire_on_commit=False,
        autoflush=False,
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def test_app(db_session: AsyncSession):
    """
    Создаёт тестовое приложение FastAPI c зависимостью get_db_session.
    """
    app = FastAPI()
    app.include_router(api_router, prefix="/api")

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_session

    return app


@pytest_asyncio.fixture(scope="function")
async def async_client(test_app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def organization_rep(db_session: AsyncSession):
    """Возвращает экземпляр OrganizationRepository"""
    return OrganizationRepository(db_session)


@pytest_asyncio.fixture(scope="function")
async def organization_member_rep(db_session: AsyncSession):
    """Возвращает экземпляр OrganizationRepository"""
    return OrganizationMemberRepository(db_session)


@pytest_asyncio.fixture(scope="function")
async def activities_rep(db_session: AsyncSession):
    """Возвращает экземпляр ActivitiesRepository"""
    return ActivitiesRepository(db_session)


@pytest_asyncio.fixture(scope="function")
async def contacts_rep(db_session: AsyncSession):
    """Возвращает экземпляр ContactsRepository"""
    return ContactsRepository(db_session)


@pytest_asyncio.fixture(scope="function")
async def deals_rep(db_session: AsyncSession):
    """Возвращает экземпляр DealsRepository"""
    return DealsRepository(db_session)


@pytest_asyncio.fixture(scope="function")
async def tasks_rep(db_session: AsyncSession):
    """Возвращает экземпляр TasksRepository"""
    return TasksRepository(db_session)


@pytest_asyncio.fixture(scope='function')
async def auth_service(db_session: AsyncSession):
    """Возвращает экземпляр AuthService."""
    return AuthService(db_session)


@pytest_asyncio.fixture(scope='function')
async def organization_service(organization_rep):
    """Возвращает экземпляр OrganizationService."""
    return OrganizationService(organization_rep)


@pytest_asyncio.fixture(scope='function')
async def activity_service(activities_rep):
    """Возвращает экземпляр ActivityService."""
    return ActivityService(activities_rep)


@pytest_asyncio.fixture(scope='function')
async def contacts_service(contacts_rep):
    """Возвращает экземпляр ContactService."""
    return ContactService(contacts_rep)


@pytest_asyncio.fixture(scope='function')
async def deals_service(deals_rep):
    """Возвращает экземпляр DealService."""
    return DealService(deals_rep)


@pytest_asyncio.fixture(scope='function')
async def member_service(organization_member_rep):
    """Возвращает экземпляр OrganizationMemberService."""
    return OrganizationMemberService(organization_member_rep)


@pytest_asyncio.fixture(scope='function')
async def tasks_service(tasks_rep):
    """Возвращает экземпляр TaskService."""
    return TaskService(tasks_rep)


@pytest_asyncio.fixture(scope='function')
async def test_user(auth_service):
    """Создаёт и возвращает тестового пользователя."""
    email = "test_user@example.com"
    password = "password123"
    name = "Test User"
    organization_name = "TestOrg"

    user, refresh_token = await auth_service.register_user(
        email=email,
        password=password,
        name=name,
        organization_name=organization_name
    )
    return user


@pytest.fixture(scope="function")
def access_token_test_user(test_user, auth_service):
    token = auth_service.create_access_token(
        user_id=test_user.id
    )
    return token


@pytest_asyncio.fixture(scope='function')
async def second_user(auth_service):
    """Создаёт второго пользователя для тестов."""
    email = "second_user@example.com"
    password = "password123"
    name = "Second User"
    organization_name = "SecondOrg"

    user, refresh_token = await auth_service.register_user(
        email=email,
        password=password,
        name=name,
        organization_name=organization_name
    )
    return user


@pytest.fixture(scope="function")
def access_token_second_user(second_user, auth_service):
    token = auth_service.create_access_token(
        user_id=second_user.id
    )
    return token


@pytest_asyncio.fixture(scope='function')
async def three_user(auth_service):
    """Создаёт третьего пользователя для тестов."""
    email = "three_user@example.com"
    password = "password123"
    name = "Three User"
    organization_name = "ThreeOrg"

    user, refresh_token = await auth_service.register_user(
        email=email,
        password=password,
        name=name,
        organization_name=organization_name
    )
    return user


@pytest_asyncio.fixture(scope='function')
async def ogranization_test_user(db_session, test_user):
    """Получить организацию первого пользователя."""
    result = await db_session.execute(
            select(OrganizationModel)
            .join(OrganizationMemberModel)
            .where(OrganizationMemberModel.user_id == test_user.id)
        )
    return result.scalars().first()


@pytest_asyncio.fixture(scope='function')
async def ogranization_second_user(db_session, test_user, second_user):
    """Получить организацию второго пользователя."""
    result = await db_session.execute(
            select(OrganizationModel)
            .join(OrganizationMemberModel)
            .where(OrganizationMemberModel.user_id == second_user.id)
        )
    return result.scalars().first()


@pytest_asyncio.fixture(scope="function")
async def get_member_test_user(
    organization_member_rep,
    test_user,
    ogranization_test_user
):
    return await organization_member_rep.get_member(
        organization_id=ogranization_test_user.id,
        user_id=test_user.id
    )


@pytest_asyncio.fixture(scope="function")
async def contact_by_test_user(
    test_user,
    ogranization_test_user,
    contacts_service
):
    """Создание контакта для тестов"""
    contact = await contacts_service.create_contact(
        organization_id=ogranization_test_user.id,
        current_user_id=test_user.id,
        name="John Doe",
        email="john.doe@example.com",
        phone="+123456789"
    )
    return contact


@pytest_asyncio.fixture(scope="function")
async def deal_by_test_user(
    test_user,
    ogranization_test_user,
    contact_by_test_user,
    deals_service
):
    deal = await deals_service.create_deal(
        contact_id=contact_by_test_user.id,
        title="John Doe",
        amount=1000.0,
        currency=Currency.USD,
        current_user_id=test_user.id,
        organization_id=ogranization_test_user.id
    )
    return deal


@pytest_asyncio.fixture(scope="function")
async def deal_amount_zero_by_test_user(
    test_user,
    ogranization_test_user,
    contact_by_test_user,
    deals_service
):
    deal = await deals_service.create_deal(
        contact_id=contact_by_test_user.id,
        title="John Doe 2",
        amount=0,
        currency=Currency.USD,
        current_user_id=test_user.id,
        organization_id=ogranization_test_user.id
    )
    return deal


@pytest_asyncio.fixture(scope="function")
async def up_stage_status_deal(
    test_user,
    ogranization_test_user,
    contact_by_test_user,
    deal_amount_zero_by_test_user,
    get_member_test_user,
    deals_service
):
    deal = await deals_service.update_deal(
        deal_id=deal_amount_zero_by_test_user.id,
        user_role=get_member_test_user.role,
        organization_id=ogranization_test_user.id,
        status=StatusDeal.IN_PROGRESS,
        stage=StageDeal.PROPOSAL,
        current_user_id=test_user.id,
    )
    return deal


@pytest_asyncio.fixture(scope="function")
async def contact_test_user(
    db_session,
    test_user,
    contact_by_test_user
):
    """Получить контакт первого пользователя."""
    result = await db_session.execute(
            select(ContactModel)
            .where(ContactModel.owner_id == test_user.id)
        )
    return result.scalars().first()


@pytest_asyncio.fixture(scope="function")
async def deal_test_user(
    db_session,
    test_user,
    deal_by_test_user
):
    """Получить сделку первого пользователя."""
    result = await db_session.execute(
            select(DealModel)
            .where(DealModel.owner_id == test_user.id)
        )
    return result.scalars().first()


@pytest_asyncio.fixture(scope="function")
async def task_test_user(
    test_user,
    ogranization_test_user,
    deal_by_test_user,
    get_member_test_user,
    tasks_service,
):
    task = await tasks_service.create_task(
        deal_id=deal_by_test_user.id,
        title="Call client",
        description="Discuss proposal details",
        due_date=date(2026, 1, 15),
        organization_id=ogranization_test_user.id,
        user_role=get_member_test_user.role,
        user_id=test_user.id,
    )
    return task


@pytest_asyncio.fixture(scope="function")
async def add_user_in_org(
    member_service,
    second_user,
    ogranization_test_user
):
    """Добавление участника в организацию."""
    member = await member_service.add_member_to_organization(
        ogranization_test_user.id,
        second_user.id
    )
    return member