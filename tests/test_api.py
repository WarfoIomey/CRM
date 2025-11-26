from datetime import date, timedelta

import pytest
from sqlalchemy import select

from models import (
    ContactModel,
    DealModel,
    UserModel,
    RefreshTokenModel,
    OrganizationModel,
    OrganizationMemberModel,
    TaskModel,
)
from models.constants import Currency, MemberRole


@pytest.mark.asyncio
async def test_register_success(async_client, db_session):
    payload = {
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User",
        "organization_name": "MyOrg"
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["refresh_token"]) > 30
    result = await db_session.execute(
        select(UserModel).where(UserModel.email == payload["email"])
    )
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.name == "Test User"
    result = await db_session.execute(
        select(OrganizationModel).where(OrganizationModel.name == "MyOrg")
    )
    org = result.scalar_one_or_none()
    assert org is not None
    result = await db_session.execute(
        select(RefreshTokenModel).where(RefreshTokenModel.user_id == user.id)
    )
    tokens = result.scalars().all()
    assert len(tokens) == 1
    assert tokens[0].revoked is False


@pytest.mark.asyncio
async def test_get_user_organizations_success(
    async_client,
    access_token_test_user,
    
):
    """
    Проверяем, что /organizations/me возвращает организации пользователя.
    """
    token = "Bearer " + access_token_test_user
    response = await async_client.get(
        "/api/v1/organizations/me",
        headers={"Authorization": token}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_add_member_to_organization_success(
    async_client,
    access_token_test_user,
    ogranization_test_user,
    second_user,
    db_session
):
    """
    Проверяем добавление нового участника в организацию через эндпоинт.
    """

    token = "Bearer " + access_token_test_user

    payload = {
        "user_id": second_user.id,
        "role": MemberRole.MEMBER
    }

    response = await async_client.post(
        "/api/v1/organizations/organization-members",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(ogranization_test_user.id)
        },
        json=payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == second_user.id
    assert data["role"] == MemberRole.MEMBER
    result = await db_session.execute(
        select(OrganizationMemberModel).where(
            OrganizationMemberModel.user_id == second_user.id,
            OrganizationMemberModel.organization_id == ogranization_test_user.id
        )
    )
    membership = result.scalar_one_or_none()
    assert membership is not None
    assert membership.role == MemberRole.MEMBER


@pytest.mark.asyncio
async def test_add_member_to_organization_permission_denied(
    async_client,
    ogranization_test_user,
    access_token_second_user,
    three_user,
):
    """
    Пользователь из другой организации не может добавить участника.
    """
    org_id = 1

    token = "Bearer " + access_token_second_user
    payload = {"user_id": three_user.id, "role": MemberRole.MEMBER}

    response = await async_client.post(
        "/api/v1/organizations/organization-members",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(org_id)
        },
        json=payload
    )
    assert response.status_code == 403
    assert response.json()[
        "detail"
    ] == "Вы не являетесь участником этой организации."


@pytest.mark.asyncio
async def test_get_user_contacts_success(
    async_client,
    access_token_test_user,
    contact_by_test_user,
    ogranization_test_user,
):
    """
    Тест GET /contacts/ который возвращает контакты пользователя.
    """
    token = "Bearer " + access_token_test_user
    response = await async_client.get(
        "/api/v1/contacts/",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(ogranization_test_user.id)
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(contact["id"] == contact_by_test_user.id for contact in data)


@pytest.mark.asyncio
async def test_create_contact_success(
    async_client,
    access_token_test_user,
    ogranization_test_user,
    db_session
):
    """
    Тест на успешное создание контакта через POST /contacts/.
    """
    token = "Bearer " + access_token_test_user

    payload = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+123456789"
    }

    response = await async_client.post(
        "/api/v1/contacts/",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(ogranization_test_user.id)
        },
        json=payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john.doe@example.com"
    assert data["phone"] == "+123456789"
    result = await db_session.execute(
        select(ContactModel).where(ContactModel.id == data["id"])
    )
    contact = result.scalar_one_or_none()
    assert contact is not None
    assert contact.name == "John Doe"


@pytest.mark.asyncio
async def test_create_contact_permission_denied(
    async_client,
    add_user_in_org,
    access_token_second_user,
    ogranization_test_user
):
    """
    Тест, что пользователь без WRITE_CONTACT не может создать контакт.
    """
    token = "Bearer " + access_token_second_user
    payload = {
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "phone": "+987654321"
    }

    response = await async_client.post(
        "/api/v1/contacts/",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(ogranization_test_user.id)
        },
        json=payload
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied"


@pytest.mark.asyncio
async def test_create_deal_success(
    async_client,
    access_token_test_user,
    ogranization_test_user,
    contact_test_user,
    db_session
):
    """
    Тест на успешное создание сделки через POST /deals/.
    """
    token = "Bearer " + access_token_test_user

    payload = {
        "contact_id": contact_test_user.id,
        "title": "Website redesign",
        "amount": 10000.0,
        "currency": Currency.EUR
    }

    response = await async_client.post(
        "/api/v1/deals/",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(ogranization_test_user.id)
        },
        json=payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["contact_id"] == payload["contact_id"]
    assert data["amount"] == payload["amount"]
    assert data["currency"] == payload["currency"]
    assert data["organization_id"] == ogranization_test_user.id
    result = await db_session.execute(
        select(DealModel).where(DealModel.id == data["id"])
    )
    deal = result.scalar_one_or_none()
    assert deal is not None
    assert deal.title == payload["title"]


@pytest.mark.asyncio
async def test_get_user_deals_success(
    async_client,
    access_token_test_user,
    ogranization_test_user,
    deal_by_test_user
):
    """
    Тест на GET /deals/ — получение списка сделок текущего пользователя.
    """
    token = "Bearer " + access_token_test_user

    response = await async_client.get(
        "/api/v1/deals/",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(ogranization_test_user.id)
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(d["id"] == deal_by_test_user.id for d in data)


@pytest.mark.asyncio
async def test_update_deal_validation_failure(
    async_client,
    access_token_test_user,
    ogranization_test_user,
    deal_by_test_user
):
    """
    Тест проверяет, что нельзя обновить сделку с неверными данными
    или правами.
    """
    token = "Bearer " + access_token_test_user

    payload = {"stage": "unvalid stage"}
    response = await async_client.patch(
        f"/api/v1/deals/{deal_by_test_user.id}",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(ogranization_test_user.id)
        },
        json=payload
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_activity_comment_success(
    async_client,
    access_token_test_user,
    ogranization_test_user,
    deal_by_test_user
):
    """
    Тест на создание комментария по сделке через POST {deal_id}/activities
    """
    token = "Bearer " + access_token_test_user
    payload = {"type": "comment", "payload": {"detail": "Discussed proposal"}}

    response = await async_client.post(
        f"/api/v1/deals/{deal_by_test_user.id}/activities",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(ogranization_test_user.id)
        },
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["payload"] == payload["payload"]


@pytest.mark.asyncio
async def test_create_task_success(
    async_client,
    access_token_test_user,
    ogranization_test_user,
    deal_by_test_user,
    db_session
):
    token = "Bearer " + access_token_test_user
    payload = {
        "deal_id": deal_by_test_user.id,
        "title": "Call client",
        "description": "Discuss proposal details",
        "due_date": (date.today() + timedelta(days=5)).isoformat()
    }
    response = await async_client.post(
        "/api/v1/tasks/",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(ogranization_test_user.id)
        },
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Call client"
    assert data["description"] == "Discuss proposal details"
    assert data["due_date"] == payload["due_date"]
    result = await db_session.execute(
        select(TaskModel).where(TaskModel.id == data["id"])
    )
    task = result.scalar_one_or_none()
    assert task is not None
    assert task.title == payload["title"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload,expected_detail,code",
    [
        (
            {
                "title": "",
                "description": "desc",
                "due_date": (date.today() + timedelta(days=1)).isoformat()
            },
            "Название не может быть пустым",
            400
        ),
        (
            {
                "title": "Title",
                "description": "",
                "due_date": (date.today() + timedelta(days=1)).isoformat()
            },
            "Описание не может быть пустым",
            400,
        ),
        (
            {
                "title": "Title",
                "description": "Desc",
                "due_date": (date.today() - timedelta(days=1)).isoformat()
            },
            "Дата выполнения не может быть",
            422,
        )
    ]
)
async def test_create_task_validation_fail(
    async_client,
    access_token_test_user,
    ogranization_test_user,
    deal_by_test_user,
    payload,
    expected_detail,
    code
):
    token = "Bearer " + access_token_test_user
    payload["deal_id"] = deal_by_test_user.id
    response = await async_client.post(
        "/api/v1/tasks/",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(ogranization_test_user.id)
        },
        json=payload
    )
    assert response.status_code == code
    assert expected_detail in response.text


@pytest.mark.asyncio
async def test_get_tasks_with_filters(
    async_client,
    access_token_test_user,
    ogranization_test_user,
    deal_by_test_user,
    task_test_user
):
    token = "Bearer " + access_token_test_user

    response = await async_client.get(
        "/api/v1/tasks/",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(ogranization_test_user.id)
        },
        params={"deal_id": deal_by_test_user.id}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(task["deal_id"] == deal_by_test_user.id for task in data)


@pytest.mark.asyncio
async def test_get_summary_of_deal(
    async_client,
    access_token_test_user,
    ogranization_test_user,
    deal_by_test_user,
):
    token = "Bearer " + access_token_test_user

    response = await async_client.get(
        "/api/v1/analytics/deals/summary",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(ogranization_test_user.id)
        },
        params={"days": 30}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "status_summary" in data
    assert "avg_won_amount" in data
    assert "new_deals_last_days" in data


@pytest.mark.asyncio
async def test_get_deals_funnel_success(
    async_client,
    access_token_test_user,
    ogranization_test_user,
    deal_by_test_user,
):
    token = "Bearer " + access_token_test_user
    response = await async_client.get(
        "/api/v1/analytics/deals/funnel",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(ogranization_test_user.id)
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "funnel" in data
    assert "conversion" in data
    assert isinstance(data["funnel"], dict)
    assert isinstance(data["conversion"], dict)
    for stage, stage_data in data["funnel"].items():
        assert isinstance(stage_data, dict)
        for status, count in stage_data.items():
            assert isinstance(status, str)
            assert isinstance(count, int)
    for stage, value in data["conversion"].items():
        assert value is None or isinstance(value, float)