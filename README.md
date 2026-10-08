# Particule

Knowledge base built on the Zettelkasten method, with semantic tools.

Notes ("particules") are small, atomic units of knowledge, organized in knowledge bases, tagged, linked to each other and to their sources.

## Stack

- [FastAPI](https://fastapi.tiangolo.com/): HTTP API
- [SQLModel](https://sqlmodel.tiangolo.com/): ORM and data models
- [MariaDB](https://mariadb.org/): database, run with Docker
- [uv](https://docs.astral.sh/uv/): dependency and environment management

## Requirements

- Python 3.12+
- uv
- Docker with Docker Compose

## Getting started

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure the environment

Copy the example file and fill in the values:

```bash
cp .env.example .env
```

| Variable           | Description                                   |
| ------------------ | --------------------------------------------- |
| `DB_ROOT_PASSWORD` | MariaDB root password                         |
| `DB_NAME`          | Database name                                 |
| `DB_USER`          | Application database user                     |
| `DB_PASSWORD`      | Application database user password            |
| `DATABASE_URL`     | SQLAlchemy connection URL used by the app     |
| `DATABASE_ECHO`    | `true` to log SQL queries (development only)  |

`DATABASE_URL` must match the database variables:

```env
DATABASE_URL=mysql+pymysql://<DB_USER>:<DB_PASSWORD>@localhost:3306/<DB_NAME>?charset=utf8mb4
```

### 3. Start the database

```bash
docker compose up -d && docker compose ps
```

Wait until the `db` service is `healthy`.

### 4. Start the server

```bash
uv run fastapi dev app/main.py
```

The API is served at http://localhost:8000, with interactive docs at http://localhost:8000/docs.

## Tests

```bash
uv run pytest
```

Tests use an in-memory SQLite database, so they don't need Docker.

## Project structure

```
app/
├── api/          # HTTP routes
├── auth/         # authentication
├── data/         # data access
├── models/       # SQLModel table models
├── services/     # business logic
├── config.py     # settings loaded from .env
├── database.py   # engine and session dependency
└── main.py       # FastAPI application
tests/            # pytest suite
docs/             # documentation
```

## Useful commands

```bash
docker compose exec db mariadb -u <DB_USER> -p <DB_NAME>   # open a SQL shell
docker compose down                                         # stop the database
docker compose down -v                                      # stop and delete all data
```

## License

MIT, see [LICENSE](LICENSE).
