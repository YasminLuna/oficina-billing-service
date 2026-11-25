import sqlite3
import pytest
from app.sql_repository import SqlQuoteRepository


@pytest.fixture
def repo():
    connection = sqlite3.connect(":memory:")
    yield SqlQuoteRepository(connection)
    connection.close()


def test_create_and_read(repo):
    assert repo.create("os-1", "15.50") == repo.get("os-1")


def test_approve(repo):
    repo.create("os-1", "15")
    assert repo.resolve("os-1", "APPROVED")["state"] == "APPROVED"


def test_reject(repo):
    repo.create("os-1", "15")
    assert repo.resolve("os-1", "REJECTED")["state"] == "REJECTED"


def test_cannot_resolve_twice(repo):
    repo.create("os-1", "15")
    repo.resolve("os-1", "APPROVED")
    with pytest.raises(ValueError):
        repo.resolve("os-1", "REJECTED")


def test_missing_quote(repo):
    assert repo.get("missing") is None
    with pytest.raises(ValueError):
        repo.resolve("missing", "APPROVED")


def test_duplicate_quote(repo):
    repo.create("os-1", "15")
    with pytest.raises(sqlite3.IntegrityError):
        repo.create("os-1", "20")


@pytest.mark.parametrize("amount", ["0", "-1", "NaN", "Infinity"])
def test_invalid_amount(repo, amount):
    with pytest.raises(ValueError):
        repo.create("os-1", amount)


def test_invalid_resolution(repo):
    with pytest.raises(ValueError):
        repo.resolve("os-1", "UNKNOWN")
