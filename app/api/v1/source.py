import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.deps import CurrentUser, SessionDep
from app.data import source as source_data
from app.models import Source, SourceCreate, SourcePublic, SourceUpdate

router = APIRouter(prefix="/sources", tags=["sources"])

def get_owned_source(session: SessionDep, current_user: CurrentUser, source_id: uuid.UUID) -> Source:
    source = source_data.get_source(session, current_user, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return source

OwnedSource = Annotated[Source, Depends(get_owned_source)]

@router.get("/", response_model=list[SourcePublic])
def list_sources(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100) -> list[Source]:
    return source_data.get_sources(session, current_user, skip, limit)

@router.get("/{source_id}", response_model=SourcePublic)
def read_source_by_id(source: OwnedSource) -> Source:
    return source

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SourcePublic)
def create_source(session: SessionDep, current_user: CurrentUser, source_in: SourceCreate) -> Source:
    return source_data.create_source(session, current_user, source_in)

@router.patch("/{source_id}", response_model=SourcePublic)
def update_source(session: SessionDep, source: OwnedSource, source_in: SourceUpdate) -> Source:
    return source_data.update_source(session, source, source_in)

@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(session: SessionDep, source: OwnedSource) -> None:
    source_data.delete_source(session, source)
