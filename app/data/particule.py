import uuid

from sqlmodel import Session, select

from app.models import KnowledgeBase, Particule, ParticuleCreate, ParticuleUpdate

# Every function takes a KnowledgeBase the caller has already checked
# belongs to the current user: scoping by kb is what enforces ownership.

def get_particules(session: Session, kb: KnowledgeBase, skip: int = 0, limit: int = 100) -> list[Particule]:
    statement = (
        select(Particule)
        .where(Particule.knowledge_base_id == kb.id)
        .order_by(Particule.title)
        .offset(skip)
        .limit(limit)
    )
    results = session.exec(statement)
    return list(results.all())

def get_particule(session: Session, kb: KnowledgeBase, particule_id: uuid.UUID) -> Particule | None:
    statement = select(Particule).where(Particule.knowledge_base_id == kb.id).where(Particule.id == particule_id)
    results = session.exec(statement)
    return results.first()

def get_particule_by_permalink(session: Session, kb: KnowledgeBase, permalink: str) -> Particule | None:
    statement = select(Particule).where(Particule.knowledge_base_id == kb.id).where(Particule.permalink == permalink)
    results = session.exec(statement)
    return results.first()

def permalink_exists(session: Session, permalink: str) -> bool:
    """Permalinks are unique across all knowledge bases (see Particule.permalink)."""
    statement = select(Particule.id).where(Particule.permalink == permalink)
    return session.exec(statement).first() is not None

def create_particule(session: Session, kb: KnowledgeBase, particule_in: ParticuleCreate) -> Particule:
    particule = Particule.model_validate(particule_in, update={"knowledge_base_id": kb.id})
    session.add(particule)
    session.commit()
    session.refresh(particule)
    return particule

def update_particule(session: Session, particule: Particule, particule_in: ParticuleUpdate) -> Particule:
    particule_data = particule_in.model_dump(exclude_unset=True)
    particule.sqlmodel_update(particule_data)
    session.add(particule)
    session.commit()
    session.refresh(particule)
    return particule

def delete_particule(session: Session, particule: Particule) -> None:
    session.delete(particule)
    session.commit()
