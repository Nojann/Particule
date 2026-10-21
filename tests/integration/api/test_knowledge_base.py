"""API tests for /knowledge-bases routes (app/api/v1/knowledge_base.py).

Focus: HTTP contract and ownership. A user must never see, nor even detect,
another user's knowledge bases: those answer 404, like ids that don't exist.
Detailed query logic belongs in tests/integration/data/test_knowledge_base.py.
"""

import uuid

import pytest

from app.models import KnowledgeBase


# --- Authentication ----------------------------------------------------------
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/"),
        ("post", "/"),
        ("get", f"/{uuid.uuid4()}"),
        ("delete", f"/{uuid.uuid4()}"),
    ],
)
def test_routes_require_a_token(client, method, path):
    r = client.request(method, f"/api/v1/knowledge-bases{path}")
    assert r.status_code == 401


# --- GET / -------------------------------------------------------------------
def test_list_is_empty_for_new_user(client, make_user, auth_headers):
    user = make_user()

    r = client.get("/api/v1/knowledge-bases/", headers=auth_headers(user))

    assert r.status_code == 200
    assert r.json() == []


def test_list_returns_only_own_knowledge_bases(client, make_user, make_kb, auth_headers):
    alice, bob = make_user(), make_user()
    physics = make_kb(owner=alice, name="Physics")
    maths = make_kb(owner=alice, name="Maths")
    make_kb(owner=bob, name="Bob's notes")

    r = client.get("/api/v1/knowledge-bases/", headers=auth_headers(alice))

    assert r.status_code == 200
    assert {kb["id"] for kb in r.json()} == {str(physics.id), str(maths.id)}


# --- POST / ------------------------------------------------------------------
def test_create_knowledge_base(client, session, make_user, auth_headers):
    user = make_user()

    r = client.post("/api/v1/knowledge-bases/", headers=auth_headers(user), json={"name": "Physics"})

    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Physics"
    assert body["owner_id"] == str(user.id)
    assert body["created_at"] is not None

    kb = session.get(KnowledgeBase, uuid.UUID(body["id"]))
    assert kb is not None
    assert kb.owner_id == user.id


def test_created_knowledge_base_appears_in_list(client, make_user, auth_headers):
    user = make_user()
    headers = auth_headers(user)

    created = client.post("/api/v1/knowledge-bases/", headers=headers, json={"name": "Physics"}).json()
    listed = client.get("/api/v1/knowledge-bases/", headers=headers).json()

    assert [kb["id"] for kb in listed] == [created["id"]]


def test_create_ignores_owner_id_from_client(client, make_user, auth_headers):
    """The owner is always the authenticated user, whatever the body says."""
    alice, bob = make_user(), make_user()

    r = client.post(
        "/api/v1/knowledge-bases/",
        headers=auth_headers(bob),
        json={"name": "Planted", "owner_id": str(alice.id)},
    )

    assert r.status_code == 201
    assert r.json()["owner_id"] == str(bob.id)


def test_create_ignores_id_from_client(client, make_user, auth_headers):
    user = make_user()
    chosen_id = str(uuid.uuid4())

    r = client.post(
        "/api/v1/knowledge-bases/", headers=auth_headers(user), json={"name": "Physics", "id": chosen_id}
    )

    assert r.status_code == 201
    assert r.json()["id"] != chosen_id


@pytest.mark.parametrize(
    "payload",
    [{}, {"name": None}, {"name": "x" * 256}],
    ids=["missing-name", "null-name", "name-too-long"],
)
def test_create_rejects_invalid_payload(client, make_user, auth_headers, payload):
    user = make_user()
    r = client.post("/api/v1/knowledge-bases/", headers=auth_headers(user), json=payload)
    assert r.status_code == 422


# --- GET /{kb_id} ------------------------------------------------------------
def test_read_own_knowledge_base(client, make_user, make_kb, auth_headers):
    user = make_user()
    kb = make_kb(owner=user, name="Physics")

    r = client.get(f"/api/v1/knowledge-bases/{kb.id}", headers=auth_headers(user))

    assert r.status_code == 200
    assert r.json()["id"] == str(kb.id)
    assert r.json()["name"] == "Physics"


def test_cannot_read_another_users_knowledge_base(client, make_user, make_kb, auth_headers):
    alice, bob = make_user(), make_user()
    kb = make_kb(owner=alice)

    r = client.get(f"/api/v1/knowledge-bases/{kb.id}", headers=auth_headers(bob))

    # 404, not 403: don't reveal that the id exists.
    assert r.status_code == 404


def test_read_unknown_knowledge_base_gets_404(client, make_user, auth_headers):
    user = make_user()
    r = client.get(f"/api/v1/knowledge-bases/{uuid.uuid4()}", headers=auth_headers(user))
    assert r.status_code == 404


def test_read_with_malformed_id_gets_422(client, make_user, auth_headers):
    user = make_user()
    r = client.get("/api/v1/knowledge-bases/not-a-uuid", headers=auth_headers(user))
    assert r.status_code == 422


# --- DELETE /{kb_id} ---------------------------------------------------------
def test_delete_own_knowledge_base(client, session, make_user, make_kb, auth_headers):
    user = make_user()
    kb_id = make_kb(owner=user).id

    r = client.delete(f"/api/v1/knowledge-bases/{kb_id}", headers=auth_headers(user))

    assert r.status_code == 204
    assert r.content == b""
    assert session.get(KnowledgeBase, kb_id) is None


def test_cannot_delete_another_users_knowledge_base(
    client, session, make_user, make_kb, auth_headers
):
    alice, bob = make_user(), make_user()
    kb_id = make_kb(owner=alice).id

    r = client.delete(f"/api/v1/knowledge-bases/{kb_id}", headers=auth_headers(bob))

    assert r.status_code == 404
    assert session.get(KnowledgeBase, kb_id) is not None


def test_delete_unknown_knowledge_base_gets_404(client, make_user, auth_headers):
    user = make_user()
    r = client.delete(f"/api/v1/knowledge-bases/{uuid.uuid4()}", headers=auth_headers(user))
    assert r.status_code == 404


def test_deleted_knowledge_base_is_no_longer_readable(client, make_user, make_kb, auth_headers):
    user = make_user()
    kb_id = make_kb(owner=user).id
    headers = auth_headers(user)

    client.delete(f"/api/v1/knowledge-bases/{kb_id}", headers=headers)
    r = client.get(f"/api/v1/knowledge-bases/{kb_id}", headers=headers)

    assert r.status_code == 404
