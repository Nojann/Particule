"""API tests for /login routes (app/api/v1/login.py).

The only tests that obtain a token through the real login endpoint. Other API
tests build their tokens directly with the `auth_headers` fixture.
"""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.auth.security import ALGORITHM
from app.config import settings


def make_token(sub: str, expires_in: timedelta = timedelta(minutes=5), key: str | None = None) -> str:
    """Build a JWT by hand, to test tokens the app would never issue itself."""
    payload = {"sub": sub, "exp": datetime.now(UTC) + expires_in}
    return jwt.encode(payload, key or settings.SECRET_KEY, algorithm=ALGORITHM)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# --- POST /login/access-token ------------------------------------------------
def test_login_returns_bearer_token(client, make_user):
    user = make_user(email="alice@example.com", password="alice-password")

    # OAuth2 password flow: form data, and the email goes in `username`.
    r = client.post("/api/v1/login/access-token", data={"username": "alice@example.com", "password": "alice-password"})

    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"

    payload = jwt.decode(body["access_token"], settings.SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == str(user.id)


def test_login_token_expires_after_configured_delay(client, make_user):
    make_user(email="alice@example.com", password="alice-password")

    r = client.post("/api/v1/login/access-token", data={"username": "alice@example.com", "password": "alice-password"})

    payload = jwt.decode(r.json()["access_token"], settings.SECRET_KEY, algorithms=[ALGORITHM])
    expires_at = datetime.fromtimestamp(payload["exp"], UTC)
    expected = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    assert abs(expires_at - expected) < timedelta(minutes=1)


def test_login_token_gives_access_to_protected_routes(client, make_user):
    """End to end: log in, then use the token."""
    user = make_user(email="alice@example.com", password="alice-password")
    r = client.post("/api/v1/login/access-token", data={"username": "alice@example.com", "password": "alice-password"})
    token = r.json()["access_token"]

    r = client.post("/api/v1/login/test-token", headers=bearer(token))

    assert r.status_code == 200
    assert r.json()["id"] == str(user.id)


def test_login_with_wrong_password_fails(client, make_user):
    make_user(email="alice@example.com", password="alice-password")
    r = client.post("/api/v1/login/access-token", data={"username": "alice@example.com", "password": "wrong-password"})
    assert r.status_code == 400


def test_login_with_unknown_email_fails(client):
    r = client.post("/api/v1/login/access-token", data={"username": "nobody@example.com", "password": "any-password"})
    assert r.status_code == 400


def test_login_errors_do_not_reveal_whether_email_exists(client, make_user):
    """Same response for a wrong password and an unknown email (no user enumeration)."""
    make_user(email="alice@example.com", password="alice-password")

    wrong_password = client.post(
        "/api/v1/login/access-token", data={"username": "alice@example.com", "password": "wrong-password"}
    )
    unknown_email = client.post(
        "/api/v1/login/access-token", data={"username": "nobody@example.com", "password": "wrong-password"}
    )

    assert wrong_password.status_code == unknown_email.status_code
    assert wrong_password.json() == unknown_email.json()


def test_login_of_inactive_user_fails(client, make_user):
    make_user(email="alice@example.com", password="alice-password", is_active=False)
    r = client.post("/api/v1/login/access-token", data={"username": "alice@example.com", "password": "alice-password"})
    assert r.status_code == 400


@pytest.mark.parametrize(
    "data",
    [{"username": "alice@example.com"}, {"password": "alice-password"}, {}],
    ids=["missing-password", "missing-username", "empty"],
)
def test_login_with_missing_fields_fails(client, data):
    r = client.post("/api/v1/login/access-token", data=data)
    assert r.status_code == 422


def test_login_does_not_accept_json(client, make_user):
    # OAuth2 requires form data; a JSON body is a client error, not a login.
    make_user(email="alice@example.com", password="alice-password")
    r = client.post("/api/v1/login/access-token", json={"username": "alice@example.com", "password": "alice-password"})
    assert r.status_code == 422


# --- POST /login/test-token --------------------------------------------------
def test_test_token_returns_current_user(client, make_user, auth_headers):
    user = make_user()

    r = client.post("/api/v1/login/test-token", headers=auth_headers(user))

    assert r.status_code == 200
    assert r.json()["id"] == str(user.id)
    assert "hashed_password" not in r.json()


def test_test_token_without_token_fails(client):
    r = client.post("/api/v1/login/test-token")
    assert r.status_code == 401


def test_expired_token_is_rejected(client, make_user):
    user = make_user()
    token = make_token(str(user.id), expires_in=timedelta(minutes=-1))

    r = client.post("/api/v1/login/test-token", headers=bearer(token))

    assert r.status_code == 403


def test_token_signed_with_another_key_is_rejected(client, make_user):
    """A forged token: valid structure and user id, but not signed by us."""
    user = make_user()
    token = make_token(str(user.id), key="attacker-key-of-sufficient-length-32b")

    r = client.post("/api/v1/login/test-token", headers=bearer(token))

    assert r.status_code == 403


def test_unsigned_token_is_rejected(client, make_user):
    """`alg: none` attack: a token with no signature at all."""
    user = make_user()
    payload = {"sub": str(user.id), "exp": datetime.now(UTC) + timedelta(minutes=5)}
    token = jwt.encode(payload, key=None, algorithm="none")

    r = client.post("/api/v1/login/test-token", headers=bearer(token))

    assert r.status_code == 403


def test_token_of_unknown_user_is_rejected(client):
    r = client.post("/api/v1/login/test-token", headers=bearer(make_token(str(uuid.uuid4()))))
    assert r.status_code == 404


def test_token_with_malformed_subject_is_rejected(client):
    """A `sub` that is not a UUID must be a clean 403, not a server error."""
    r = client.post("/api/v1/login/test-token", headers=bearer(make_token("not-a-uuid")))
    assert r.status_code == 403
