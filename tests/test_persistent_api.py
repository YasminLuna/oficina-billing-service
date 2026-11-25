"""Exercise the actual SQLite-backed Billing API, including error paths."""
import pytest
from fastapi.testclient import TestClient

from app.persistent_api import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("BILLING_SQLITE_PATH", str(tmp_path / "quotes.db"))
    monkeypatch.setenv("PAYMENT_PROVIDER_MODE", "mock")
    with TestClient(app) as test_client:
        yield test_client


def quote(client, order="os-1", amount="10.50"):
    return client.post("/quotes", json={"order_id": order, "amount": amount})


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_read_approve_and_pending_mock_payment(client):
    assert quote(client).status_code == 201
    assert client.get("/quotes/os-1").json()["amount"] == "10.50"
    assert client.post("/quotes/os-1/payments", json={}).status_code == 409
    assert client.post("/quotes/os-1/approve").json()["state"] == "APPROVED"
    response = client.post("/quotes/os-1/payments", json={})
    assert response.status_code == 202
    assert response.json()["status"] == "pending"
    assert response.json()["simulated"] is True
    assert client.post("/quotes/os-1/approve").status_code == 409


def test_reject_and_cancel(client):
    quote(client)
    assert client.post("/quotes/os-1/reject").json()["state"] == "REJECTED"
    assert client.post("/quotes/os-1/cancel").status_code == 409
    assert client.post("/quotes/os-1/payments", json={}).status_code == 409


def test_cancel_idempotent(client):
    quote(client)
    assert client.post("/quotes/os-1/cancel").json()["state"] == "CANCELLED"
    assert client.post("/quotes/os-1/cancel").json()["state"] == "CANCELLED"
    assert client.post("/quotes/os-1/approve").status_code == 409


def test_cancel_approved_quote(client):
    quote(client)
    client.post("/quotes/os-1/approve")
    assert client.post("/quotes/os-1/cancel").json()["state"] == "CANCELLED"


@pytest.mark.parametrize("amount", ["0", "-1", "NaN", "Infinity", "abc"])
def test_invalid_amount(client, amount):
    assert quote(client, amount=amount).status_code == 422


def test_duplicate_and_missing(client):
    quote(client)
    assert quote(client).status_code == 409
    assert client.get("/quotes/missing").status_code == 404
    assert client.post("/quotes/missing/approve").status_code == 404
    assert client.post("/quotes/missing/reject").status_code == 404
    assert client.post("/quotes/missing/cancel").status_code == 404
    assert client.post("/quotes/missing/payments", json={}).status_code == 404


def test_reject_missing_and_invalid_payload(client):
    assert quote(client, order="", amount="10").status_code == 422
    assert quote(client, amount="1").status_code == 201
    assert client.post("/quotes/os-1/reject").json()["state"] == "REJECTED"
    assert client.post("/quotes/os-1/reject").status_code == 409


def test_gateway_configuration_error(client, monkeypatch):
    quote(client)
    client.post("/quotes/os-1/approve")
    monkeypatch.setenv("PAYMENT_PROVIDER_MODE", "mercadopago")
    monkeypatch.delenv("MERCADOPAGO_ACCESS_TOKEN", raising=False)
    assert client.post("/quotes/os-1/payments", json={}).status_code == 503
    monkeypatch.setenv("PAYMENT_PROVIDER_MODE", "invalid")
    assert client.post("/quotes/os-1/payments", json={}).status_code == 422
