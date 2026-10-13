import uuid

from sqlmodel import Field, SQLModel, Relationship
from app.models.particule_link import ParticuleLink

class Link(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    link: str = Field(index=True)
    particules: list["Particule"] = Relationship(back_populates="links", link_model=ParticuleLink) # type: ignore