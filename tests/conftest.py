import os
import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)   # or run `alembic upgrade head` (see §6)
    yield engine
    engine.dispose()

@pytest.fixture
def session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    # Your data layer calls session.commit(); this turns each commit into a SAVEPOINT
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()                 # everything the test did disappears
    connection.close()