from sqlmodel import Field, SQLModel, Relationship

class KnowledgeBase(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    particules: list["Particule"] = Relationship(back_populates="knowledge_base") # type: ignore
    