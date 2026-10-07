import pytest
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

# Import every table model so SQLModel.metadata knows all tables before create_all
import app.models.particule  # noqa: F401


@pytest.fixture
def session():
    engine = create_engine("sqlite://")

    # SQLite ignores foreign keys unless asked, Postgres always enforces them
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
