import uuid

from sqlmodel import Field, SQLModel, Relationship
from datetime import UTC, datetime

def get_datetime_utc() -> datetime:
    return datetime.now(UTC)

class KnowledgeBaseBase(SQLModel):
    name: str = Field(max_length=255)

class KnowledgeBase(KnowledgeBaseBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at:  datetime | None = Field(default_factory=get_datetime_utc)
    updated_at: datetime | None = Field(default_factory=get_datetime_utc)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    owner: "User" = Relationship(back_populates="knowledge_bases")  # type: ignore
    particules: list["Particule"] = Relationship(back_populates="knowledge_base", cascade_delete=True) # type: ignore

class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass

class KnowledgeBaseUpdate(KnowledgeBaseBase):
    pass
