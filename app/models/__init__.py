"""Import every table model so SQLModel.metadata knows about all of them."""

from app.models.particule_link import ParticuleLink
from app.models.particule_tag import ParticuleTag

from app.models.knowledge_base import KnowledgeBase, KnowledgeBaseCreate
from app.models.link import Link, LinkCreate, LinkPublic, LinkUpdate
from app.models.particule import (
    Particule,
    ParticuleCreate,
    ParticulePublic,
    ParticuleUpdate,
)
from app.models.source import Source, SourceCreate, SourcePublic, SourceUpdate
from app.models.tag import Tag, TagCreate, TagPublic, TagUpdate
from app.models.user import (
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.models.auth import Token, TokenPayload, NewPassword

__all__ = [
    "KnowledgeBase",
    "KnowledgeBaseCreate",
    "Link",
    "LinkCreate",
    "LinkPublic",
    "LinkUpdate",
    "Particule",
    "ParticuleCreate",
    "ParticulePublic",
    "ParticuleUpdate",
    "ParticuleLink",
    "ParticuleTag",
    "Source",
    "SourceCreate",
    "SourcePublic",
    "SourceUpdate",
    "Tag",
    "TagCreate",
    "TagPublic",
    "TagUpdate",
    "UpdatePassword",
    "User",
    "UserCreate",
    "UserPublic",
    "UserRegister",
    "UsersPublic",
    "UserUpdate",
    "UserUpdateMe",
    "Token",
    "TokenPayload",
    "NewPassword"
]
