import uuid

from sqlmodel import Session, select

from app.models import Source, SourceCreate, SourceUpdate, User


def get_sources(session: Session, current_user: User, skip: int = 0, limit: int = 100) -> list[Source]:
    statement = (
        select(Source)
        .where(Source.owner_id == current_user.id)
        # Undated sources (year is null) last
        .order_by(Source.title, Source.year.is_(None), Source.year)
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
    """Apply a partial update, then check the merged source with SourceCreate's rules.

    Raises pydantic.ValidationError, before touching the row, if the result is invalid.
    """
    # retains only the fields explicitly provided by the client
    update = source_in.model_dump(exclude_unset=True)
    # build the final state, from SourceCreate
    merged = source.model_dump(include=set(SourceCreate.model_fields)) | update
    # A new published_date sets the year again, unless the year is sent too
    if update.get("published_date") is not None and "year" not in update:
        merged["year"] = None
    validated = SourceCreate.model_validate(merged)
    source.sqlmodel_update(validated.model_dump())
    session.add(source)
    session.commit()
    session.refresh(source)
    return source

def delete_source(session: Session, source: Source) -> None:
    session.delete(source)
    session.commit()
