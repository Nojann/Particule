from sqlmodel import Session, create_engine, SQLModel

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url, 
    pool_pre_ping=True,             # test a connection before use, reconnect if dead
    pool_recycle=3600,              # replace connections before MariaDB's wait_timeout drops them
    pool_size=5,                    # connections kept open permanently
    max_overflow=10,                # extra connections allowed during traffic spikes
    #echo=settings.database_echo,    # log SQL queries (dev only)
)

def get_session():
    with Session(engine) as session :
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)