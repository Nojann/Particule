from sqlmodel import Field, SQLModel, Relationship
from app.models import User

class KnowledgeBase(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    particules: list["Particule"] = Relationship(back_populates="knowledge_base") # type: ignore

    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    user: User = Relationship(back_populates="knowledge_bases")  # type: ignore