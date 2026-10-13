import uuid

from sqlmodel import Field, SQLModel, Relationship


class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = False

    knowledge_bases: list["KnowledgeBase"] = Relationship(  # type: ignore
        back_populates="owner", cascade_delete=True
    )