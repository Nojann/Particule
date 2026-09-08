from sqlmodel import Field, SQLModel

class ParticuleTag(SQLModel, table=True):
    particule_id: int | None = Field(default=None, foreign_key="particule.id", primary_key=True)
    tag_id: int | None = Field(default=None, foreign_key="tag.id", primary_key=True)