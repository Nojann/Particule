from sqlmodel import Field, SQLModel

class ParticuleLink(SQLModel, table=True):
    particule_id: int | None = Field(default=None, foreign_key="particule.id", primary_key=True)
    link_id: int | None = Field(default=None, foreign_key="link.id", primary_key=True)
