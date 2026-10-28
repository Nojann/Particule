# Sources: only the title is required

## Goal

Each source type requires fields on top of `title`: `authors` for `book`,
`journal_article`, `book_chapter` and `web_page`, `container_title` for `journal_article`
and `book_chapter`, `url` for `web_page`. A user often wants to record an academic source
before knowing every bibliographic detail, and is refused.

Drop every per-type rule: only `type` and `title` are required, for every type.

## Changes

| Field             | Before                                    | After |
| ----------------- | ----------------------------------------- | ----- |
| `authors`         | required, except for `other`              | optional on every type |
| `container_title` | required for `journal_article`, `book_chapter` | optional on every type |
| `url`             | required for `web_page`                   | optional on every type |

No schema change: these columns are already nullable, so no migration.

## Acceptance criteria

- `POST /sources/` accepts `{type, title}` alone for every type, and stores `null` for the
  missing fields.
- `POST /sources/` still answers `422` when `type` or `title` is missing.
- `PATCH /sources/{id}` accepts setting `authors`, `container_title` or `url` to `null` on
  any type, and changing the type without sending those fields.
- `PATCH` with `title: null` still answers `422` and leaves the source unchanged.
- The `year` / `published_date` rule, ordering, ownership (`404`) and pagination are
  unchanged.
- `docs/api.md` describes `type` and `title` as the only required fields.

## Out of scope

- Removing the `other` type.
- Rejecting empty strings (`""`), as today.
- Any "incomplete source" indicator or completeness check.

## Test plan

- `tests/unit/models/test_source.py`: every type valid with only `type` and `title`, also
  with explicit `null`s; `type` and `title` still required.
- `tests/integration/api/test_source.py`: create each type with only a title (`201`, `null`s
  stored); create a `book` with `authors: null` (`201`); missing `type` or `title` (`422`);
  `PATCH` `authors: null` on a `book` accepted; `PATCH` a `book` to `web_page` without `url`
  accepted; `PATCH` an `other` without authors to `book` accepted.
