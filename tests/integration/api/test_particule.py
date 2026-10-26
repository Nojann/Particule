"""API tests for /knowledge-bases/{kb_id}/particules routes (app/api/v1/particule.py).

Focus: HTTP contract and ownership. Particules are reached through their
knowledge base: another user's knowledge base, or a particule of another
knowledge base, answers 404 like ids that don't exist.
"""

import uuid

import pytest

from app.models import Particule


def particules_url(kb_id, suffix: str = "") -> str:
    return f"/api/v1/knowledge-bases/{kb_id}/particules{suffix}"


def particule_payload(**overrides) -> dict:
    payload = {
        "title": "Entropy",
        "permalink": f"entropy-{uuid.uuid4().hex[:8]}",
        "content": "A measure of disorder.",
        "origins": "Thermodynamics course",
    }
    payload.update(overrides)
    return payload


# --- Authentication ----------------------------------------------------------
@pytest.mark.parametrize(
    ("method", "suffix"),
    [
        ("get", "/"),
        ("post", "/"),
        ("get", f"/{uuid.uuid4()}"),
        ("get", "/by-permalink/some-permalink"),
        ("patch", f"/{uuid.uuid4()}"),
        ("delete", f"/{uuid.uuid4()}"),
    ],
)
def test_routes_require_a_token(client, method, suffix):
    r = client.request(method, particules_url(uuid.uuid4(), suffix))
    assert r.status_code == 401


# --- Knowledge base ownership ------------------------------------------------
@pytest.mark.parametrize(
    ("method", "suffix", "json"),
    [
        ("get", "/", None),
        ("post", "/", particule_payload()),
        ("get", "/{pid}", None),
        ("get", "/by-permalink/{permalink}", None),
        ("patch", "/{pid}", {"title": "Hijacked"}),
        ("delete", "/{pid}", None),
    ],
)
def test_another_users_knowledge_base_gets_404(
    client, make_user, make_kb, make_particule, auth_headers, method, suffix, json
):
    alice, bob = make_user(), make_user()
    kb = make_kb(owner=alice)
    particule = make_particule(kb=kb)
    path = suffix.format(pid=particule.id, permalink=particule.permalink)

    r = client.request(method, particules_url(kb.id, path), headers=auth_headers(bob), json=json)

    # 404, not 403: don't reveal that the knowledge base exists.
    assert r.status_code == 404


def test_unknown_knowledge_base_gets_404(client, make_user, auth_headers):
    user = make_user()
    r = client.get(particules_url(uuid.uuid4(), "/"), headers=auth_headers(user))
    assert r.status_code == 404


def test_malformed_knowledge_base_id_gets_422(client, make_user, auth_headers):
    user = make_user()
    r = client.get(particules_url("not-a-uuid", "/"), headers=auth_headers(user))
    assert r.status_code == 422


# --- GET / -------------------------------------------------------------------
def test_list_is_empty_for_new_knowledge_base(client, make_user, make_kb, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)

    r = client.get(particules_url(kb.id, "/"), headers=auth_headers(user))

    assert r.status_code == 200
    assert r.json() == []


def test_list_returns_only_particules_of_the_knowledge_base(
    client, make_user, make_kb, make_particule, auth_headers
):
    user = make_user()
    physics, maths = make_kb(owner=user), make_kb(owner=user)
    entropy = make_particule(kb=physics, title="Entropy")
    energy = make_particule(kb=physics, title="Energy")
    make_particule(kb=maths, title="Integral")

    r = client.get(particules_url(physics.id, "/"), headers=auth_headers(user))

    assert r.status_code == 200
    assert {p["id"] for p in r.json()} == {str(entropy.id), str(energy.id)}


def test_list_is_sorted_by_title(client, make_user, make_kb, make_particule, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)
    for title in ["Charlie", "Alpha", "Bravo"]:
        make_particule(kb=kb, title=title)

    r = client.get(particules_url(kb.id, "/"), headers=auth_headers(user))

    assert [p["title"] for p in r.json()] == ["Alpha", "Bravo", "Charlie"]


def test_list_is_paginated(client, make_user, make_kb, make_particule, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)
    for title in ["A", "B", "C", "D"]:
        make_particule(kb=kb, title=title)

    r = client.get(
        particules_url(kb.id, "/"), headers=auth_headers(user), params={"skip": 1, "limit": 2}
    )

    assert r.status_code == 200
    assert [p["title"] for p in r.json()] == ["B", "C"]


# --- POST / ------------------------------------------------------------------
def test_create_particule(client, session, make_user, make_kb, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)
    payload = particule_payload()

    r = client.post(particules_url(kb.id, "/"), headers=auth_headers(user), json=payload)

    assert r.status_code == 201
    body = r.json()
    for field in ["title", "permalink", "content", "origins"]:
        assert body[field] == payload[field]
    assert body["knowledge_base_id"] == str(kb.id)
    assert body["source_id"] is None

    particule = session.get(Particule, uuid.UUID(body["id"]))
    assert particule is not None
    assert particule.knowledge_base_id == kb.id


def test_create_particule_with_long_content(client, make_user, make_kb, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)
    payload = particule_payload(content="x" * 5000)

    r = client.post(particules_url(kb.id, "/"), headers=auth_headers(user), json=payload)

    assert r.status_code == 201
    assert r.json()["content"] == payload["content"]


def test_created_particule_appears_in_list(client, make_user, make_kb, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)
    headers = auth_headers(user)

    created = client.post(particules_url(kb.id, "/"), headers=headers, json=particule_payload()).json()
    listed = client.get(particules_url(kb.id, "/"), headers=headers).json()

    assert [p["id"] for p in listed] == [created["id"]]


def test_create_ignores_knowledge_base_id_from_client(client, make_user, make_kb, auth_headers):
    """The knowledge base always comes from the URL, whatever the body says."""
    alice, bob = make_user(), make_user()
    alice_kb, bob_kb = make_kb(owner=alice), make_kb(owner=bob)

    r = client.post(
        particules_url(bob_kb.id, "/"),
        headers=auth_headers(bob),
        json=particule_payload(knowledge_base_id=str(alice_kb.id)),
    )

    assert r.status_code == 201
    assert r.json()["knowledge_base_id"] == str(bob_kb.id)


def test_create_ignores_id_from_client(client, make_user, make_kb, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)
    chosen_id = str(uuid.uuid4())

    r = client.post(
        particules_url(kb.id, "/"), headers=auth_headers(user), json=particule_payload(id=chosen_id)
    )

    assert r.status_code == 201
    assert r.json()["id"] != chosen_id


def test_create_with_existing_permalink_gets_409(
    client, make_user, make_kb, make_particule, auth_headers
):
    user = make_user()
    kb = make_kb(owner=user)
    make_particule(kb=kb, permalink="entropy")

    r = client.post(
        particules_url(kb.id, "/"), headers=auth_headers(user), json=particule_payload(permalink="entropy")
    )

    assert r.status_code == 409


def test_create_with_permalink_used_in_another_knowledge_base_gets_409(
    client, make_user, make_kb, make_particule, auth_headers
):
    """Permalinks are unique across all knowledge bases, not per knowledge base."""
    user = make_user()
    make_particule(kb=make_kb(), permalink="entropy")
    kb = make_kb(owner=user)

    r = client.post(
        particules_url(kb.id, "/"), headers=auth_headers(user), json=particule_payload(permalink="entropy")
    )

    assert r.status_code == 409


@pytest.mark.parametrize(
    "missing",
    ["title", "permalink", "content", "origins"],
)
def test_create_rejects_missing_field(client, make_user, make_kb, auth_headers, missing):
    user = make_user()
    kb = make_kb(owner=user)
    payload = particule_payload()
    del payload[missing]

    r = client.post(particules_url(kb.id, "/"), headers=auth_headers(user), json=payload)

    assert r.status_code == 422


# --- GET /{particule_id} -----------------------------------------------------
def test_read_own_particule(client, make_user, make_kb, make_particule, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)
    particule = make_particule(kb=kb, title="Entropy")

    r = client.get(particules_url(kb.id, f"/{particule.id}"), headers=auth_headers(user))

    assert r.status_code == 200
    assert r.json()["id"] == str(particule.id)
    assert r.json()["title"] == "Entropy"


def test_read_particule_through_wrong_knowledge_base_gets_404(
    client, make_user, make_kb, make_particule, auth_headers
):
    """Both knowledge bases are the user's, but the particule isn't in this one."""
    user = make_user()
    physics, maths = make_kb(owner=user), make_kb(owner=user)
    particule = make_particule(kb=physics)

    r = client.get(particules_url(maths.id, f"/{particule.id}"), headers=auth_headers(user))

    assert r.status_code == 404


def test_read_unknown_particule_gets_404(client, make_user, make_kb, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)
    r = client.get(particules_url(kb.id, f"/{uuid.uuid4()}"), headers=auth_headers(user))
    assert r.status_code == 404


def test_read_with_malformed_particule_id_gets_422(client, make_user, make_kb, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)
    r = client.get(particules_url(kb.id, "/not-a-uuid"), headers=auth_headers(user))
    assert r.status_code == 422


# --- GET /by-permalink/{permalink} -------------------------------------------
def test_read_particule_by_permalink(client, make_user, make_kb, make_particule, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)
    particule = make_particule(kb=kb, permalink="entropy")

    r = client.get(particules_url(kb.id, "/by-permalink/entropy"), headers=auth_headers(user))

    assert r.status_code == 200
    assert r.json()["id"] == str(particule.id)


def test_read_by_permalink_through_wrong_knowledge_base_gets_404(
    client, make_user, make_kb, make_particule, auth_headers
):
    user = make_user()
    physics, maths = make_kb(owner=user), make_kb(owner=user)
    make_particule(kb=physics, permalink="entropy")

    r = client.get(particules_url(maths.id, "/by-permalink/entropy"), headers=auth_headers(user))

    assert r.status_code == 404


def test_read_unknown_permalink_gets_404(client, make_user, make_kb, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)
    r = client.get(particules_url(kb.id, "/by-permalink/nothing-here"), headers=auth_headers(user))
    assert r.status_code == 404


# --- PATCH /{particule_id} ---------------------------------------------------
def test_update_particule(client, session, make_user, make_kb, make_particule, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)
    particule = make_particule(kb=kb, title="Old", content="Old content")

    r = client.patch(
        particules_url(kb.id, f"/{particule.id}"),
        headers=auth_headers(user),
        json={"title": "New", "content": "New content"},
    )

    assert r.status_code == 200
    assert r.json()["title"] == "New"
    assert r.json()["content"] == "New content"
    session.refresh(particule)
    assert particule.title == "New"


def test_update_keeps_fields_not_sent(client, make_user, make_kb, make_particule, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)
    particule = make_particule(kb=kb, title="Old", origins="Kept origins")

    r = client.patch(
        particules_url(kb.id, f"/{particule.id}"), headers=auth_headers(user), json={"title": "New"}
    )

    assert r.status_code == 200
    assert r.json()["origins"] == "Kept origins"
    assert r.json()["permalink"] == particule.permalink


def test_update_with_own_permalink_is_allowed(
    client, make_user, make_kb, make_particule, auth_headers
):
    user = make_user()
    kb = make_kb(owner=user)
    particule = make_particule(kb=kb, permalink="entropy")

    r = client.patch(
        particules_url(kb.id, f"/{particule.id}"),
        headers=auth_headers(user),
        json={"permalink": "entropy"},
    )

    assert r.status_code == 200


def test_update_with_taken_permalink_gets_409(
    client, make_user, make_kb, make_particule, auth_headers
):
    user = make_user()
    kb = make_kb(owner=user)
    make_particule(kb=kb, permalink="entropy")
    particule = make_particule(kb=kb, permalink="energy")

    r = client.patch(
        particules_url(kb.id, f"/{particule.id}"),
        headers=auth_headers(user),
        json={"permalink": "entropy"},
    )

    assert r.status_code == 409


def test_update_cannot_move_particule_to_another_knowledge_base(
    client, session, make_user, make_kb, make_particule, auth_headers
):
    alice, bob = make_user(), make_user()
    bob_kb, alice_kb = make_kb(owner=bob), make_kb(owner=alice)
    particule = make_particule(kb=bob_kb)

    r = client.patch(
        particules_url(bob_kb.id, f"/{particule.id}"),
        headers=auth_headers(bob),
        json={"knowledge_base_id": str(alice_kb.id)},
    )

    assert r.status_code == 200
    session.refresh(particule)
    assert particule.knowledge_base_id == bob_kb.id


def test_update_particule_through_wrong_knowledge_base_gets_404(
    client, session, make_user, make_kb, make_particule, auth_headers
):
    user = make_user()
    physics, maths = make_kb(owner=user), make_kb(owner=user)
    particule = make_particule(kb=physics, title="Old")

    r = client.patch(
        particules_url(maths.id, f"/{particule.id}"), headers=auth_headers(user), json={"title": "New"}
    )

    assert r.status_code == 404
    session.refresh(particule)
    assert particule.title == "Old"


# --- DELETE /{particule_id} --------------------------------------------------
def test_delete_own_particule(client, session, make_user, make_kb, make_particule, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)
    particule_id = make_particule(kb=kb).id

    r = client.delete(particules_url(kb.id, f"/{particule_id}"), headers=auth_headers(user))

    assert r.status_code == 204
    assert r.content == b""
    assert session.get(Particule, particule_id) is None


def test_delete_particule_through_wrong_knowledge_base_gets_404(
    client, session, make_user, make_kb, make_particule, auth_headers
):
    user = make_user()
    physics, maths = make_kb(owner=user), make_kb(owner=user)
    particule_id = make_particule(kb=physics).id

    r = client.delete(particules_url(maths.id, f"/{particule_id}"), headers=auth_headers(user))

    assert r.status_code == 404
    assert session.get(Particule, particule_id) is not None


def test_delete_unknown_particule_gets_404(client, make_user, make_kb, auth_headers):
    user = make_user()
    kb = make_kb(owner=user)
    r = client.delete(particules_url(kb.id, f"/{uuid.uuid4()}"), headers=auth_headers(user))
    assert r.status_code == 404


def test_deleted_particule_is_no_longer_readable(
    client, make_user, make_kb, make_particule, auth_headers
):
    user = make_user()
    kb = make_kb(owner=user)
    particule_id = make_particule(kb=kb).id
    headers = auth_headers(user)

    client.delete(particules_url(kb.id, f"/{particule_id}"), headers=headers)
    r = client.get(particules_url(kb.id, f"/{particule_id}"), headers=headers)

    assert r.status_code == 404
