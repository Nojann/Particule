<p align="center">
  <img src="docs/assets/particule-icon.svg" alt="Particule" width="96" height="96">
</p>

<h1 align="center">Particule</h1>

<p align="center">
  <strong>A knowledge base you build yourself, with an AI that makes you think instead of thinking for you.</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/python-3.12+-blue" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/status-early%20development-orange" alt="Status: early development">
</p>


## How it works

**Particules.** Each note is a *particule*: a small, self-contained piece of knowledge.
You link particules to each other, tag them and attach the sources they come from. The
model is inspired by Zettelkasten, without being locked into it.

**Knowledge bases.** Particules live in knowledge bases, one per subject or project. A
knowledge base is meant to be reopened, reread and extended over years, not filled once
and forgotten.

**Sources.** Books, articles, chapters, web pages, podcasts, conversations. Record what
you know now: a title is enough, the rest can come later. Add your own note on why the
source matters.

**A human side and a machine side.** Writing methods that push you to cover a subject
yourself, combined with embeddings, vector similarity and knowledge discovery. The balance
between the two is deliberate: the AI supports your thinking, it does not replace it.

## Status

Particule is in early development. This repository is the back-end API.

| Available now                                        | Planned                                     |
| ---------------------------------------------------- | ------------------------------------------- |
| Accounts and authentication (JWT)                    | Semantic search across your particules      |
| Knowledge bases, particules, tags, links, sources    | AI suggestions: questions, gaps, related notes |
| Bibliographic sources with a personal note           | Public publishing of a knowledge base       |

The web interface lives in a separate repository, **Particule-UI**.

## Getting started

You need Python 3.12+, [uv](https://docs.astral.sh/uv/) and Docker with Docker Compose.

```bash
uv sync                          # install dependencies
cp .env.example .env             # then fill in the values (see below)
docker compose up -d             # start MariaDB, wait until "healthy"
uv run alembic upgrade head      # create the schema
uv run fastapi dev app/main.py   # start the API
```

The API runs at http://localhost:8000, with interactive docs at http://localhost:8000/docs.

### Configuration

| Variable                      | Description                                        |
| ----------------------------- | -------------------------------------------------- |
| `DB_ROOT_PASSWORD`            | MariaDB root password (Docker only)                |
| `DB_NAME`                     | Database name (Docker only)                        |
| `DB_USER`, `DB_PASSWORD`      | Application database user (Docker only)            |
| `DATABASE_URL`                | SQLAlchemy connection URL used by the app          |
| `DATABASE_ECHO`               | `true` to log SQL queries (development only)       |
| `SECRET_KEY`                  | Key used to sign tokens                            |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime (2 days by default)                 |
| `BACKEND_CORS_ORIGINS`        | Allowed front-end origins (Vite dev server by default) |

`DATABASE_URL` must match the database variables:

```env
DATABASE_URL=mysql+pymysql://<DB_USER>:<DB_PASSWORD>@localhost:3306/<DB_NAME>?charset=utf8mb4
```

## Development

### Tests

```bash
docker compose --profile test up -d db-test   # throwaway MariaDB on port 3307, in memory
uv run pytest
```

Without `db-test`, integration tests are skipped, not failed: check the summary.

### Stack

[FastAPI](https://fastapi.tiangolo.com/) for the HTTP API,
[SQLModel](https://sqlmodel.tiangolo.com/) for models and data access,
[MariaDB](https://mariadb.org/) for storage, [Alembic](https://alembic.sqlalchemy.org/)
for migrations, [uv](https://docs.astral.sh/uv/) for dependencies.

### Project structure

```
app/
├── api/v1/       # HTTP routes
├── auth/         # JWT, password hashing
├── data/         # database queries
├── models/       # SQLModel tables and API schemas
├── services/     # business logic, future AI features
├── config.py     # settings loaded from .env
├── database.py   # engine and session
└── main.py       # FastAPI application
alembic/          # migrations
tests/            # unit and integration tests
docs/             # documentation
```

More in [`docs/`](docs/index.md): [API conventions](docs/api.md),
[migrations](docs/migrations.md), [testing](docs/testing.md).

### Useful commands

```bash
docker compose exec db mariadb -u <DB_USER> -p <DB_NAME>   # open a SQL shell
docker compose down                                         # stop the database
docker compose down -v                                      # stop and delete all data
```

## License

MIT, see [LICENSE](LICENSE).
