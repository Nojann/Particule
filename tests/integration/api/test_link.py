"""API tests for /links routes (app/api/v1/link.py).

Focus: HTTP contract and ownership. Links belong to a user: two users can have
the same link, a user can't have it twice. Another user's links answer 404,
like ids that don't exist.
"""

import uuid

import pytest

from app.models import Link

URL = "/api/v1/links"


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


def test_list_returns_only_own_links(client, make_user, make_link, auth_headers):
    alice, bob = make_user(), make_user()
    wiki = make_link(owner=alice, link="https://en.wikipedia.org")
    arxiv = make_link(owner=alice, link="https://arxiv.org")
    make_link(owner=bob, link="https://bob.example.com")

    r = client.get(f"{URL}/", headers=auth_headers(alice))

    assert r.status_code == 200
    assert {link["id"] for link in r.json()} == {str(wiki.id), str(arxiv.id)}


def test_list_is_sorted_by_url(client, make_user, make_link, auth_headers):
    user = make_user()
    for url in ["https://c.example.com", "https://a.example.com", "https://b.example.com"]:
        make_link(owner=user, link=url)

    r = client.get(f"{URL}/", headers=auth_headers(user))

    assert [link["link"] for link in r.json()] == [
        "https://a.example.com",
        "https://b.example.com",
        "https://c.example.com",
    ]


def test_list_is_paginated(client, make_user, make_link, auth_headers):
    user = make_user()
    for name in ["a", "b", "c", "d"]:
        make_link(owner=user, link=f"https://{name}.example.com")

    r = client.get(f"{URL}/", headers=auth_headers(user), params={"skip": 1, "limit": 2})

    assert r.status_code == 200
    assert [link["link"] for link in r.json()] == ["https://b.example.com", "https://c.example.com"]


# --- POST / ------------------------------------------------------------------
def test_create_link(client, session, make_user, auth_headers):
    user = make_user()

    r = client.post(f"{URL}/", headers=auth_headers(user), json={"link": "https://arxiv.org"})

    assert r.status_code == 201
    body = r.json()
    assert body["link"] == "https://arxiv.org"
    assert body["owner_id"] == str(user.id)

    link = session.get(Link, uuid.UUID(body["id"]))
    assert link is not None
    assert link.owner_id == user.id


def test_create_ignores_owner_id_from_client(client, make_user, auth_headers):
    """The owner is always the authenticated user, whatever the body says."""
    alice, bob = make_user(), make_user()

    r = client.post(
        f"{URL}/",
        headers=auth_headers(bob),
        json={"link": "https://planted.example.com", "owner_id": str(alice.id)},
    )

    assert r.status_code == 201
    assert r.json()["owner_id"] == str(bob.id)


def test_create_ignores_id_from_client(client, make_user, auth_headers):
    user = make_user()
    chosen_id = str(uuid.uuid4())

    r = client.post(
        f"{URL}/", headers=auth_headers(user), json={"link": "https://arxiv.org", "id": chosen_id}
    )

    assert r.status_code == 201
    assert r.json()["id"] != chosen_id


def test_create_existing_link_gets_409(client, make_user, make_link, auth_headers):
    user = make_user()
    make_link(owner=user, link="https://arxiv.org")

    r = client.post(f"{URL}/", headers=auth_headers(user), json={"link": "https://arxiv.org"})

    assert r.status_code == 409


def test_two_users_can_have_the_same_link(client, make_user, make_link, auth_headers):
    alice, bob = make_user(), make_user()
    make_link(owner=alice, link="https://arxiv.org")

    r = client.post(f"{URL}/", headers=auth_headers(bob), json={"link": "https://arxiv.org"})

    assert r.status_code == 201


@pytest.mark.parametrize(
    "payload",
    [{}, {"link": None}, {"link": ""}],
    ids=["missing-link", "null-link", "empty-link"],
)
def test_create_rejects_invalid_payload(client, make_user, auth_headers, payload):
    user = make_user()
    r = client.post(f"{URL}/", headers=auth_headers(user), json=payload)
    assert r.status_code == 422


# --- GET /{link_id} ----------------------------------------------------------
def test_read_own_link(client, make_user, make_link, auth_headers):
    user = make_user()
    link = make_link(owner=user, link="https://arxiv.org")

    r = client.get(f"{URL}/{link.id}", headers=auth_headers(user))

    assert r.status_code == 200
    assert r.json()["id"] == str(link.id)
    assert r.json()["link"] == "https://arxiv.org"


def test_cannot_read_another_users_link(client, make_user, make_link, auth_headers):
    alice, bob = make_user(), make_user()
    link = make_link(owner=alice)

    r = client.get(f"{URL}/{link.id}", headers=auth_headers(bob))

    # 404, not 403: don't reveal that the id exists.
    assert r.status_code == 404


def test_read_unknown_link_gets_404(client, make_user, auth_headers):
    user = make_user()
    r = client.get(f"{URL}/{uuid.uuid4()}", headers=auth_headers(user))
    assert r.status_code == 404


def test_read_with_malformed_id_gets_422(client, make_user, auth_headers):
    user = make_user()
    r = client.get(f"{URL}/not-a-uuid", headers=auth_headers(user))
    assert r.status_code == 422


# --- PATCH /{link_id} --------------------------------------------------------
def test_update_link(client, session, make_user, make_link, auth_headers):
    user = make_user()
    link = make_link(owner=user, link="http://arxiv.org")

    r = client.patch(f"{URL}/{link.id}", headers=auth_headers(user), json={"link": "https://arxiv.org"})

    assert r.status_code == 200
    assert r.json()["link"] == "https://arxiv.org"
    session.refresh(link)
    assert link.link == "https://arxiv.org"


def test_update_to_same_url_is_allowed(client, make_user, make_link, auth_headers):
    user = make_user()
    link = make_link(owner=user, link="https://arxiv.org")

    r = client.patch(f"{URL}/{link.id}", headers=auth_headers(user), json={"link": "https://arxiv.org"})

    assert r.status_code == 200


def test_update_to_existing_link_gets_409(client, make_user, make_link, auth_headers):
    user = make_user()
    make_link(owner=user, link="https://arxiv.org")
    link = make_link(owner=user, link="https://en.wikipedia.org")

    r = client.patch(f"{URL}/{link.id}", headers=auth_headers(user), json={"link": "https://arxiv.org"})

    assert r.status_code == 409


def test_cannot_update_another_users_link(client, session, make_user, make_link, auth_headers):
    alice, bob = make_user(), make_user()
    link = make_link(owner=alice, link="https://arxiv.org")

    r = client.patch(
        f"{URL}/{link.id}", headers=auth_headers(bob), json={"link": "https://hijacked.example.com"}
    )

    assert r.status_code == 404
    session.refresh(link)
    assert link.link == "https://arxiv.org"


# --- DELETE /{link_id} -------------------------------------------------------
def test_delete_own_link(client, session, make_user, make_link, auth_headers):
    user = make_user()
    link_id = make_link(owner=user).id

    r = client.delete(f"{URL}/{link_id}", headers=auth_headers(user))

    assert r.status_code == 204
    assert r.content == b""
    assert session.get(Link, link_id) is None


def test_cannot_delete_another_users_link(client, session, make_user, make_link, auth_headers):
    alice, bob = make_user(), make_user()
    link_id = make_link(owner=alice).id

    r = client.delete(f"{URL}/{link_id}", headers=auth_headers(bob))

    assert r.status_code == 404
    assert session.get(Link, link_id) is not None


def test_delete_unknown_link_gets_404(client, make_user, auth_headers):
    user = make_user()
    r = client.delete(f"{URL}/{uuid.uuid4()}", headers=auth_headers(user))
    assert r.status_code == 404
