from decimal import Decimal, InvalidOperation
from enum import Enum
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Oficina Billing Service", version="0.1.0")


class QuoteState(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class QuoteInput(BaseModel):
    order_id: str = Field(min_length=1)
    amount: str


class Quote(BaseModel):
    order_id: str
    amount: str
    state: QuoteState = QuoteState.PENDING


# Development-only store; replace with service-owned SQL persistence before deploy.
quotes: dict[str, Quote] = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/quotes", response_model=Quote, status_code=201)
def create_quote(data: QuoteInput):
    try:
        amount = Decimal(data.amount)
    except InvalidOperation:
        raise HTTPException(422, "Invalid amount")
    if not amount.is_finite() or amount <= 0:
        raise HTTPException(422, "Amount must be positive and finite")
    if data.order_id in quotes:
        raise HTTPException(409, "Quote already exists")
    quote = Quote(order_id=data.order_id, amount=str(amount.quantize(Decimal("0.01"))))
    quotes[data.order_id] = quote
    return quote


@app.get("/quotes/{order_id}", response_model=Quote)
def get_quote(order_id: str):
    if order_id not in quotes:
        raise HTTPException(404, "Quote not found")
    return quotes[order_id]


@app.post("/quotes/{order_id}/approve", response_model=Quote)
def approve_quote(order_id: str):
    quote = get_quote(order_id)
    if quote.state != QuoteState.PENDING:
        raise HTTPException(409, "Quote already resolved")
    quote = quote.model_copy(update={"state": QuoteState.APPROVED})
    quotes[order_id] = quote
    return quote


@app.post("/quotes/{order_id}/reject", response_model=Quote)
def reject_quote(order_id: str):
    quote = get_quote(order_id)
    if quote.state != QuoteState.PENDING:
        raise HTTPException(409, "Quote already resolved")
    quote = quote.model_copy(update={"state": QuoteState.REJECTED})
    quotes[order_id] = quote
    return quote
