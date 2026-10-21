import uuid

from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint
from app.models.particule_link import ParticuleLink

class LinkBase(SQLModel):
    link: str = Field(index=True, min_length=1)

# Links belong to a user: two users can each have the same link,
# but a user can't have it twice.
class Link(LinkBase, table=True):
    __table_args__ = (UniqueConstraint("owner_id", "link"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    owner: "User" = Relationship(back_populates="links")  # type: ignore
    particules: list["Particule"] = Relationship(back_populates="links", link_model=ParticuleLink) # type: ignore

class LinkCreate(LinkBase):
    pass

class LinkUpdate(LinkBase):
    pass

class LinkPublic(LinkBase):
    id: uuid.UUID
    owner_id: uuid.UUID
