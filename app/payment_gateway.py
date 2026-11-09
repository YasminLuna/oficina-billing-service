"""Mercado Pago payment adapter with safe, credential-free sandbox simulation.

The mock NEVER calls the network. Real requests use the official Payments API.
Do not treat mock responses as financial settlement.
"""
import json
import os
import uuid
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class PaymentGatewayError(RuntimeError):
    pass


def create_payment(*, order_id: str, amount: str, token: str, email: str,
                   payment_method_id: str = "pix", mode: str | None = None) -> dict:
    mode = (mode or os.getenv("PAYMENT_PROVIDER_MODE", "mock")).lower()
    try:
        value = Decimal(amount)
        if not value.is_finite() or value <= 0:
            raise ValueError()
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Payment amount must be positive and finite") from exc
    if not order_id:
        raise ValueError("order_id is required")
    if mode == "mock":
        return {"id": "mock-" + str(uuid.uuid4()), "status": "pending",
                "external_reference": order_id, "provider": "mock",
                "amount": str(value), "simulated": True}
    if mode != "mercadopago":
        raise ValueError("Unsupported PAYMENT_PROVIDER_MODE")
    access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")
    if not access_token:
        raise PaymentGatewayError("MERCADOPAGO_ACCESS_TOKEN is not configured")
    if not email or not token:
        raise ValueError("payer email and payment token are required")
    payload = {"transaction_amount": float(value), "token": token,
               "description": "Oficina OS " + order_id,
               "installments": 1, "payment_method_id": payment_method_id,
               "payer": {"email": email}, "external_reference": order_id}
    req = Request("https://api.mercadopago.com/v1/payments",
                  data=json.dumps(payload).encode(), method="POST",
                  headers={"Authorization": "Bearer " + access_token,
                           "Content-Type": "application/json",
                           "X-Idempotency-Key": "oficina-" + order_id})
    try:
        with urlopen(req, timeout=15) as response:
            result = json.load(response)
    except HTTPError as exc:
        raise PaymentGatewayError("Mercado Pago returned HTTP " + str(exc.code)) from exc
    except (URLError, TimeoutError) as exc:
        raise PaymentGatewayError("Mercado Pago connection failed") from exc
    return {"id": str(result["id"]), "status": result["status"],
            "external_reference": order_id, "provider": "mercadopago",
            "amount": str(value), "simulated": False}
