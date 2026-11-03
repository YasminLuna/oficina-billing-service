import pytest
from fastapi.testclient import TestClient
from app.main import app, quotes

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_quotes():
    quotes.clear()


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_quote_approval():
    assert client.post("/quotes", json={"order_id": "os-1", "amount": "10.50"}).status_code == 201
    assert client.post("/quotes/os-1/approve").json()["state"] == "APPROVED"


def test_quote_rejection():
    client.post("/quotes", json={"order_id": "os-1", "amount": "10"})
    assert client.post("/quotes/os-1/reject").json()["state"] == "REJECTED"


@pytest.mark.parametrize("amount", ["0", "-1", "NaN", "Infinity", "abc"])
def test_invalid_amount(amount):
    assert client.post("/quotes", json={"order_id": "os-1", "amount": amount}).status_code == 422


def test_duplicate_quote():
    data = {"order_id": "os-1", "amount": "10"}
    client.post("/quotes", json=data)
    assert client.post("/quotes", json=data).status_code == 409


def test_missing_quote():
    assert client.get("/quotes/missing").status_code == 404


def test_cannot_approve_twice():
    client.post("/quotes", json={"order_id": "os-1", "amount": "10"})
    client.post("/quotes/os-1/approve")
    assert client.post("/quotes/os-1/approve").status_code == 409
