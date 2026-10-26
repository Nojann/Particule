import uuid

from typing import Optional
from sqlmodel import Field, SQLModel, Relationship, Text
from app.models.source import Source
from app.models.link import Link
from app.models.particule_link import ParticuleLink
from app.models.tag import Tag
from app.models.particule_tag import ParticuleTag
from app.models.knowledge_base import KnowledgeBase

class ParticuleBase(SQLModel):
    title: str = Field(index=True)
    permalink: str = Field(unique=True)
    # Text, not str: on MySQL a bare str becomes VARCHAR(255)
    content: str = Field(sa_type=Text)
    origins: str

class Particule(ParticuleBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    #title_embedding: vector
    links: list[Link] = Relationship(back_populates="particules", link_model = ParticuleLink)
    tags: list[Tag] = Relationship(back_populates="particules", link_model = ParticuleTag)
    #content_embedding: vector

    source_id: uuid.UUID | None = Field(default=None, foreign_key="source.id", ondelete = "SET NULL" )
    source: Optional[Source] = Relationship(back_populates="particules")

    knowledge_base_id: uuid.UUID = Field(foreign_key="knowledgebase.id")
    knowledge_base: KnowledgeBase = Relationship(back_populates="particules")

# knowledge_base_id is never accepted from the client: it comes from the URL
class ParticuleCreate(ParticuleBase):
    source_id: uuid.UUID | None = None

class ParticuleUpdate(SQLModel):
    title: str | None = None
    permalink: str | None = None
    content: str | None = None
    origins: str | None = None
    source_id: uuid.UUID | None = None

class ParticulePublic(ParticuleBase):
    id: uuid.UUID
    source_id: uuid.UUID | None
    knowledge_base_id: uuid.UUID
