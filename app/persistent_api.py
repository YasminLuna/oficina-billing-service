"""Local SQLite-backed Billing API. Each request opens a short-lived connection."""
import os
import sqlite3
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.sql_repository import SqlQuoteRepository

app = FastAPI(title="Oficina Billing - Local SQL", version="0.2.0")


class QuoteInput(BaseModel):
    order_id: str = Field(min_length=1)
    amount: str


@contextmanager
def repository():
    path = os.getenv("BILLING_SQLITE_PATH", "/tmp/oficina-billing.db")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    try:
        yield SqlQuoteRepository(connection)
    finally:
        connection.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/quotes", status_code=201)
def create_quote(data: QuoteInput):
    try:
        amount = Decimal(data.amount)
        if not amount.is_finite() or amount <= 0:
            raise ValueError("Invalid amount")
        with repository() as repo:
            return repo.create(data.order_id, data.amount)
    except (InvalidOperation, ValueError):
        raise HTTPException(422, "Amount must be positive and finite")
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Quote already exists")


@app.get("/quotes/{order_id}")
def get_quote(order_id: str):
    with repository() as repo:
        result = repo.get(order_id)
    if result is None:
        raise HTTPException(404, "Quote not found")
    return result


def resolve_quote(order_id: str, state: str):
    with repository() as repo:
        try:
            return repo.resolve(order_id, state)
        except ValueError:
            if repo.get(order_id) is None:
                raise HTTPException(404, "Quote not found")
            raise HTTPException(409, "Quote already resolved")


@app.post("/quotes/{order_id}/approve")
def approve_quote(order_id: str):
    return resolve_quote(order_id, "APPROVED")


@app.post("/quotes/{order_id}/reject")
def reject_quote(order_id: str):
    return resolve_quote(order_id, "REJECTED")

@app.post("/quotes/{order_id}/cancel")
def cancel_quote(order_id: str):
    with repository() as repo:
        try:
            return repo.cancel(order_id)
        except ValueError:
            if repo.get(order_id) is None:
                raise HTTPException(404, "Quote not found")
            raise HTTPException(409, "Quote cannot be cancelled")
