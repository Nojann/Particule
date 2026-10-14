# Database migrations

The database schema is managed with [Alembic](https://alembic.sqlalchemy.org/).
Migrations are generated from the SQLModel models in `app/models/` and stored in `alembic/versions/`.

## Prerequisites

- Dependencies installed: `uv sync`
- `.env` configured with `DATABASE_URL` (see the README)
- Database running: `docker compose up -d`

Alembic reads the connection URL from `app.config.settings`, so the `sqlalchemy.url` value in `alembic.ini` is ignored.

## Apply migrations

Bring the database up to the latest schema:

```bash
uv run alembic upgrade head
```

Run this after cloning the project and after pulling changes that add new migrations.

## Create a migration

1. Change or add a model in `app/models/`.
2. If it is a new table model, import it in `app/models/__init__.py` so Alembic can see it.
3. Generate the migration:

   ```bash
   uv run alembic revision --autogenerate -m "add created_at to user"
   ```

4. **Review the generated file** in `alembic/versions/` (see [Pitfalls](#pitfalls)).
5. Apply it:

   ```bash
   uv run alembic upgrade head
   ```

6. Commit the migration file together with the model change.

## Useful commands

| Command                                         | Description                                   |
| ----------------------------------------------- | --------------------------------------------- |
| `uv run alembic upgrade head`                   | Apply all pending migrations                  |
| `uv run alembic downgrade -1`                   | Revert the last migration                     |
| `uv run alembic downgrade base`                 | Revert every migration (empties the schema)   |
| `uv run alembic current`                        | Show the revision the database is at          |
| `uv run alembic history --verbose`              | List all migrations                           |
| `uv run alembic check`                          | Fail if the models differ from the migrations |
| `uv run alembic upgrade head --sql`             | Print the SQL without running it              |
| `uv run alembic stamp head`                     | Mark the database as up to date, run nothing  |

## Pitfalls

- **Renames are not detected.** Renaming a column or table is generated as a drop plus an add, which loses the data. Edit the migration to use `op.alter_column(..., new_column_name=...)` or `op.rename_table(...)` instead.
- **Models must be imported.** Autogenerate only sees tables registered on `SQLModel.metadata`. A model missing from `app/models/__init__.py` will be generated as a dropped table.
- **SQLModel types.** `str` fields use `sqlmodel.sql.sqltypes.AutoString`. The template `alembic/script.py.mako` already imports `sqlmodel.sql.sqltypes`, so do not remove that import.
- **Downgrades.** Check that `downgrade()` really reverses `upgrade()`, and fill it in by hand when autogenerate leaves it incomplete.
- **Do not use `create_all`.** `create_db_and_tables()` in `app/database.py` bypasses Alembic. Tables created that way are not tracked and the next `upgrade` will fail on existing tables.

## Reset the development database

To start over from an empty schema:

```bash
uv run alembic downgrade base
uv run alembic upgrade head
```

If the database was created outside Alembic (for example with `create_all`), drop the Docker volume instead:

```bash
docker compose down -v
docker compose up -d
uv run alembic upgrade head
```

This deletes all data.
