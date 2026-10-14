"""Root conftest: environment shared by every test (unit and integration).

pytest loads conftest.py files from the root down, so this one runs before
any test module or nested conftest imports `app.*`.

Fixtures live in the conftest closest to where they are used:
    tests/integration/conftest.py       engine, session, factories, auth_headers
    tests/integration/api/conftest.py   client
"""

import os

# Open values on purpose: they are not secrets, they only match the throwaway
# `db-test` service in docker-compose.yml. setdefault: a real environment
# variable wins, so CI can point elsewhere.
os.environ.setdefault(
    "TEST_DATABASE_URL",
    "mysql+pymysql://particule:particule@localhost:3307/particule_test",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

# `app.config` builds `Settings()` at import time, and environment variables
# take precedence over .env. Pointing DATABASE_URL at the test database means
# even code that bypasses dependency injection and uses `app.database.engine`
# directly never touches the dev one.
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
