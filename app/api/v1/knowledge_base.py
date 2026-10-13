import uuid
from fastapi import APIRouter, HTTPException, status

from app.auth.deps import CurrentUser, SessionDep
from app.data import knowledge_base as kb_data
from app.models import KnowledgeBase, KnowledgeBaseCreate

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])

@router.get("/")
def list_knowledge_bases(session: SessionDep, current_user: CurrentUser) -> list[KnowledgeBase]:
    return kb_data.get_knowledge_bases(session, current_user)

@router.get("/{kb_id}")
def read_knowledge_base_by_id(session: SessionDep, current_user: CurrentUser, kb_id: uuid.UUID) -> KnowledgeBase:
    kb = kb_data.get_knowledge_base(session, current_user, kb_id)
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    return kb

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_knowledge_base(session: SessionDep, current_user: CurrentUser, kb: KnowledgeBaseCreate) -> KnowledgeBase:
    return kb_data.create_knowledge_base(session, current_user, kb)

@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(session: SessionDep, current_user: CurrentUser, kb_id: uuid.UUID) -> None:
    kb = kb_data.get_knowledge_base(session, current_user, kb_id)
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    kb_data.delete_knowledge_base(session, kb)