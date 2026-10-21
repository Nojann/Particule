import uuid

from typing import List
from sqlmodel import Field, SQLModel, Relationship


class SourceBase(SQLModel):
    authors: str
    year: int
    edition: str
    publisher: str

# Sources belong to a user: two users can each have their own entry for the same book.
class Source(SourceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    owner: "User" = Relationship(back_populates="sources")  # type: ignore
    particules: List["Particule"] = Relationship(back_populates="source") # type: ignore

class SourceCreate(SourceBase):
    pass

# Properties to receive via API on update, all are optional
class SourceUpdate(SQLModel):
    authors: str | None = None
    year: int | None = None
    edition: str | None = None
    publisher: str | None = None

class SourcePublic(SourceBase):
    id: uuid.UUID
    owner_id: uuid.UUID
