#Source : part of https://github.com/fastapi/full-stack-fastapi-template/blob/master/backend/app/api/routes/users.py

import uuid

from sqlmodel import Session, func, select

from app.auth.security import get_password_hash, verify_password
from app.models import User, UserPublic, UserCreate, UserUpdate, UserUpdateMe

# Dummy hash used to keep authentication timing constant when the user does not exist
DUMMY_HASH = get_password_hash("dummy-password-for-timing")


def get_users(session: Session, skip: int = 0, limit: int = 100) -> tuple[list[UserPublic], int]:
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()
    statement = select(User).order_by(User.created_at).offset(skip).limit(limit)
    users = session.exec(statement).all()
    users_public = [UserPublic.model_validate(user) for user in users]
    return list(users_public), count

def get_user(session: Session, user_id: uuid.UUID) -> User | None:
    return session.get(User, user_id)

def get_user_by_email(session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    results = session.exec(statement)
    user = results.first()
    return user

def create_user(session: Session, user_in: UserCreate) -> User:
    user = User.model_validate(user_in, update={"hashed_password": get_password_hash(user_in.password)})
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def update_user(session: Session, user: User, user_in: UserUpdate | UserUpdateMe) -> User:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data.pop("password")
        if password is not None:
            extra_data["hashed_password"] = get_password_hash(password)
    user.sqlmodel_update(user_data, update=extra_data)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def update_password(session: Session, user: User, new_password: str) -> User:
    user.hashed_password = get_password_hash(new_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def delete_user(session: Session, user: User) -> None:
    session.delete(user)
    session.commit()
