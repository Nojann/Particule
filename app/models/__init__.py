"""Import every table model so SQLModel.metadata knows about all of them."""

from app.models.particule_link import ParticuleLink
from app.models.particule_tag import ParticuleTag

from app.models.knowledge_base import KnowledgeBase, KnowledgeBaseCreate
from app.models.link import Link
from app.models.particule import Particule
from app.models.source import Source
from app.models.tag import Tag
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
    "Particule",
    "ParticuleLink",
    "ParticuleTag",
    "Source",
    "Tag",
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