import uuid

from sqlmodel import Session, select

from app.models import Source, SourceCreate, SourceUpdate, User


def get_sources(session: Session, current_user: User, skip: int = 0, limit: int = 100) -> list[Source]:
    statement = (
        select(Source)
        .where(Source.owner_id == current_user.id)
        .order_by(Source.authors, Source.year)
        .offset(skip)
        .limit(limit)
    )
    results = session.exec(statement)
    return list(results.all())

def get_source(session: Session, current_user: User, source_id: uuid.UUID) -> Source | None:
    statement = select(Source).where(Source.owner_id == current_user.id).where(Source.id == source_id)
    results = session.exec(statement)
    return results.first()

def create_source(session: Session, current_user: User, source_in: SourceCreate) -> Source:
    source = Source.model_validate(source_in, update={"owner_id": current_user.id})
    session.add(source)
    session.commit()
    session.refresh(source)
    return source

def update_source(session: Session, source: Source, source_in: SourceUpdate) -> Source:
    source.sqlmodel_update(source_in.model_dump(exclude_unset=True))
    session.add(source)
    session.commit()
    session.refresh(source)
    return source

def delete_source(session: Session, source: Source) -> None:
    session.delete(source)
    session.commit()
