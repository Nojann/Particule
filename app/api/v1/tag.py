import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.deps import CurrentUser, SessionDep
from app.data import tag as tag_data
from app.models import Tag, TagCreate, TagPublic, TagUpdate

router = APIRouter(prefix="/tags", tags=["tags"])

def get_owned_tag(session: SessionDep, current_user: CurrentUser, tag_id: uuid.UUID) -> Tag:
    tag = tag_data.get_tag(session, current_user, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return tag

OwnedTag = Annotated[Tag, Depends(get_owned_tag)]

def ensure_tag_available(session: SessionDep, current_user: CurrentUser, name: str) -> None:
    if tag_data.get_tag_by_name(session, current_user, name) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag already exists")

@router.get("/", response_model=list[TagPublic])
def list_tags(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100) -> list[Tag]:
    return tag_data.get_tags(session, current_user, skip, limit)

@router.get("/{tag_id}", response_model=TagPublic)
def read_tag_by_id(tag: OwnedTag) -> Tag:
    return tag

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TagPublic)
def create_tag(session: SessionDep, current_user: CurrentUser, tag_in: TagCreate) -> Tag:
    ensure_tag_available(session, current_user, tag_in.tag)
    return tag_data.create_tag(session, current_user, tag_in)

@router.patch("/{tag_id}", response_model=TagPublic)
def update_tag(session: SessionDep, current_user: CurrentUser, tag: OwnedTag, tag_in: TagUpdate) -> Tag:
    if tag_in.tag != tag.tag:
        ensure_tag_available(session, current_user, tag_in.tag)
    return tag_data.update_tag(session, tag, tag_in)

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(session: SessionDep, tag: OwnedTag) -> None:
    tag_data.delete_tag(session, tag)
