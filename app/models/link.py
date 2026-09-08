from sqlmodel import Field, SQLModel, Relationship
from particule_link import ParticuleLink

class Link(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    link: str = Field(index=True)
    particules: list["Particule"] = Relationship(back_populates="teams", link_model=ParticuleLink) # type: ignore