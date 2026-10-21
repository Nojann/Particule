import uuid

from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint
from app.models.particule_tag import ParticuleTag

class TagBase(SQLModel):
    tag: str = Field(index=True, min_length=1, max_length=255)

# Tags belong to a user: two users can each have the same tag,
# but a user can't have it twice.
class Tag(TagBase, table=True):
    __table_args__ = (UniqueConstraint("owner_id", "tag"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    owner: "User" = Relationship(back_populates="tags")  # type: ignore
    particules: list["Particule"] = Relationship(back_populates="tags", link_model=ParticuleTag) # type: ignore

class TagCreate(TagBase):
    pass

class TagUpdate(TagBase):
    pass

class TagPublic(TagBase):
    id: uuid.UUID
    owner_id: uuid.UUID
