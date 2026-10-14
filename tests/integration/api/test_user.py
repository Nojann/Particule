"""API tests for /users routes (app/api/v1/user.py).

Focus: HTTP contract (status codes, response shape) and access control.
Detailed query logic belongs in tests/integration/data/test_user.py.
"""

import uuid

import pytest
from sqlmodel import select

from app.auth.security import verify_password
from app.config import settings
from app.models import KnowledgeBase, User

USERS = f"{settings.API_V1_STR}/users"

# Fields that must never appear in a response.
SECRET_FIELDS = {"password", "hashed_password"}


def assert_no_secrets(body: dict) -> None:
    assert SECRET_FIELDS.isdisjoint(body)


# --- Authentication ----------------------------------------------------------
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/me"),
        ("patch", "/me"),
        ("patch", "/me/password"),
        ("delete", "/me"),
        ("get", "/"),
        ("post", "/"),
    ],
)
def test_protected_routes_require_a_token(client, method, path):
    r = client.request(method, f"{USERS}{path}")
    assert r.status_code == 401


def test_invalid_token_is_rejected(client):
    r = client.get(f"{USERS}/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 403


def test_token_of_deleted_user_is_rejected(client, session, make_user, auth_headers):
    user = make_user()
    headers = auth_headers(user)
    session.delete(user)
    session.commit()

    r = client.get(f"{USERS}/me", headers=headers)
    assert r.status_code == 404


def test_inactive_user_is_rejected(client, make_user, auth_headers):
    user = make_user(is_active=False)
    r = client.get(f"{USERS}/me", headers=auth_headers(user))
    assert r.status_code == 400


# --- POST /signup ------------------------------------------------------------
def test_signup_creates_user(client, session):
    payload = {"email": "new@example.com", "password": "password123", "full_name": "New"}

    r = client.post(f"{USERS}/signup", json=payload)

    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "new@example.com"
    assert body["full_name"] == "New"
    assert body["is_active"] is True
    assert body["is_superuser"] is False
    assert_no_secrets(body)

    user = session.exec(select(User).where(User.email == "new@example.com")).one()
    assert verify_password("password123", user.hashed_password)[0]
    assert user.hashed_password != "password123"


def test_signup_cannot_create_superuser(client, session):
    # UserRegister has no is_superuser field: extra input must be ignored.
    payload = {"email": "sneaky@example.com", "password": "password123", "is_superuser": True}

    r = client.post(f"{USERS}/signup", json=payload)

    assert r.status_code == 200
    assert r.json()["is_superuser"] is False


def test_signup_with_existing_email_fails(client, make_user):
    make_user(email="taken@example.com")
    r = client.post(
        f"{USERS}/signup", json={"email": "taken@example.com", "password": "password123"}
    )
    assert r.status_code == 400


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "not-an-email", "password": "password123"},
        {"email": "short@example.com", "password": "short"},
        {"email": "missing-password@example.com"},
    ],
    ids=["invalid-email", "password-too-short", "missing-password"],
)
def test_signup_rejects_invalid_payload(client, payload):
    r = client.post(f"{USERS}/signup", json=payload)
    assert r.status_code == 422


# --- GET /me -----------------------------------------------------------------
def test_read_me_returns_current_user(client, make_user, auth_headers):
    user = make_user(full_name="Alice")

    r = client.get(f"{USERS}/me", headers=auth_headers(user))

    assert r.status_code == 200
    body = r.json()
    assert body["id"] == str(user.id)
    assert body["full_name"] == "Alice"
    assert_no_secrets(body)


# --- PATCH /me ---------------------------------------------------------------
def test_update_me(client, make_user, auth_headers):
    user = make_user(full_name="Old")

    r = client.patch(
        f"{USERS}/me",
        headers=auth_headers(user),
        json={"full_name": "New", "email": "updated@example.com"},
    )

    assert r.status_code == 200
    assert r.json()["full_name"] == "New"
    assert r.json()["email"] == "updated@example.com"


def test_update_me_with_own_email_is_allowed(client, make_user, auth_headers):
    user = make_user(email="me@example.com")
    r = client.patch(
        f"{USERS}/me", headers=auth_headers(user), json={"email": "me@example.com"}
    )
    assert r.status_code == 200


def test_update_me_with_email_of_another_user_fails(client, make_user, auth_headers):
    make_user(email="taken@example.com")
    user = make_user()

    r = client.patch(
        f"{USERS}/me", headers=auth_headers(user), json={"email": "taken@example.com"}
    )

    assert r.status_code == 409


def test_update_me_cannot_grant_superuser(client, make_user, auth_headers):
    # UserUpdateMe has no is_superuser field: extra input must be ignored.
    user = make_user()
    r = client.patch(
        f"{USERS}/me", headers=auth_headers(user), json={"is_superuser": True}
    )
    assert r.status_code == 200
    assert r.json()["is_superuser"] is False


# --- PATCH /me/password ------------------------------------------------------
def test_update_my_password(client, session, make_user, auth_headers):
    user = make_user(password="old-password")

    r = client.patch(
        f"{USERS}/me/password",
        headers=auth_headers(user),
        json={"current_password": "old-password", "new_password": "new-password"},
    )

    assert r.status_code == 200
    session.refresh(user)
    assert verify_password("new-password", user.hashed_password)[0]
    assert not verify_password("old-password", user.hashed_password)[0]


def test_update_my_password_with_wrong_current_password_fails(
    client, make_user, auth_headers
):
    user = make_user(password="old-password")
    r = client.patch(
        f"{USERS}/me/password",
        headers=auth_headers(user),
        json={"current_password": "wrong-password", "new_password": "new-password"},
    )
    assert r.status_code == 400


def test_update_my_password_to_the_same_one_fails(client, make_user, auth_headers):
    user = make_user(password="old-password")
    r = client.patch(
        f"{USERS}/me/password",
        headers=auth_headers(user),
        json={"current_password": "old-password", "new_password": "old-password"},
    )
    assert r.status_code == 400


# --- DELETE /me --------------------------------------------------------------
def test_delete_me(client, session, make_user, make_kb, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)
    user_id, kb_id = user.id, kb.id

    r = client.delete(f"{USERS}/me", headers=auth_headers(user))

    assert r.status_code == 200
    assert session.get(User, user_id) is None
    # Knowledge bases are deleted with their owner (cascade).
    assert session.get(KnowledgeBase, kb_id) is None


def test_superuser_cannot_delete_themselves(client, make_user, auth_headers):
    admin = make_user(is_superuser=True)
    r = client.delete(f"{USERS}/me", headers=auth_headers(admin))
    assert r.status_code == 403


# --- GET /{user_id} ----------------------------------------------------------
def test_read_own_user_by_id(client, make_user, auth_headers):
    user = make_user()
    r = client.get(f"{USERS}/{user.id}", headers=auth_headers(user))
    assert r.status_code == 200
    assert r.json()["id"] == str(user.id)


def test_user_cannot_read_another_user(client, make_user, auth_headers):
    alice, bob = make_user(), make_user()
    r = client.get(f"{USERS}/{alice.id}", headers=auth_headers(bob))
    assert r.status_code == 403


def test_superuser_can_read_any_user(client, make_user, auth_headers):
    admin, alice = make_user(is_superuser=True), make_user()
    r = client.get(f"{USERS}/{alice.id}", headers=auth_headers(admin))
    assert r.status_code == 200
    assert r.json()["id"] == str(alice.id)


def test_superuser_reading_unknown_user_gets_404(client, make_user, auth_headers):
    admin = make_user(is_superuser=True)
    r = client.get(f"{USERS}/{uuid.uuid4()}", headers=auth_headers(admin))
    assert r.status_code == 404


# --- GET /{email} ------------------------------------------------------------
def test_read_own_user_by_email(client, make_user, auth_headers):
    user = make_user(email="alice@example.com")
    r = client.get(f"{USERS}/alice@example.com", headers=auth_headers(user))
    assert r.status_code == 200
    assert r.json()["id"] == str(user.id)


# --- GET / (superuser) -------------------------------------------------------
def test_superuser_lists_users(client, make_user, auth_headers):
    admin = make_user(is_superuser=True)
    make_user()
    make_user()

    r = client.get(f"{USERS}/", headers=auth_headers(admin))

    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 3
    assert len(body["data"]) == 3
    for user in body["data"]:
        assert_no_secrets(user)


def test_list_users_is_paginated(client, make_user, auth_headers):
    admin = make_user(is_superuser=True)
    for _ in range(4):
        make_user()

    r = client.get(f"{USERS}/", headers=auth_headers(admin), params={"skip": 1, "limit": 2})

    assert r.status_code == 200
    assert r.json()["count"] == 5      # total, not the page size
    assert len(r.json()["data"]) == 2


def test_user_cannot_list_users(client, make_user, auth_headers):
    user = make_user()
    r = client.get(f"{USERS}/", headers=auth_headers(user))
    assert r.status_code == 403


# --- POST / (superuser) ------------------------------------------------------
def test_superuser_creates_user(client, make_user, auth_headers):
    admin = make_user(is_superuser=True)

    r = client.post(
        f"{USERS}/",
        headers=auth_headers(admin),
        json={"email": "created@example.com", "password": "password123", "is_superuser": True},
    )

    assert r.status_code == 200
    assert r.json()["email"] == "created@example.com"
    assert r.json()["is_superuser"] is True
    assert_no_secrets(r.json())


def test_superuser_cannot_create_duplicate_email(client, make_user, auth_headers):
    admin = make_user(is_superuser=True)
    make_user(email="taken@example.com")

    r = client.post(
        f"{USERS}/",
        headers=auth_headers(admin),
        json={"email": "taken@example.com", "password": "password123"},
    )

    assert r.status_code == 400


def test_user_cannot_create_user(client, make_user, auth_headers):
    user = make_user()
    r = client.post(
        f"{USERS}/",
        headers=auth_headers(user),
        json={"email": "created@example.com", "password": "password123"},
    )
    assert r.status_code == 403


# --- PATCH /{user_id} (superuser) --------------------------------------------
def test_superuser_updates_user(client, session, make_user, auth_headers):
    admin, alice = make_user(is_superuser=True), make_user()

    r = client.patch(
        f"{USERS}/{alice.id}",
        headers=auth_headers(admin),
        json={"full_name": "Alice", "password": "reset-password"},
    )

    assert r.status_code == 200
    assert r.json()["full_name"] == "Alice"
    session.refresh(alice)
    assert verify_password("reset-password", alice.hashed_password)[0]


def test_superuser_updating_with_taken_email_fails(client, make_user, auth_headers):
    admin, alice = make_user(is_superuser=True), make_user()
    make_user(email="taken@example.com")

    r = client.patch(
        f"{USERS}/{alice.id}",
        headers=auth_headers(admin),
        json={"email": "taken@example.com"},
    )

    assert r.status_code == 409


def test_superuser_updating_unknown_user_gets_404(client, make_user, auth_headers):
    admin = make_user(is_superuser=True)
    r = client.patch(
        f"{USERS}/{uuid.uuid4()}", headers=auth_headers(admin), json={"full_name": "X"}
    )
    assert r.status_code == 404


def test_user_cannot_update_another_user(client, make_user, auth_headers):
    alice, bob = make_user(), make_user()
    r = client.patch(
        f"{USERS}/{alice.id}", headers=auth_headers(bob), json={"full_name": "Hacked"}
    )
    assert r.status_code == 403


# --- DELETE /{user_id} (superuser) -------------------------------------------
def test_superuser_deletes_user(client, session, make_user, auth_headers):
    admin, alice = make_user(is_superuser=True), make_user()
    alice_id = alice.id

    r = client.delete(f"{USERS}/{alice_id}", headers=auth_headers(admin))

    assert r.status_code == 200
    assert session.get(User, alice_id) is None


def test_superuser_deleting_unknown_user_gets_404(client, make_user, auth_headers):
    admin = make_user(is_superuser=True)
    r = client.delete(f"{USERS}/{uuid.uuid4()}", headers=auth_headers(admin))
    assert r.status_code == 404


def test_superuser_cannot_delete_themselves_by_id(client, make_user, auth_headers):
    admin = make_user(is_superuser=True)
    r = client.delete(f"{USERS}/{admin.id}", headers=auth_headers(admin))
    assert r.status_code == 403


def test_user_cannot_delete_another_user(client, make_user, auth_headers):
    alice, bob = make_user(), make_user()
    r = client.delete(f"{USERS}/{alice.id}", headers=auth_headers(bob))
    assert r.status_code == 403
