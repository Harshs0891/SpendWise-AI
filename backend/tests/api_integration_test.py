from decimal import Decimal

from fastapi.testclient import TestClient


def register_and_login(
    client: TestClient,
    email: str,
    password: str = "StrongPass123!",
) -> tuple[str, str]:
    registration = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert registration.status_code == 201, registration.text

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text

    token = login.json()["access_token"]
    return token, registration.json()["id"]


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_account(
    client: TestClient,
    token: str,
    name: str = "Primary Savings",
) -> dict:
    response = client.post(
        "/api/v1/accounts",
        headers=authorization(token),
        json={
            "name": name,
            "account_type": "bank",
            "currency": "INR",
            "opening_balance": "25000.0000",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_registration_login_and_authenticated_profile(client: TestClient):
    token, user_id = register_and_login(client, "api-flow@example.com")

    profile = client.get(
        "/api/v1/users/me",
        headers=authorization(token),
    )

    assert profile.status_code == 200
    assert profile.json()["id"] == user_id
    assert profile.json()["email"] == "api-flow@example.com"
    assert "password_hash" not in profile.json()

    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "email": "api-flow@example.com",
            "password": "StrongPass123!",
        },
    )
    assert duplicate.status_code == 409

    invalid_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "api-flow@example.com",
            "password": "WrongPassword123!",
        },
    )
    assert invalid_login.status_code == 401


def test_accounts_require_authentication_and_are_user_scoped(
    client: TestClient,
):
    first_token, first_user_id = register_and_login(
        client, "account-owner@example.com"
    )
    second_token, second_user_id = register_and_login(
        client, "another-owner@example.com"
    )

    account = create_account(client, first_token)

    assert account["user_id"] == first_user_id
    assert account["opening_balance"] == "25000.0000"

    first_accounts = client.get(
        "/api/v1/accounts",
        headers=authorization(first_token),
    )
    second_accounts = client.get(
        "/api/v1/accounts",
        headers=authorization(second_token),
    )

    assert first_accounts.status_code == 200
    assert len(first_accounts.json()) == 1
    assert second_accounts.status_code == 200
    assert second_accounts.json() == []

    cross_user_read = client.get(
        f"/api/v1/accounts/{account['id']}",
        headers=authorization(second_token),
    )
    assert cross_user_read.status_code == 404

    unauthenticated = client.get("/api/v1/accounts")
    assert unauthenticated.status_code == 401

    assert first_user_id != second_user_id


def test_transaction_creation_listing_and_account_validation(
    client: TestClient,
):
    token, user_id = register_and_login(
        client, "transactions@example.com"
    )
    account = create_account(client, token)

    transaction_payload = {
        "account_id": account["id"],
        "type": "expense",
        "amount": "125.5000",
        "currency": "INR",
        "description": "Groceries",
        "merchant": "Local Market",
        "transaction_date": "2026-11-08",
        "notes": "Weekly groceries",
    }

    created = client.post(
        "/api/v1/transactions",
        headers=authorization(token),
        json=transaction_payload,
    )

    assert created.status_code == 201, created.text
    transaction = created.json()
    assert transaction["user_id"] == user_id
    assert transaction["account_id"] == account["id"]
    assert Decimal(transaction["amount"]) == Decimal("125.5000")
    assert transaction["description"] == "Groceries"

    history = client.get(
        "/api/v1/transactions?type=expense&limit=10&offset=0",
        headers=authorization(token),
    )

    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert len(history.json()["items"]) == 1
    assert history.json()["items"][0]["id"] == transaction["id"]

    wrong_currency = client.post(
        "/api/v1/transactions",
        headers=authorization(token),
        json={**transaction_payload, "currency": "USD"},
    )
    assert wrong_currency.status_code == 400
    assert "currency must match account currency" in wrong_currency.json()["detail"]

    invalid_amount = client.post(
        "/api/v1/transactions",
        headers=authorization(token),
        json={**transaction_payload, "amount": "0"},
    )
    assert invalid_amount.status_code == 422
