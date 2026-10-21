import uuid

from sqlmodel import Session, select

from app.models import Tag, TagCreate, TagUpdate, User


def get_tags(session: Session, current_user: User, skip: int = 0, limit: int = 100) -> list[Tag]:
    statement = (
        select(Tag)
        .where(Tag.owner_id == current_user.id)
        .order_by(Tag.tag)
        .offset(skip)
        .limit(limit)
    )
    results = session.exec(statement)
    return list(results.all())

def get_tag(session: Session, current_user: User, tag_id: uuid.UUID) -> Tag | None:
    statement = select(Tag).where(Tag.owner_id == current_user.id).where(Tag.id == tag_id)
    results = session.exec(statement)
    return results.first()

def get_tag_by_name(session: Session, current_user: User, name: str) -> Tag | None:
    statement = select(Tag).where(Tag.owner_id == current_user.id).where(Tag.tag == name)
    results = session.exec(statement)
    return results.first()

def create_tag(session: Session, current_user: User, tag_in: TagCreate) -> Tag:
    tag = Tag.model_validate(tag_in, update={"owner_id": current_user.id})
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag

def update_tag(session: Session, tag: Tag, tag_in: TagUpdate) -> Tag:
    tag.sqlmodel_update(tag_in.model_dump(exclude_unset=True))
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag

def delete_tag(session: Session, tag: Tag) -> None:
    session.delete(tag)
    session.commit()
