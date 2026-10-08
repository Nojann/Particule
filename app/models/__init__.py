"""Import every table model so SQLModel.metadata knows about all of them."""

from app.models.particule_link import ParticuleLink
from app.models.particule_tag import ParticuleTag

from app.models.knowledge_base import KnowledgeBase
from app.models.link import Link
from app.models.particule import Particule
from app.models.source import Source
from app.models.tag import Tag

__all__ = [
    "KnowledgeBase",
    "Link",
    "Particule",
    "ParticuleLink",
    "ParticuleTag",
    "Source",
    "Tag",
]