import uuid

from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint
from app.models.particule_link import ParticuleLink

# Links belong to a user: two users can each have the same link,
# but a user can't have it twice.
class Link(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("owner_id", "link"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    link: str = Field(index=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    owner: "User" = Relationship(back_populates="links")  # type: ignore
    particules: list["Particule"] = Relationship(back_populates="links", link_model=ParticuleLink) # type: ignore
