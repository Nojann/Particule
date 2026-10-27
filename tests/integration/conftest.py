"""Fixtures for tests that need a database (data layer and API).

Fixture map (pytest only builds a fixture when a test asks for it):

    engine        (once per run)   test database, schema created from the models
    └── session   (per test)       transaction rolled back after each test
        ├── make_user              factory: insert a User
        ├── make_kb                factory: insert a KnowledgeBase
        ├── make_particule         factory: insert a Particule
        ├── make_tag               factory: insert a Tag
        ├── make_link              factory: insert a Link
        └── make_source            factory: insert a Source
    auth_headers                   factory: "Authorization: Bearer <jwt>" for a user

Needs the throwaway test database (see docs/testing.md):
    docker compose --profile test up -d --wait db-test
"""

import os
import uuid
from collections.abc import Callable, Generator
from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel

from app.auth.security import create_access_token, get_password_hash
# Importing app.models runs its __init__, which registers every table on
# SQLModel.metadata (needed by create_all below).
from app.models import KnowledgeBase, Link, Particule, Source, Tag, User
from app.models.source import SourceType

TEST_PASSWORD = "test-password-123"

INTEGRATION_DIR = Path(__file__).parent


# --- Markers -----------------------------------------------------------------
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark everything under tests/integration/ as `integration` automatically.

    No need to decorate each test: `pytest -m "not integration"` deselects
    them, `pytest` runs everything.
    """
    for item in items:
        if INTEGRATION_DIR in item.path.parents:
            item.add_marker(pytest.mark.integration)


# --- Database ----------------------------------------------------------------
@pytest.fixture(scope="session")
def engine() -> Generator[Engine]:
    """One engine and one fresh schema for the whole test run."""
    # Always set: tests/conftest.py provides a default.
    test_database_url = os.environ["TEST_DATABASE_URL"]

    # drop_all() below wipes every table: refuse anything that doesn't look
    # like a throwaway database, so a wrong URL can't destroy real data.
    db_name = make_url(test_database_url).database or ""
    if "test" not in db_name:
        pytest.exit(f"Refusing to run: database '{db_name}' must contain 'test'")

    engine = create_engine(test_database_url, pool_pre_ping=True)
    try:
        engine.connect().close()
    except OperationalError:
        pytest.skip(
            "Test database unreachable, start it with: "
            "docker compose --profile test up -d --wait db-test"
        )

    # Start from a clean schema built from the models. Whether the Alembic
    # migrations produce the same schema is checked in test_migrations.py.
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Generator[Session]:
    """A session whose changes are all rolled back at the end of the test.

    The data layer calls `session.commit()`. With
    join_transaction_mode="create_savepoint", those commits only release a
    SAVEPOINT inside the outer transaction opened here; nothing is ever really
    committed. Rolling back the outer transaction leaves the database empty for
    the next test: fast and fully isolated, with no table truncation.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# --- Factories ---------------------------------------------------------------
# Factories rather than pre-filled fixtures: each test creates exactly the
# rows it needs, so it reads on its own and doesn't depend on hidden data.


@pytest.fixture
def make_user(session: Session) -> Callable[..., User]:
    """Insert a user. Its password is TEST_PASSWORD unless given.

    Usage: alice = make_user(); admin = make_user(is_superuser=True)
    """

    def _make_user(
        email: str | None = None, password: str = TEST_PASSWORD, **fields
    ) -> User:
        user = User(
            # Random email: the column is unique, tests must not collide.
            email=email or f"user-{uuid.uuid4().hex[:8]}@example.com",
            hashed_password=get_password_hash(password),
            **fields,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    return _make_user


@pytest.fixture
def make_kb(session: Session, make_user: Callable[..., User]) -> Callable[..., KnowledgeBase]:
    """Insert a knowledge base, owned by a new user unless `owner` is given.

    Usage: kb = make_kb(owner=alice, name="Physics")
    """

    def _make_kb(owner: User | None = None, name: str = "Test KB") -> KnowledgeBase:
        kb = KnowledgeBase(name=name, owner_id=(owner or make_user()).id)
        session.add(kb)
        session.commit()
        session.refresh(kb)
        return kb

    return _make_kb


@pytest.fixture
def make_particule(
    session: Session, make_kb: Callable[..., KnowledgeBase]
) -> Callable[..., Particule]:
    """Insert a particule, in a new knowledge base unless `kb` is given.

    Usage: p = make_particule(kb=physics, title="Entropy")
    """

    def _make_particule(
        kb: KnowledgeBase | None = None,
        title: str = "Test particule",
        permalink: str | None = None,
        content: str = "Some content",
        origins: str = "Some origins",
        **fields,
    ) -> Particule:
        particule = Particule(
            title=title,
            # Random permalink: the column is unique, tests must not collide.
            permalink=permalink or f"particule-{uuid.uuid4().hex[:8]}",
            content=content,
            origins=origins,
            knowledge_base_id=(kb or make_kb()).id,
            **fields,
        )
        session.add(particule)
        session.commit()
        session.refresh(particule)
        return particule

    return _make_particule


@pytest.fixture
def make_tag(session: Session, make_user: Callable[..., User]) -> Callable[..., Tag]:
    """Insert a tag, owned by a new user unless `owner` is given.

    Usage: physics = make_tag(owner=alice, tag="physics")
    """

    def _make_tag(owner: User | None = None, tag: str | None = None) -> Tag:
        # Random name: (owner_id, tag) is unique, tests must not collide.
        tag = Tag(tag=tag or f"tag-{uuid.uuid4().hex[:8]}", owner_id=(owner or make_user()).id)
        session.add(tag)
        session.commit()
        session.refresh(tag)
        return tag

    return _make_tag


@pytest.fixture
def make_link(session: Session, make_user: Callable[..., User]) -> Callable[..., Link]:
    """Insert a link, owned by a new user unless `owner` is given.

    Usage: wiki = make_link(owner=alice, link="https://en.wikipedia.org")
    """

    def _make_link(owner: User | None = None, link: str | None = None) -> Link:
        # Random URL: (owner_id, link) is unique, tests must not collide.
        link = Link(
            link=link or f"https://example.com/{uuid.uuid4().hex[:8]}",
            owner_id=(owner or make_user()).id,
        )
        session.add(link)
        session.commit()
        session.refresh(link)
        return link

    return _make_link


@pytest.fixture
def make_source(session: Session, make_user: Callable[..., User]) -> Callable[..., Source]:
    """Insert a source, owned by a new user unless `owner` is given.

    Usage: book = make_source(owner=alice, authors="Feynman")
    """

    def _make_source(
        owner: User | None = None,
        type: SourceType = SourceType.book,
        title: str = "Test title",
        authors: str | None = "Test author",
        year: int | None = 2000,
        edition: str | None = "1st",
        publisher: str | None = "Test publisher",
        **fields,
    ) -> Source:
        source = Source(
            type=type,
            title=title,
            authors=authors,
            year=year,
            edition=edition,
            publisher=publisher,
            **fields,
            owner_id=(owner or make_user()).id,
        )
        session.add(source)
        session.commit()
        session.refresh(source)
        return source

    return _make_source


@pytest.fixture
def auth_headers() -> Callable[[User], dict[str, str]]:
    """Build Authorization headers for a user, with a real signed JWT.

    No mocking of `get_current_user`: the request goes through the real token
    decoding and user lookup. Only test_login.py needs to exercise the
    /login/access-token endpoint itself.

    Usage: client.get("/api/v1/...", headers=auth_headers(alice))
    """

    def _auth_headers(user: User) -> dict[str, str]:
        token = create_access_token(user.id, timedelta(minutes=5))
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers
