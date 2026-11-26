# exercises/test-suite/tests/conftest.py
# L11 — Test fixtures
#
# Your task: Set up an isolated test database and override the get_db dependency.

import os
import pytest
from fastapi.testclient import TestClient

# TODO: Import create_engine and StaticPool from sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

# TODO: Import sessionmaker and Session from sqlalchemy.orm
from sqlalchemy.orm import sessionmaker, Session

# Set before app imports: even table creation must not touch the real database.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# TODO: Import Base, get_db from app.database
from app.database import Base, get_db

# TODO: Import the app
from app.main import app


# TODO: Create an in-memory SQLite test engine
# Use StaticPool so the same connection is reused (required for :memory: databases)
# Key concept: We use a SEPARATE in-memory DB for tests so tests never touch
# the real database file.
#
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# TODO: Define a client fixture that:
# 1. Creates all tables in the test DB
# 2. Defines override_get_db() yielding a test session
# 3. Overrides app.dependency_overrides[get_db] = override_get_db
# 4. Uses with TestClient(app) as test_client: yield test_client
# 5. In finally: remove this override, drop tables, dispose the test engine
#
# Key concept — override_dependency pattern:
# FastAPI's dependency_overrides dict lets you replace any dependency with a
# different function for testing. Here we replace get_db (which uses the real
# SQLite file) with override_get_db (which uses :memory:).
# This means ALL endpoints that call Depends(get_db) get the test session instead.

@pytest.fixture
def client():
    """
    Pytest fixture that provides a TestClient with an isolated in-memory DB.

    TODO: Implement using the pattern described above.
    """
    Base.metadata.create_all(bind=test_engine)

    #Before yield setup database, pause and hand off db to endpoint, and python resumes right after yield, enter the finally:bloc and runs db.clsoe() to close connection 
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()

