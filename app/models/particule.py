from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from source import Source
from link import Link
from particule_link import ParticuleLink
from tag import Tag
from particule_tag import ParticuleTag
from knowledge_base import KnowledgeBase

class Particule(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    #title_embedding: vector
    permalink: str = Field(unique=True)
    links: list[Link] = Relationship(back_populates="particules", link_model = ParticuleLink)
    tags: list[Tag] = Relationship(back_populates="particules", link_model = ParticuleTag) 
    content: str
    #content_embedding: vector
    origins: str
    source: Optional[Source] = Relationship(back_populates="particules")
    knowledge_base: KnowledgeBase = Relationship(back_populates="particules")
