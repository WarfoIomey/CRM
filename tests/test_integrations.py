from datetime import date

import pytest

from models.constants import MemberRole


@pytest.mark.asyncio
async def test_full_flow(
    async_client,
    second_user,
    db_session
):
    payload = {
        "email": "e2e_user@example.com",
        "password": "password123",
        "name": "E2E User",
        "organization_name": "E2E Org"
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    tokens = response.json()
    token = "Bearer " + tokens["access_token"]
    response_orgs = await async_client.get(
        "/api/v1/organizations/me",
        headers={"Authorization": token}
    )
    orgs = response_orgs.json()
    org_id = orgs[0]["id"]
    second_user_payload = {"user_id": second_user.id, "role": MemberRole.MEMBER}
    response = await async_client.post(
        "/api/v1/organizations/organization-members",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(org_id)
        },
        json=second_user_payload
    )
    assert response.status_code == 200
    member_data = response.json()
    assert member_data["user_id"] == second_user.id
    contact_payload = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+123456789"
    }
    response = await async_client.post(
        "/api/v1/contacts/",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(org_id)
        },
        json=contact_payload
    )
    assert response.status_code == 200
    contact_data = response.json()
    contact_id = contact_data["id"]
    deal_payload = {
        "contact_id": contact_id,
        "title": "Website redesign",
        "amount": 10000,
        "currency": "EUR"
    }
    response = await async_client.post(
        "/api/v1/deals/",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(org_id)
        },
        json=deal_payload
    )
    assert response.status_code == 200
    deal_data = response.json()
    deal_id = deal_data["id"]
    task_payload = {
        "deal_id": deal_id,
        "title": "Call client",
        "description": "Discuss proposal",
        "due_date": str(date.today())
    }
    response = await async_client.post(
        "/api/v1/tasks/",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(org_id)
        },
        json=task_payload
    )
    assert response.status_code == 200
    task_data = response.json()
    response = await async_client.get(
        "/api/v1/analytics/deals/funnel",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(org_id)
        }
    )
    assert response.status_code == 200
    funnel_data = response.json()
    assert "funnel" in funnel_data
    assert "conversion" in funnel_data
    response = await async_client.get(
        "/api/v1/analytics/deals/summary?days=30",
        headers={
            "Authorization": token,
            "X-Organization-ID": str(org_id)
        }
    )
    assert response.status_code == 200
    summary_data = response.json()




