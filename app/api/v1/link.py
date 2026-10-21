import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.deps import CurrentUser, SessionDep
from app.data import link as link_data
from app.models import Link, LinkCreate, LinkPublic, LinkUpdate

router = APIRouter(prefix="/links", tags=["links"])

def get_owned_link(session: SessionDep, current_user: CurrentUser, link_id: uuid.UUID) -> Link:
    link = link_data.get_link(session, current_user, link_id)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return link

OwnedLink = Annotated[Link, Depends(get_owned_link)]

def ensure_link_available(session: SessionDep, current_user: CurrentUser, url: str) -> None:
    if link_data.get_link_by_url(session, current_user, url) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Link already exists")

@router.get("/", response_model=list[LinkPublic])
def list_links(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100) -> list[Link]:
    return link_data.get_links(session, current_user, skip, limit)

@router.get("/{link_id}", response_model=LinkPublic)
def read_link_by_id(link: OwnedLink) -> Link:
    return link

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=LinkPublic)
def create_link(session: SessionDep, current_user: CurrentUser, link_in: LinkCreate) -> Link:
    ensure_link_available(session, current_user, link_in.link)
    return link_data.create_link(session, current_user, link_in)

@router.patch("/{link_id}", response_model=LinkPublic)
def update_link(session: SessionDep, current_user: CurrentUser, link: OwnedLink, link_in: LinkUpdate) -> Link:
    if link_in.link != link.link:
        ensure_link_available(session, current_user, link_in.link)
    return link_data.update_link(session, link, link_in)

@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(session: SessionDep, link: OwnedLink) -> None:
    link_data.delete_link(session, link)
