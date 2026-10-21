import uuid

from sqlmodel import Session, select

from app.models import Link, LinkCreate, LinkUpdate, User


def get_links(session: Session, current_user: User, skip: int = 0, limit: int = 100) -> list[Link]:
    statement = (
        select(Link)
        .where(Link.owner_id == current_user.id)
        .order_by(Link.link)
        .offset(skip)
        .limit(limit)
    )
    results = session.exec(statement)
    return list(results.all())

def get_link(session: Session, current_user: User, link_id: uuid.UUID) -> Link | None:
    statement = select(Link).where(Link.owner_id == current_user.id).where(Link.id == link_id)
    results = session.exec(statement)
    return results.first()

def get_link_by_url(session: Session, current_user: User, url: str) -> Link | None:
    statement = select(Link).where(Link.owner_id == current_user.id).where(Link.link == url)
    results = session.exec(statement)
    return results.first()

def create_link(session: Session, current_user: User, link_in: LinkCreate) -> Link:
    link = Link.model_validate(link_in, update={"owner_id": current_user.id})
    session.add(link)
    session.commit()
    session.refresh(link)
    return link

def update_link(session: Session, link: Link, link_in: LinkUpdate) -> Link:
    link.sqlmodel_update(link_in.model_dump(exclude_unset=True))
    session.add(link)
    session.commit()
    session.refresh(link)
    return link

def delete_link(session: Session, link: Link) -> None:
    session.delete(link)
    session.commit()
