# Particule

Back-end API of Particule: FastAPI + SQLModel on MariaDB, managed with uv. The front end
lives in a separate repository (Particule-UI).

**Language.** Answer the user in French. Write code, comments, docs, commit messages and
PR descriptions in English.

## Product

Particule builds **hybrid knowledge bases**:

1. **Human side.** Personal notes, written with methods that stimulate cognition so
   that the user covers a subject themselves.
2. **Machine side.** Generative AI, embeddings, vector similarity and knowledge
   discovery.
3. **Balance.** The split between cognitive stimulation and agentic automation must be
   deliberate and precise (see [AI features](#ai-features)).
4. **Notions.** Notes are modelled as *particules*, inspired by Zettelkasten. In time
   they should get a model of their own, so avoid hard-coding Zettelkasten assumptions.
5. **Lasting use.** A knowledge base is built to be used again and again, not just as a
   place to take notes.
6. **Publishing.** A knowledge base can be published publicly. This is planned and not
   built yet.

Current scope: auth (JWT), users, and CRUD for knowledge bases, particules, tags, links
and sources. No AI feature is built yet.

## AI features

- The AI part will live in **both** the back end (embeddings, vector search, agents) and
  the front end (some lightweight calls/computations).
- **The user comes first.** The AI suggests and never acts in the user's place. The user
  writes; the AI questions, links, points out gaps and surfaces related particules.
  Never write AI output into a particule without an explicit user action, and keep
  AI-produced content distinguishable from the user's own.
- When designing an AI feature, state how it stimulates the user's thinking rather than
  replacing it.

## Docs & references

- `README.md`: setup, environment variables, useful commands.
- `docs/api.md`: API conventions (auth, ownership, errors, pagination). The route-level
  reference is FastAPI's OpenAPI docs at http://localhost:8000/docs.
- `docs/index.md`: documentation index.

## Architecture (summary)

```
app/
├── api/v1/    # HTTP routes only: parsing, dependencies, status codes, HTTPException
├── auth/      # JWT, password hashing, CurrentUser / SessionDep dependencies
├── data/      # database access: every query lives here
├── models/    # SQLModel tables and API schemas (Base / Create / Update / Public)
├── services/  # business logic (empty for now; semantic/AI features go here)
├── config.py  # settings (pydantic-settings, .env)
├── database.py
└── main.py
alembic/       # migrations
tests/         # unit/ and integration/ (api/, data/), test_migrations.py
```

- **Strict layers.** `api/` → `services/` → `data/` → `models/`. Routes never run
  queries (`session.exec`, `select`) themselves; they call `data/` functions.
- **Ownership by scoping.** Every resource belongs to a user, particules to a knowledge
  base. `data/` functions take the owner (user or an already-checked `KnowledgeBase`)
  and filter by it. Another user's resource answers **404**, never 403, so its
  existence is never revealed. Reuse the `get_owned_*` dependencies in `api/v1/`.

## Implementation rules

- **Explicit text types.** On MySQL/MariaDB a bare `str` table field becomes
  `VARCHAR(255)`. Give every string column either `max_length` or
  `sa_type=Text` (`from sqlmodel import Text`) for free-form text.
- **Models.** Follow the existing `XBase` / `X` (table) / `XCreate` / `XUpdate` /
  `XPublic` pattern. Fields the server owns (ids, `knowledge_base_id`, owner) are never
  accepted from the client.
- **Migrations.** Every schema change gets a new Alembic revision:
  `uv run alembic revision --autogenerate -m "<message>"`, then review and fix the
  generated file (types, data backfill, downgrade). Never edit an existing migration.
- **API docs.** Any added or changed route, or changed convention, updates
  `docs/api.md` in the same change.
- Match the surrounding code: naming, comment density, idioms.

## Build & run

```bash
uv sync                                  # install dependencies
docker compose up -d                     # dev database (port 3306)
uv run alembic upgrade head              # apply migrations
uv run fastapi dev app/main.py           # http://localhost:8000, docs at /docs
```

## Testing

```bash
docker compose --profile test up -d db-test   # throwaway MariaDB, port 3307, tmpfs
uv run pytest
```

- Start `db-test` first: without it, integration tests are **skipped**, not failed.
  Check the summary for skips before claiming tests pass.
- Tests only ever run against `particule_test` (port 3307). Never point them at the dev
  database.
- Every behaviour change adds or updates a test: API contract in
  `tests/integration/api/`, queries in `tests/integration/data/`, pure logic in
  `tests/unit/`.

## Configuration & environment

Settings live in `app/config.py` (pydantic-settings, read from `.env`; see
`.env.example`): `DATABASE_URL`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`,
`BACKEND_CORS_ORIGINS` (defaults to the Vite dev server). `DB_*` variables are only
used by `docker-compose.yml`. Never commit `.env` or real secrets.

## DevOps

TODO

## Development process

- **Git.** Use one branch per feature or task, merged through a pull request. Do not
  work directly on `main`. Commit messages follow Conventional Commits
  (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`), short, imperative and in
  English.
- **What Claude may do without asking:** run tests, start `db-test`, and start the dev
  server to verify a change.
- **Ask first** before committing or adding a dependency (`uv add`).
- **Never** push, and never run `docker compose down -v` (it deletes the dev database
  volume).

## Project management (autonomous programming)

The method is still being defined. Current baseline:

- **Backlog.** Use both a GitHub issue to track a task and a spec file in `specs/` for
  the details: goal, acceptance criteria, out of scope, test plan. The issue links to
  the spec.
- **Cycle for an autonomous task:**
  1. **Spec.** Write or complete the spec with the user and get it validated.
  2. **Plan.** Propose the implementation plan and get it validated.
  3. **Code.** Implement it on a dedicated branch.
  4. **Test.** Write the unit and integration tests listed in the spec's test plan.
  5. **Verify.** Run the tests (with `db-test` up) and run the app to check the
     acceptance criteria.
  6. **PR.** Prepare a PR that links the issue and the spec; the user pushes and opens
     it.
- Do not expand the scope beyond the spec. Record follow-ups as new issues.

## Maintenance

TODO

## Performance

TODO

## Security

- Passwords are hashed with pwdlib (`app/auth/security.py`); never log or return them.
- Ownership rules above are the main access control: every new query must be scoped
  to its owner.
