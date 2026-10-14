"""Fixtures for API tests: an HTTP client wired to the test database."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.auth.deps import get_db
from app.main import app


@pytest.fixture
def client(session: Session) -> Generator[TestClient]:
    """HTTP client for the app, sharing the test's session.

    Every route gets its session through `get_db` (SessionDep), so overriding
    it makes the API read and write inside the test transaction: data created
    with the factories is visible to the API, and vice versa.
    """
    app.dependency_overrides[get_db] = lambda: session
    with TestClient(app) as c:
        yield c
    # Don't leak the override into the next test.
    app.dependency_overrides.clear()
