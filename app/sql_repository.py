"""SQL-backed quote repository with transaction-safe state transitions.

SQLite supports local tests; production requires a PostgreSQL adapter and migrations.
"""
import sqlite3
from decimal import Decimal


class SqlQuoteRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                order_id TEXT PRIMARY KEY,
                amount TEXT NOT NULL,
                state TEXT NOT NULL CHECK (state IN ('PENDING', 'APPROVED', 'REJECTED'))
            )
        """)
        self.connection.commit()

    def create(self, order_id: str, amount: str) -> dict:
        value = Decimal(amount)
        if not order_id or not value.is_finite() or value <= 0:
            raise ValueError("order_id and positive finite amount are required")
        normalized = str(value.quantize(Decimal("0.01")))
        with self.connection:
            self.connection.execute(
                "INSERT INTO quotes(order_id, amount, state) VALUES (?, ?, 'PENDING')",
                (order_id, normalized),
            )
        return {"order_id": order_id, "amount": normalized, "state": "PENDING"}

    def get(self, order_id: str) -> dict | None:
        row = self.connection.execute(
            "SELECT order_id, amount, state FROM quotes WHERE order_id = ?",
            (order_id,),
        ).fetchone()
        return dict(zip(("order_id", "amount", "state"), row)) if row else None

    def resolve(self, order_id: str, state: str) -> dict:
        if state not in ("APPROVED", "REJECTED"):
            raise ValueError("Invalid quote resolution")
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE quotes SET state = ? WHERE order_id = ? AND state = 'PENDING'",
                (state, order_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Quote missing or already resolved")
        return self.get(order_id)
