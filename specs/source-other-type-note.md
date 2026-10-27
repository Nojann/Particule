# `other` source type and source note

## Goal

The four source types (`book`, `journal_article`, `book_chapter`, `web_page`) do not cover
every reference a user cites: a podcast, a conversation, a lecture, a personal document…
These often have no identifiable author, yet `authors` is required.

Add a catch-all `other` type whose `authors` is optional, and a free-text `note` on every
source, where the user records in their own words what the source is, why it matters or
where they found it.

## Changes

| Field     | Change                                                                   |
| --------- | ------------------------------------------------------------------------ |
| `type`    | new value `other`                                                        |
| `authors` | optional (may be absent or `null`) for `other`; still required for the other types |
| `note`    | new, optional on every type, free text (`TEXT` column), `null` by default |

`other` requires only `type` and `title`: no `container_title` or `url` rule.

## Acceptance criteria

- `POST /sources/` accepts `type: "other"` without `authors`, and stores `authors: null`.
- `POST /sources/` still answers `422` when `authors` is missing or `null` for `book`,
  `journal_article`, `book_chapter` or `web_page`.
- `note` is accepted on every type, on `POST` and `PATCH`, and returned in every source
  response (`null` when not set). `PATCH` with `note: null` clears it.
- `PATCH /sources/{id}` applies the rules to the merged result:
  - setting `authors: null` on an `other` source is accepted;
  - switching an `other` source without authors to another type, without sending
    `authors`, answers `422` and leaves the source unchanged.
- The existing rules (per-type `container_title` / `url`, `year` / `published_date`),
  ordering, ownership (`404`) and pagination are unchanged.
- The migration keeps existing sources unchanged, with `note = null`.
- `docs/api.md` describes the `other` type, the optional `authors` and `note`.

## Out of scope

- A sub-type or free-text label for `other` (podcast, lecture…).
- Any AI processing of `note` (summary, suggestions…).
- Searching or sorting by `note` or `authors`.
- Rejecting an empty string `authors` (`""`), as today.

## Test plan

- `tests/unit/models/test_source.py`: `other` valid with only `title`; `authors` missing or
  `null` refused for each other type; `note` accepted on every type.
- `tests/integration/api/test_source.py`: create `other` without authors (`authors: null` in
  the response); create a `book` without authors (`422`); `note` on create, update and clear;
  `PATCH` `authors: null` on `other` accepted, on `book` refused; `PATCH` switching `other`
  without authors to `book` refused and source unchanged.
- Migration: `alembic upgrade head`, `downgrade -1`, `upgrade head` on the test database.
  The downgrade is lossy: `note` is dropped, `other` sources become `book` and a `null`
  `authors` becomes `''`.
