import uuid

from sqlmodel import Session, select

from app.models import KnowledgeBase, KnowledgeBaseCreate, User


def get_knowledge_bases(session: Session, current_user: User) -> list[KnowledgeBase]:
    statement = select(KnowledgeBase).where(KnowledgeBase.owner_id == current_user.id)
    results = session.exec(statement)
    knowledge_bases = results.all()
    return list(knowledge_bases)

def get_knowledge_base(session: Session, current_user: User, kb_id: uuid.UUID) -> KnowledgeBase | None:
    statement = select(KnowledgeBase).where(KnowledgeBase.owner_id == current_user.id).where(KnowledgeBase.id == kb_id)
    results = session.exec(statement)
    knowledge_base = results.first()
    return knowledge_base

def create_knowledge_base(session: Session, current_user: User, kb_in: KnowledgeBaseCreate) -> KnowledgeBase:
    kb = KnowledgeBase.model_validate(kb_in, update={"owner_id": current_user.id})
    session.add(kb)
    session.commit()
    session.refresh(kb)
    return kb


def delete_knowledge_base(session: Session, kb: KnowledgeBase) -> None:
    session.delete(kb)
    session.commit()
