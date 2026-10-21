"""API tests for /sources routes (app/api/v1/source.py).

Focus: HTTP contract and ownership. Sources belong to a user; another user's
sources answer 404, like ids that don't exist.
"""

import uuid

import pytest

from app.models import Particule, Source

URL = "/api/v1/sources"


def source_payload(**overrides) -> dict:
    payload = {
        "authors": "Richard Feynman",
        "year": 1964,
        "edition": "1st",
        "publisher": "Addison-Wesley",
    }
    payload.update(overrides)
    return payload


# --- Authentication ----------------------------------------------------------
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/"),
        ("post", "/"),
        ("get", f"/{uuid.uuid4()}"),
        ("patch", f"/{uuid.uuid4()}"),
        ("delete", f"/{uuid.uuid4()}"),
    ],
)
def test_routes_require_a_token(client, method, path):
    r = client.request(method, f"{URL}{path}")
    assert r.status_code == 401


# --- GET / -------------------------------------------------------------------
def test_list_is_empty_for_new_user(client, make_user, auth_headers):
    user = make_user()

    r = client.get(f"{URL}/", headers=auth_headers(user))

    assert r.status_code == 200
    assert r.json() == []


def test_list_returns_only_own_sources(client, make_user, make_source, auth_headers):
    alice, bob = make_user(), make_user()
    feynman = make_source(owner=alice, authors="Feynman")
    landau = make_source(owner=alice, authors="Landau")
    make_source(owner=bob, authors="Bob")

    r = client.get(f"{URL}/", headers=auth_headers(alice))

    assert r.status_code == 200
    assert {s["id"] for s in r.json()} == {str(feynman.id), str(landau.id)}


def test_list_is_sorted_by_authors_then_year(client, make_user, make_source, auth_headers):
    user = make_user()
    make_source(owner=user, authors="Landau", year=1960)
    make_source(owner=user, authors="Feynman", year=1965)
    make_source(owner=user, authors="Feynman", year=1963)

    r = client.get(f"{URL}/", headers=auth_headers(user))

    assert [(s["authors"], s["year"]) for s in r.json()] == [
        ("Feynman", 1963),
        ("Feynman", 1965),
        ("Landau", 1960),
    ]


def test_list_is_paginated(client, make_user, make_source, auth_headers):
    user = make_user()
    for authors in ["A", "B", "C", "D"]:
        make_source(owner=user, authors=authors)

    r = client.get(f"{URL}/", headers=auth_headers(user), params={"skip": 1, "limit": 2})

    assert r.status_code == 200
    assert [s["authors"] for s in r.json()] == ["B", "C"]


# --- POST / ------------------------------------------------------------------
def test_create_source(client, session, make_user, auth_headers):
    user = make_user()
    payload = source_payload()

    r = client.post(f"{URL}/", headers=auth_headers(user), json=payload)

    assert r.status_code == 201
    body = r.json()
    for field, value in payload.items():
        assert body[field] == value
    assert body["owner_id"] == str(user.id)

    source = session.get(Source, uuid.UUID(body["id"]))
    assert source is not None
    assert source.owner_id == user.id


def test_create_ignores_owner_id_from_client(client, make_user, auth_headers):
    """The owner is always the authenticated user, whatever the body says."""
    alice, bob = make_user(), make_user()

    r = client.post(f"{URL}/", headers=auth_headers(bob), json=source_payload(owner_id=str(alice.id)))

    assert r.status_code == 201
    assert r.json()["owner_id"] == str(bob.id)


def test_create_ignores_id_from_client(client, make_user, auth_headers):
    user = make_user()
    chosen_id = str(uuid.uuid4())

    r = client.post(f"{URL}/", headers=auth_headers(user), json=source_payload(id=chosen_id))

    assert r.status_code == 201
    assert r.json()["id"] != chosen_id


def test_same_source_can_be_created_twice(client, make_user, auth_headers):
    """Unlike tags and links, sources have no uniqueness rule."""
    user = make_user()
    headers = auth_headers(user)

    first = client.post(f"{URL}/", headers=headers, json=source_payload())
    second = client.post(f"{URL}/", headers=headers, json=source_payload())

    assert first.status_code == second.status_code == 201
    assert first.json()["id"] != second.json()["id"]


@pytest.mark.parametrize("missing", ["authors", "year", "edition", "publisher"])
def test_create_rejects_missing_field(client, make_user, auth_headers, missing):
    user = make_user()
    payload = source_payload()
    del payload[missing]

    r = client.post(f"{URL}/", headers=auth_headers(user), json=payload)

    assert r.status_code == 422


def test_create_rejects_non_integer_year(client, make_user, auth_headers):
    user = make_user()
    r = client.post(f"{URL}/", headers=auth_headers(user), json=source_payload(year="sixties"))
    assert r.status_code == 422


# --- GET /{source_id} --------------------------------------------------------
def test_read_own_source(client, make_user, make_source, auth_headers):
    user = make_user()
    source = make_source(owner=user, authors="Feynman")

    r = client.get(f"{URL}/{source.id}", headers=auth_headers(user))

    assert r.status_code == 200
    assert r.json()["id"] == str(source.id)
    assert r.json()["authors"] == "Feynman"


def test_cannot_read_another_users_source(client, make_user, make_source, auth_headers):
    alice, bob = make_user(), make_user()
    source = make_source(owner=alice)

    r = client.get(f"{URL}/{source.id}", headers=auth_headers(bob))

    # 404, not 403: don't reveal that the id exists.
    assert r.status_code == 404


def test_read_unknown_source_gets_404(client, make_user, auth_headers):
    user = make_user()
    r = client.get(f"{URL}/{uuid.uuid4()}", headers=auth_headers(user))
    assert r.status_code == 404


def test_read_with_malformed_id_gets_422(client, make_user, auth_headers):
    user = make_user()
    r = client.get(f"{URL}/not-a-uuid", headers=auth_headers(user))
    assert r.status_code == 422


# --- PATCH /{source_id} ------------------------------------------------------
def test_update_source(client, session, make_user, make_source, auth_headers):
    user = make_user()
    source = make_source(owner=user, edition="1st")

    r = client.patch(f"{URL}/{source.id}", headers=auth_headers(user), json={"edition": "2nd"})

    assert r.status_code == 200
    assert r.json()["edition"] == "2nd"
    session.refresh(source)
    assert source.edition == "2nd"


def test_update_keeps_fields_not_sent(client, make_user, make_source, auth_headers):
    user = make_user()
    source = make_source(owner=user, authors="Feynman", year=1964)

    r = client.patch(f"{URL}/{source.id}", headers=auth_headers(user), json={"edition": "2nd"})

    assert r.status_code == 200
    assert r.json()["authors"] == "Feynman"
    assert r.json()["year"] == 1964


def test_cannot_update_another_users_source(client, session, make_user, make_source, auth_headers):
    alice, bob = make_user(), make_user()
    source = make_source(owner=alice, authors="Feynman")

    r = client.patch(f"{URL}/{source.id}", headers=auth_headers(bob), json={"authors": "Hijacked"})

    assert r.status_code == 404
    session.refresh(source)
    assert source.authors == "Feynman"


# --- DELETE /{source_id} -----------------------------------------------------
def test_delete_own_source(client, session, make_user, make_source, auth_headers):
    user = make_user()
    source_id = make_source(owner=user).id

    r = client.delete(f"{URL}/{source_id}", headers=auth_headers(user))

    assert r.status_code == 204
    assert r.content == b""
    assert session.get(Source, source_id) is None


def test_delete_source_keeps_its_particules(
    client, session, make_user, make_kb, make_source, make_particule, auth_headers
):
    """Particule.source_id is ON DELETE SET NULL: the particule survives, unlinked."""
    user = make_user()
    source = make_source(owner=user)
    particule = make_particule(kb=make_kb(owner=user), source_id=source.id)

    r = client.delete(f"{URL}/{source.id}", headers=auth_headers(user))

    assert r.status_code == 204
    session.expire_all()
    particule = session.get(Particule, particule.id)
    assert particule is not None
    assert particule.source_id is None


def test_cannot_delete_another_users_source(client, session, make_user, make_source, auth_headers):
    alice, bob = make_user(), make_user()
    source_id = make_source(owner=alice).id

    r = client.delete(f"{URL}/{source_id}", headers=auth_headers(bob))

    assert r.status_code == 404
    assert session.get(Source, source_id) is not None


def test_delete_unknown_source_gets_404(client, make_user, auth_headers):
    user = make_user()
    r = client.delete(f"{URL}/{uuid.uuid4()}", headers=auth_headers(user))
    assert r.status_code == 404
