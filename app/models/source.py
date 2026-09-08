from typing import List
from sqlmodel import Field, SQLModel, Relationship


class Source(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    authors: str
    year: int
    edition: str
    publisher: str
    particules: List["Particule"] = Relationship(back_populates="source", cascade_delete=True) # type: ignore