# Bibliographic fields on sources

## Goal

A source only had `authors` (a single string), `year`, `edition` and `publisher`, all
required. That is enough for a book, but not for an article, a chapter or a web page, and it
cannot represent several authors, editors or an undated source (« s.d. »).

Give sources a CSL-like model: a type, a title, editors, a container, volume, issue, pages,
DOI, URL and dates, so particules can cite real-world references precisely. Names stay free
text (e.g. `"Feynman, Richard; Leighton, Robert"`), with no structured name model.

## Fields

| Field             | Type                                             | Required |
| ----------------- | ------------------------------------------------ | -------- |
| `type`            | `book` \| `journal_article` \| `book_chapter` \| `web_page` | yes |
| `title`           | string, up to 1024 characters                    | yes      |
| `authors`         | string, up to 1024 characters                    | yes      |
| `editors`         | string, up to 1024 characters                    | no       |
| `container_title` | string, up to 1024 characters                    | per type |
| `volume`, `issue` | string, up to 64 characters                      | no       |
| `pages`           | string, up to 64 characters (e.g. `"45–67"`)     | no       |
| `doi`             | string, up to 255 characters                     | no       |
| `url`             | string, up to 2048 characters                    | per type |
| `published_date`  | date                                             | no       |
| `accessed_date`   | date                                             | no       |
| `year`            | integer, `null` for an undated source            | no       |
| `edition`         | string, up to 255 characters                     | no       |
| `publisher`       | string, up to 255 characters                     | no       |

## Acceptance criteria

- `POST /sources/` accepts the fields above and answers `422` when:
  - `type`, `title` or `authors` is missing, or `type` is not one of the four values;
  - `journal_article` or `book_chapter` has no `container_title`;
  - `web_page` has no `url`;
  - `year` and `published_date` are both given and disagree.
- When `year` is absent and `published_date` is given, `year` is set from the date.
- `PATCH /sources/{id}` applies the same rules to the merged result: a change that would
  leave the source invalid (e.g. switching `type` to `web_page` without a `url`) answers
  `422` and leaves the source unchanged.
- `GET /sources/` is sorted by title, then year, undated sources last.
- The migration keeps existing sources: `type = book`, `title = "Untitled"`, `authors`
  unchanged (widened to 1024 characters). `year`, `edition` and `publisher` become nullable.
- Ownership is unchanged: another user's source answers `404`.
- `docs/api.md` describes the new body, name shapes, rules and ordering.

## Out of scope

- Structured names (family / given / literal) and lists of authors.
- Other CSL types (thesis, report, conference paper…).
- Formatting citations in a style (APA, Chicago…), importing from DOI/BibTeX.
- Searching or sorting by author.
- Validating DOI or URL syntax.

## Test plan

- `tests/unit/models/test_source.py`: `year` derived from `published_date`; `year`/date
  mismatch; required fields for each type; length limits.
- `tests/integration/api/test_source.py`: create with the full body; required and optional
  fields; invalid enum; per-type rules on
  `POST` and on `PATCH` (source unchanged after a refused `PATCH`); `year: null` accepted;
  ordering by title then year, undated last; existing ownership and pagination tests.
- Migration: `alembic upgrade head`, `downgrade -1`, `upgrade head` on the test database with
  an old-style row.
