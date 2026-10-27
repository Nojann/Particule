import uuid

from datetime import date
from enum import Enum
from typing import List, Self
from pydantic import model_validator
from sqlmodel import Field, SQLModel, Relationship, Text


class SourceType(str, Enum):
    book = "book"
    journal_article = "journal_article"
    book_chapter = "book_chapter"
    web_page = "web_page"
    # Catch-all (podcast, lecture, conversation…): only a title is required
    other = "other"

# Fields each type needs on top of title
REQUIRED_BY_TYPE: dict[SourceType, tuple[str, ...]] = {
    SourceType.book: ("authors",),
    SourceType.journal_article: ("authors", "container_title"),
    SourceType.book_chapter: ("authors", "container_title"),
    SourceType.web_page: ("authors", "url"),
    SourceType.other: (),
}

class SourceBase(SQLModel):
    type: SourceType
    title: str = Field(max_length=1024)
    # Free text, e.g. "Feynman, Richard; Leighton, Robert". Required except for other.
    authors: str | None = Field(default=None, max_length=1024)
    editors: str | None = Field(default=None, max_length=1024)
    container_title: str | None = Field(default=None, max_length=1024)
    volume: str | None = Field(default=None, max_length=64)
    issue: str | None = Field(default=None, max_length=64)
    pages: str | None = Field(default=None, max_length=64)
    doi: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=2048)
    published_date: date | None = None
    accessed_date: date | None = None
    # null for an undated source (« s.d. »)
    year: int | None = None
    edition: str | None = Field(default=None, max_length=255)
    publisher: str | None = Field(default=None, max_length=255)
    # The user's own words about the source
    note: str | None = Field(default=None, sa_type=Text)

# Sources belong to a user: two users can each have their own entry for the same book.
class Source(SourceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    owner: "User" = Relationship(back_populates="sources")  # type: ignore
    particules: List["Particule"] = Relationship(back_populates="source") # type: ignore

class SourceCreate(SourceBase):
    @model_validator(mode="after")
    def check_consistency(self) -> Self:
        if self.published_date is not None:
            if self.year is None:
                self.year = self.published_date.year
            elif self.year != self.published_date.year:
                raise ValueError("year must match published_date")
        missing = [f for f in REQUIRED_BY_TYPE[self.type] if getattr(self, f) is None]
        if missing:
            raise ValueError(f"{self.type.value} requires {', '.join(missing)}")
        return self

# Properties to receive via API on update, all are optional.
# The merged result is validated again with SourceCreate (see data.update_source).
class SourceUpdate(SQLModel):
    type: SourceType | None = None
    title: str | None = Field(default=None, max_length=1024)
    authors: str | None = Field(default=None, max_length=1024)
    editors: str | None = Field(default=None, max_length=1024)
    container_title: str | None = Field(default=None, max_length=1024)
    volume: str | None = Field(default=None, max_length=64)
    issue: str | None = Field(default=None, max_length=64)
    pages: str | None = Field(default=None, max_length=64)
    doi: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=2048)
    published_date: date | None = None
    accessed_date: date | None = None
    year: int | None = None
    edition: str | None = Field(default=None, max_length=255)
    publisher: str | None = Field(default=None, max_length=255)
    note: str | None = None

class SourcePublic(SourceBase):
    id: uuid.UUID
    owner_id: uuid.UUID
