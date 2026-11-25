"""Tests for the payment gateway without external credentials or charges."""
import pytest

from app.payment_gateway import PaymentGatewayError, create_payment


def test_mock_payment_is_pending_and_not_real():
    result = create_payment(order_id="os-123", amount="150.00", token="", email="", mode="mock")
    assert result["status"] == "pending"
    assert result["simulated"] is True
    assert result["provider"] == "mock"
    assert result["external_reference"] == "os-123"
    assert result["id"].startswith("mock-")


@pytest.mark.parametrize("amount", ["0", "-1", "NaN", "Infinity", "abc"])
def test_invalid_amount_rejected(amount):
    with pytest.raises(ValueError):
        create_payment(order_id="os-123", amount=amount, token="", email="", mode="mock")


def test_invalid_provider_rejected():
    with pytest.raises(ValueError):
        create_payment(order_id="os-123", amount="10", token="", email="", mode="invalid")


def test_real_provider_requires_credentials(monkeypatch):
    monkeypatch.delenv("MERCADOPAGO_ACCESS_TOKEN", raising=False)
    with pytest.raises(PaymentGatewayError, match="not configured"):
        create_payment(order_id="os-123", amount="10", token="test-token",
                       email="buyer@example.com", mode="mercadopago")
