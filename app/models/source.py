import uuid

from typing import List
from sqlmodel import Field, SQLModel, Relationship


class Source(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    authors: str
    year: int
    edition: str
    publisher: str
    particules: List["Particule"] = Relationship(back_populates="source") # type: ignore
    