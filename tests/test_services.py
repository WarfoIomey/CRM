from datetime import date

import pytest
from fastapi import HTTPException

from models.constants import Currency, StatusDeal, StageDeal, MemberRole


@pytest.mark.asyncio
async def test_register_user_success(auth_service):
    email = "unit_test@example.com"
    password = "testpassword"
    name = "Unit Test"
    organization_name = "UnitOrg"

    user, refresh_token = await auth_service.register_user(
        email=email,
        password=password,
        name=name,
        organization_name=organization_name
    )

    assert user.email == email
    assert user.check_password(password)
    assert isinstance(refresh_token, str)
    assert len(refresh_token) > 0


@pytest.mark.asyncio
async def test_register_user_existing_email(auth_service, test_user):
    with pytest.raises(ValueError) as exc:
        await auth_service.register_user(
            email=test_user.email,
            password="password",
            name="Dup User",
            organization_name="NewOrg"
        )
    assert "Пользователь с таким email уже существует" in str(exc.value)


@pytest.mark.asyncio
async def test_register_user_existing_organization(auth_service, test_user):
    with pytest.raises(ValueError) as exc:
        await auth_service.register_user(
            email="newuser@example.com",
            password="password",
            name="New User",
            organization_name="TestOrg"
        )
    assert "Организация с названием" in str(exc.value)


@pytest.mark.asyncio
async def test_authenticate_user(auth_service, test_user):
    user = await auth_service.authenticate_user(test_user.email, "password123")
    assert user is not None
    assert user.email == test_user.email
    user_wrong = await auth_service.authenticate_user(
        test_user.email,
        "wrongpassword"
    )
    assert user_wrong is None
    user_none = await auth_service.authenticate_user(
        "noemail@example.com",
        "pass"
    )
    assert user_none is None


@pytest.mark.asyncio
async def test_create_access_token(auth_service, test_user):
    token = auth_service.create_access_token(test_user.id)
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.asyncio
async def test_refresh_token_flow(auth_service, test_user):
    old_refresh = await auth_service.create_refresh_token(test_user.id)
    stored = await auth_service.refresh_repo.get_valid(old_refresh)
    assert stored is not None
    assert stored.user_id == test_user.id
    new_access, new_refresh = await auth_service.refresh_access_token(
        old_refresh
    )
    assert isinstance(new_access, str)
    assert isinstance(new_refresh, str)
    assert new_refresh != old_refresh
    old_stored = await auth_service.refresh_repo.get_valid(old_refresh)
    assert old_stored is None


@pytest.mark.asyncio
async def test_get_contacts(
    ogranization_test_user,
    contacts_service,
    contact_by_test_user,
    get_member_test_user,
    test_user
):
    """Тест на получение контакта."""
    contacts = await contacts_service.get_user_contacts(
        organization_id=ogranization_test_user.id,
        user_id=test_user.id,
        member=get_member_test_user
    )
    assert len(contacts) == 1


@pytest.mark.asyncio
async def test_create_contacts(
    ogranization_test_user,
    contacts_service,
    test_user
):
    """Тест на получение контакта."""
    contact = await contacts_service.create_contact(
        organization_id=ogranization_test_user.id,
        current_user_id=test_user.id,
        name="John Doe",
        email="john.doe@example.com",
        phone="+123456789"
    )
    assert contact.name == "John Doe"
    assert contact.email == "john.doe@example.com"
    assert contact.phone == "+123456789"
    assert contact.organization_id == ogranization_test_user.id
    assert contact.owner_id == test_user.id


@pytest.mark.asyncio
async def test_add_user_in_org(
    member_service,
    second_user,
    ogranization_test_user
):
    """Тест на добавления пользователя в организацию."""
    member = await member_service.add_member_to_organization(
        ogranization_test_user.id,
        second_user.id
    )
    assert member.user_id == second_user.id


@pytest.mark.asyncio
async def test_add_member_to_organization_already_exists(
    member_service,
    test_user,
    ogranization_test_user
):
    """Тест на добавления пользователя который уже в организации."""
    with pytest.raises(HTTPException) as exc:
        await member_service.add_member_to_organization(
            ogranization_test_user.id,
            test_user.id
        )
    assert exc.value.status_code == 400
    assert "Участник уже состоит в организации" in exc.value.detail


@pytest.mark.asyncio
async def test_get_organizations_by_user(
    organization_service,
    test_user,
    second_user
):
    """Тест на получение организаций."""
    orgs = await organization_service.get_user_organizations(test_user.id)
    assert len(orgs) == 1


@pytest.mark.asyncio
async def test_get_deals(
    deal_by_test_user,
    get_member_test_user,
    test_user,
    ogranization_test_user,
    deals_service,
):
    deals = await deals_service.get_user_deals(
        user_id=test_user.id,
        organization_id=ogranization_test_user.id,
        page=1,
        page_size=20,
        order="asc",
        order_by="created_at",
        user_role=get_member_test_user.role
    )
    assert len(deals) == 1


@pytest.mark.asyncio
async def test_creat_deal(
    test_user,
    ogranization_test_user,
    contact_test_user,
    deals_service,
):
    deal = await deals_service.create_deal(
        contact_id=contact_test_user.id,
        title="Website redesign",
        amount=10000.0,
        currency=Currency.EUR,
        current_user_id=test_user.id,
        organization_id=ogranization_test_user.id,
    )
    assert deal.title == "Website redesign"
    assert deal.contact_id == contact_test_user.id
    assert deal.amount == 10000.0
    assert deal.currency == Currency.EUR
    assert deal.owner_id == test_user.id
    assert deal.organization_id == ogranization_test_user.id


@pytest.mark.asyncio
async def test_update_deal(
    test_user,
    ogranization_test_user,
    deal_by_test_user,
    get_member_test_user,
    deals_service,
):
    """Тест на частичное обновление сделки."""
    deal = await deals_service.update_deal(
        deal_id=deal_by_test_user.id,
        user_role=get_member_test_user.role,
        organization_id=ogranization_test_user.id,
        status=StatusDeal.LOST,
        stage=StageDeal.CLOSED,
        current_user_id=test_user.id,
    )
    assert deal.status == StatusDeal.LOST
    assert deal.stage == StageDeal.CLOSED


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "current_user_id,org_id,role,expected_code,status,stage,err_msg",
    [
        (
            1,
            2,
            MemberRole.OWNER,
            404,
            None,
            None,
            "Deal not found in organization"
        ),
        (
            2,
            1,
            MemberRole.MEMBER,
            403,
            StatusDeal.NEW,
            StageDeal.QUALIFICATION,
            "Member cannot move stage backward"
        ),
        (
            1,
            1,
            MemberRole.OWNER,
            400,
            None,
            StageDeal.CLOSED,
            "Cannot close deal with amount <= 0"
        ),
    ]
)
async def test_update_deal_validation_failure(
    deals_service,
    up_stage_status_deal,
    org_id,
    expected_code,
    role,
    current_user_id,
    status,
    stage,
    err_msg,
):
    """
    Unit-тест проверяющий валидацию сервиса update_deal при разных ошибках.
    """
    with pytest.raises(HTTPException) as exc:
        await deals_service.update_deal(
            organization_id=org_id,
            deal_id=up_stage_status_deal.id,
            user_role=role,
            current_user_id=current_user_id,
            status=status,
            stage=stage,
        )
    assert exc.value.status_code == expected_code
    assert err_msg in str(exc.value.detail)


@pytest.mark.asyncio
async def test_summary_deal(
    test_user,
    ogranization_test_user,
    deal_by_test_user,
    deals_service,
):
    """Тест на получение сводки по сделке."""
    summary = await deals_service.get_summary(
        organization_id=ogranization_test_user.id,
        days=30
    )
    assert summary["status_summary"][0] == {
        'count': 1,
        'status': 'new',
        'total': 1000.0
    }
    assert summary["avg_won_amount"] == 0
    assert summary["new_deals_last_days"] == 1


@pytest.mark.asyncio
async def test_funnel_deal(
    test_user,
    ogranization_test_user,
    deal_by_test_user,
    deals_service,
):
    """Тест на получение воронки."""
    funnel = await deals_service.get_funnel(
        organization_id=ogranization_test_user.id,
    )
    assert funnel["funnel"]["qualification"]["new"] == 1


@pytest.mark.asyncio
async def test_get_task(
    ogranization_test_user,
    deal_by_test_user,
    task_test_user,
    tasks_service,
):
    """Тест на получение задач по сделке."""
    tasks = await tasks_service.get_tasks(
        organization_id=ogranization_test_user.id,
        deal_id=deal_by_test_user.id
    )
    assert len(tasks) == 1


@pytest.mark.asyncio
async def test_creat_task(
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
    assert task.title == "Call client"
    assert task.description == "Discuss proposal details"
    assert task.due_date == date(2026, 1, 15)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "deal_id, title, description, due_date, org_id, user_role, user_id, expected_exception",
    [
        (1, "Task", "Desc", date(2026, 1, 15), 2, "OWNER", 1, HTTPException),
        (1, "", "Valid desc", date(2026, 1, 15), 1, "OWNER", 1, HTTPException),
        (
            1,
            "   ",
            "Valid desc",
            date(2026, 1, 15),
            1,
            "OWNER",
            1,
            HTTPException
        ),
        (
            1,
            "T" * 150,
            "Valid desc",
            date(2026, 1, 15),
            1,
            "OWNER",
            1,
            HTTPException
        ),
        (1, "Valid task", "", date(2026, 1, 15), 1, "OWNER", 1, HTTPException),
        (
            1,
            "Valid task",
            "   ",
            date(2026, 1, 15),
            1,
            "OWNER",
            1,
            HTTPException
        ),
        (
            1,
            "Valid task",
            "Valid desc",
            date(2020, 1, 15),
            1,
            "OWNER",
            1,
            HTTPException
        ),
    ]
)
async def test_create_task_service_validation(
    tasks_service,
    deal_by_test_user,
    deal_id,
    title,
    description,
    due_date,
    org_id,
    user_role,
    user_id,
    expected_exception
):
    with pytest.raises(expected_exception) as exc:
        await tasks_service.create_task(
            deal_id=deal_id if deal_id != 1 else deal_by_test_user.id,
            title=title,
            description=description,
            due_date=due_date,
            organization_id=org_id,
            user_role=user_role,
            user_id=user_id
        )

    if expected_exception is HTTPException:
        err = exc.value
        assert isinstance(err, HTTPException)
        assert err.status_code in (400, 403)
        assert err.detail is not None

    if expected_exception is ValueError:
        assert "title" in str(exc.value) or "description" in str(exc.value)