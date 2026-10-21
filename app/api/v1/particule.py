import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.deps import CurrentUser, SessionDep
from app.data import knowledge_base as kb_data
from app.data import particule as particule_data
from app.models import KnowledgeBase, Particule, ParticuleCreate, ParticulePublic, ParticuleUpdate

router = APIRouter(prefix="/knowledge-bases/{kb_id}/particules", tags=["particules"])

def get_owned_kb(session: SessionDep, current_user: CurrentUser, kb_id: uuid.UUID) -> KnowledgeBase:
    kb = kb_data.get_knowledge_base(session, current_user, kb_id)
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    return kb

OwnedKB = Annotated[KnowledgeBase, Depends(get_owned_kb)]

def get_owned_particule(session: SessionDep, kb: OwnedKB, particule_id: uuid.UUID) -> Particule:
    particule = particule_data.get_particule(session, kb, particule_id)
    if particule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Particule not found")
    return particule

OwnedParticule = Annotated[Particule, Depends(get_owned_particule)]

def ensure_permalink_available(session: SessionDep, permalink: str) -> None:
    if particule_data.permalink_exists(session, permalink):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Permalink already exists")

@router.get("/", response_model=list[ParticulePublic])
def list_particules(session: SessionDep, kb: OwnedKB, skip: int = 0, limit: int = 100) -> list[Particule]:
    return particule_data.get_particules(session, kb, skip, limit)

@router.get("/by-permalink/{permalink}", response_model=ParticulePublic)
def read_particule_by_permalink(session: SessionDep, kb: OwnedKB, permalink: str) -> Particule:
    particule = particule_data.get_particule_by_permalink(session, kb, permalink)
    if particule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Particule not found")
    return particule

@router.get("/{particule_id}", response_model=ParticulePublic)
def read_particule_by_id(particule: OwnedParticule) -> Particule:
    return particule

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ParticulePublic)
def create_particule(session: SessionDep, kb: OwnedKB, particule_in: ParticuleCreate) -> Particule:
    ensure_permalink_available(session, particule_in.permalink)
    return particule_data.create_particule(session, kb, particule_in)

@router.patch("/{particule_id}", response_model=ParticulePublic)
def update_particule(session: SessionDep, particule: OwnedParticule, particule_in: ParticuleUpdate) -> Particule:
    if particule_in.permalink is not None and particule_in.permalink != particule.permalink:
        ensure_permalink_available(session, particule_in.permalink)
    return particule_data.update_particule(session, particule, particule_in)

@router.delete("/{particule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_particule(session: SessionDep, particule: OwnedParticule) -> None:
    particule_data.delete_particule(session, particule)
