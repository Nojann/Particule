"""API tests for /tags routes (app/api/v1/tag.py).

Focus: HTTP contract and ownership. Tags belong to a user: two users can have
the same tag, a user can't have it twice. Another user's tags answer 404,
like ids that don't exist.
"""

import uuid

import pytest

from app.models import Tag

URL = "/api/v1/tags"


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


def test_list_returns_only_own_tags(client, make_user, make_tag, auth_headers):
    alice, bob = make_user(), make_user()
    physics = make_tag(owner=alice, tag="physics")
    maths = make_tag(owner=alice, tag="maths")
    make_tag(owner=bob, tag="bob-tag")

    r = client.get(f"{URL}/", headers=auth_headers(alice))

    assert r.status_code == 200
    assert {t["id"] for t in r.json()} == {str(physics.id), str(maths.id)}


def test_list_is_sorted_by_name(client, make_user, make_tag, auth_headers):
    user = make_user()
    for name in ["charlie", "alpha", "bravo"]:
        make_tag(owner=user, tag=name)

    r = client.get(f"{URL}/", headers=auth_headers(user))

    assert [t["tag"] for t in r.json()] == ["alpha", "bravo", "charlie"]


def test_list_is_paginated(client, make_user, make_tag, auth_headers):
    user = make_user()
    for name in ["a", "b", "c", "d"]:
        make_tag(owner=user, tag=name)

    r = client.get(f"{URL}/", headers=auth_headers(user), params={"skip": 1, "limit": 2})

    assert r.status_code == 200
    assert [t["tag"] for t in r.json()] == ["b", "c"]


# --- POST / ------------------------------------------------------------------
def test_create_tag(client, session, make_user, auth_headers):
    user = make_user()

    r = client.post(f"{URL}/", headers=auth_headers(user), json={"tag": "physics"})

    assert r.status_code == 201
    body = r.json()
    assert body["tag"] == "physics"
    assert body["owner_id"] == str(user.id)

    tag = session.get(Tag, uuid.UUID(body["id"]))
    assert tag is not None
    assert tag.owner_id == user.id


def test_create_ignores_owner_id_from_client(client, make_user, auth_headers):
    """The owner is always the authenticated user, whatever the body says."""
    alice, bob = make_user(), make_user()

    r = client.post(
        f"{URL}/", headers=auth_headers(bob), json={"tag": "planted", "owner_id": str(alice.id)}
    )

    assert r.status_code == 201
    assert r.json()["owner_id"] == str(bob.id)


def test_create_ignores_id_from_client(client, make_user, auth_headers):
    user = make_user()
    chosen_id = str(uuid.uuid4())

    r = client.post(f"{URL}/", headers=auth_headers(user), json={"tag": "physics", "id": chosen_id})

    assert r.status_code == 201
    assert r.json()["id"] != chosen_id


def test_create_existing_tag_gets_409(client, make_user, make_tag, auth_headers):
    user = make_user()
    make_tag(owner=user, tag="physics")

    r = client.post(f"{URL}/", headers=auth_headers(user), json={"tag": "physics"})

    assert r.status_code == 409


def test_two_users_can_have_the_same_tag(client, make_user, make_tag, auth_headers):
    alice, bob = make_user(), make_user()
    make_tag(owner=alice, tag="physics")

    r = client.post(f"{URL}/", headers=auth_headers(bob), json={"tag": "physics"})

    assert r.status_code == 201


@pytest.mark.parametrize(
    "payload",
    [{}, {"tag": None}, {"tag": ""}, {"tag": "x" * 256}],
    ids=["missing-tag", "null-tag", "empty-tag", "tag-too-long"],
)
def test_create_rejects_invalid_payload(client, make_user, auth_headers, payload):
    user = make_user()
    r = client.post(f"{URL}/", headers=auth_headers(user), json=payload)
    assert r.status_code == 422


# --- GET /{tag_id} -----------------------------------------------------------
def test_read_own_tag(client, make_user, make_tag, auth_headers):
    user = make_user()
    tag = make_tag(owner=user, tag="physics")

    r = client.get(f"{URL}/{tag.id}", headers=auth_headers(user))

    assert r.status_code == 200
    assert r.json()["id"] == str(tag.id)
    assert r.json()["tag"] == "physics"


def test_cannot_read_another_users_tag(client, make_user, make_tag, auth_headers):
    alice, bob = make_user(), make_user()
    tag = make_tag(owner=alice)

    r = client.get(f"{URL}/{tag.id}", headers=auth_headers(bob))

    # 404, not 403: don't reveal that the id exists.
    assert r.status_code == 404


def test_read_unknown_tag_gets_404(client, make_user, auth_headers):
    user = make_user()
    r = client.get(f"{URL}/{uuid.uuid4()}", headers=auth_headers(user))
    assert r.status_code == 404


def test_read_with_malformed_id_gets_422(client, make_user, auth_headers):
    user = make_user()
    r = client.get(f"{URL}/not-a-uuid", headers=auth_headers(user))
    assert r.status_code == 422


# --- PATCH /{tag_id} ---------------------------------------------------------
def test_rename_tag(client, session, make_user, make_tag, auth_headers):
    user = make_user()
    tag = make_tag(owner=user, tag="phyiscs")

    r = client.patch(f"{URL}/{tag.id}", headers=auth_headers(user), json={"tag": "physics"})

    assert r.status_code == 200
    assert r.json()["tag"] == "physics"
    session.refresh(tag)
    assert tag.tag == "physics"


def test_rename_to_same_name_is_allowed(client, make_user, make_tag, auth_headers):
    user = make_user()
    tag = make_tag(owner=user, tag="physics")

    r = client.patch(f"{URL}/{tag.id}", headers=auth_headers(user), json={"tag": "physics"})

    assert r.status_code == 200


def test_rename_to_existing_tag_gets_409(client, make_user, make_tag, auth_headers):
    user = make_user()
    make_tag(owner=user, tag="physics")
    tag = make_tag(owner=user, tag="maths")

    r = client.patch(f"{URL}/{tag.id}", headers=auth_headers(user), json={"tag": "physics"})

    assert r.status_code == 409


def test_rename_to_another_users_tag_name_is_allowed(client, make_user, make_tag, auth_headers):
    alice, bob = make_user(), make_user()
    make_tag(owner=alice, tag="physics")
    tag = make_tag(owner=bob, tag="maths")

    r = client.patch(f"{URL}/{tag.id}", headers=auth_headers(bob), json={"tag": "physics"})

    assert r.status_code == 200


def test_cannot_rename_another_users_tag(client, session, make_user, make_tag, auth_headers):
    alice, bob = make_user(), make_user()
    tag = make_tag(owner=alice, tag="physics")

    r = client.patch(f"{URL}/{tag.id}", headers=auth_headers(bob), json={"tag": "hijacked"})

    assert r.status_code == 404
    session.refresh(tag)
    assert tag.tag == "physics"


# --- DELETE /{tag_id} --------------------------------------------------------
def test_delete_own_tag(client, session, make_user, make_tag, auth_headers):
    user = make_user()
    tag_id = make_tag(owner=user).id

    r = client.delete(f"{URL}/{tag_id}", headers=auth_headers(user))

    assert r.status_code == 204
    assert r.content == b""
    assert session.get(Tag, tag_id) is None


def test_cannot_delete_another_users_tag(client, session, make_user, make_tag, auth_headers):
    alice, bob = make_user(), make_user()
    tag_id = make_tag(owner=alice).id

    r = client.delete(f"{URL}/{tag_id}", headers=auth_headers(bob))

    assert r.status_code == 404
    assert session.get(Tag, tag_id) is not None


def test_delete_unknown_tag_gets_404(client, make_user, auth_headers):
    user = make_user()
    r = client.delete(f"{URL}/{uuid.uuid4()}", headers=auth_headers(user))
    assert r.status_code == 404
