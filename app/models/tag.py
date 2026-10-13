import uuid

from sqlmodel import Field, SQLModel, Relationship
from app.models.particule_tag import ParticuleTag

class Tag(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tag: str = Field(index=True)
    particules: list["Particule"] = Relationship(back_populates="tags", link_model=ParticuleTag) # type: ignore
    