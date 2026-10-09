from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from app.models import Source, Link, ParticuleLink, Tag, ParticuleTag, KnowledgeBase

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

    source_id: int | None = Field(default=None, foreign_key="source.id", ondelete = "SET NULL" )
    source: Optional[Source] = Relationship(back_populates="particules")

    knowledge_base_id: int = Field(foreign_key="knowledgebase.id")
    knowledge_base: KnowledgeBase = Relationship(back_populates="particules")
