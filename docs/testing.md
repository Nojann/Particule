# Testing

Tests use [pytest](https://docs.pytest.org/) and follow the three layers of the application:

```
api (app/api/v1)  →  data (app/data)  →  models (app/models)  →  MariaDB
```

Each behavior is tested thoroughly in one layer only. For example, "user A cannot see user B's knowledge base" is tested in detail in the data layer, and the API has a single test checking that the 404 comes through.

## Prerequisites

- Dependencies installed, including the dev group: `uv sync`
- For integration tests: the test database running (see [Test database](#test-database))

## Run the tests

```bash
docker compose --profile test up -d --wait db-test   # once per session
uv run pytest                          # everything
uv run pytest tests/unit               # unit tests only, no database needed
uv run pytest -m "not integration"     # same, selected by marker
uv run pytest tests/integration/api    # one folder
uv run pytest tests/integration/api/test_user.py::test_read_me_returns_current_user   # one test
```

Useful options:

| Option              | Description                                        |
| ------------------- | -------------------------------------------------- |
| `-x`                | Stop at the first failure                          |
| `-k "signup"`       | Run only tests whose name contains `signup`        |
| `--lf`              | Rerun only the tests that failed last time         |
| `-v`                | Show each test name                                |
| `-s`                | Show `print()` output                              |
| `--pdb`             | Open the debugger on failure                       |

Integration tests are **skipped** when the test database is unreachable. Run `uv run pytest -rs` to see why tests were skipped.

## Test database

Integration tests run against MariaDB, not SQLite. UUID storage, datetime timezones, collations and constraints behave differently in SQLite, and a test that passes there can still fail in production.

They use a **dedicated, throwaway container**, `db-test` in `docker-compose.yml`, separate from the development database:

```bash
docker compose --profile test up -d --wait db-test   # start (waits until ready)
docker compose --profile test stop db-test           # stop
```

| Setting  | Value                                                                  |
| -------- | ---------------------------------------------------------------------- |
| Host     | `localhost:3307`                                                       |
| Database | `particule_test`                                                       |
| User     | `particule` / `particule`                                              |
| URL      | `mysql+pymysql://particule:particule@localhost:3307/particule_test`    |

- **Open credentials on purpose.** The container holds no real data, so there is nothing to protect and no setup to do. The values are committed as defaults in `tests/conftest.py`.
- **Data lives in memory** (`tmpfs`): fast, and gone when the container stops.
- **The `test` profile** keeps it out of a plain `docker compose up`.
- **Real environment variables override the defaults**, for example in CI: `TEST_DATABASE_URL=... uv run pytest`.

During the test run, `DATABASE_URL` is replaced by `TEST_DATABASE_URL`, and `SECRET_KEY` gets a fixed test value. Your development database is never touched. The run also refuses to start on a database whose name does not contain `test`, because it drops and recreates every table.

## Layout

```
tests/
├── conftest.py                  # environment only (DATABASE_URL, SECRET_KEY)
├── unit/                        # no database, no app import, runs in milliseconds
│   ├── models/                  # validation rules, defaults
│   └── auth/                    # password hashing, JWT
├── integration/                 # needs MariaDB, marked `integration` automatically
│   ├── conftest.py              # engine, session, factories, auth_headers
│   ├── data/                    # queries, ownership filters, persistence
│   └── api/
│       ├── conftest.py          # client
│       └── test_*.py            # status codes, response shape, access control
└── test_migrations.py           # Alembic migrations match the models
```

Fixtures are defined in the `conftest.py` closest to where they are used, and pytest makes them available to every test in that folder and below, without imports. Test files can share a name across folders (`--import-mode=importlib` in `pyproject.toml`).

## Fixtures

| Fixture         | Where                   | Description                                                                 |
| --------------- | ----------------------- | --------------------------------------------------------------------------- |
| `engine`        | `integration/`          | Connects to the test database and recreates the schema, once per run        |
| `session`       | `integration/`          | Database session; everything the test does is rolled back afterwards        |
| `make_user`     | `integration/`          | Factory: `make_user()`, `make_user(is_superuser=True, password="...")`      |
| `make_kb`       | `integration/`          | Factory: `make_kb(owner=alice, name="Physics")`                             |
| `auth_headers`  | `integration/`          | `auth_headers(user)` returns a header with a real signed JWT                |
| `client`        | `integration/api/`      | FastAPI `TestClient` that uses the test `session`                           |

### Isolation

Each test runs inside a transaction that is rolled back at the end. The data layer still calls `session.commit()`, but those commits only release a savepoint inside that transaction. Every test starts from an empty database, whatever the previous one did, and tests can run in any order.

The `client` fixture overrides the `get_db` dependency, so the API and the factories share the same session: rows created with `make_user` are visible to the API, and rows created through the API can be checked with `session`.

## Write a test

Use the factories to create exactly the data the test needs, then follow Arrange / Act / Assert:

```python
def test_user_cannot_read_another_user(client, make_user, auth_headers):
    # Arrange
    alice, bob = make_user(), make_user()

    # Act
    r = client.get(f"/api/v1/users/{alice.id}", headers=auth_headers(bob))

    # Assert
    assert r.status_code == 403
```

Guidelines:

- **One behavior per test**, with a name that reads as a sentence (`test_signup_with_existing_email_fails`).
- **Test the right layer.** Query logic goes in `integration/data/`, HTTP contract and access control in `integration/api/`, validation and defaults in `unit/models/`.
- **Do not mock your own code.** Use the real database and real tokens. Only mock what leaves the process (email, external APIs, LLM calls).
- **Check that secrets never leak:** no `password` or `hashed_password` in a response.
- **Test access control on every route:** no token (401), another user's data (403/404), non-superuser on admin routes (403).
- **Reproduce a bug with a test before fixing it.**
- **Do not import from `conftest.py`.** Pass explicit values instead, for example `make_user(password="old-password")`.

## Pitfalls

- **`Settings` loads at import time.** Anything that sets environment variables for tests must run before `app.*` is imported, which is why it lives in the root `conftest.py`.
- **Objects expire after a commit.** After an API call that changed a row, call `session.refresh(obj)` before reading its attributes, or fetch it again with `session.get(...)`.
- **Keep IDs before deleting.** Read `user.id` into a variable before the call that deletes `user`, then check `session.get(User, user_id) is None`.
- **Route order matters.** FastAPI matches routes in declaration order, so `GET /users/{user_id}` declared before `GET /users/me` catches `/me` and returns 422. Declare fixed paths before parameterized ones.
- **The schema comes from `create_all`, not Alembic,** in the test database. `test_migrations.py` checks that the migrations produce the same schema.
