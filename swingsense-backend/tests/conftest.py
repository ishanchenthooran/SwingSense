import os
import sys
import uuid

import pytest
from fastapi import Header
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.core.auth import get_current_user  # noqa: E402
from app.main import app  # noqa: E402

TEST_USER_ID = str(uuid.uuid4())
TEST_USER_EMAIL = "test@example.com"

# Requires `alembic upgrade head` to already have been run against DATABASE_URL.
engine = create_engine(settings.DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    """
    Wrap each test in an outer transaction + SAVEPOINT so nothing the test
    (or the app code under test, which calls session.commit()) writes
    survives past the test.
    """
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture()
def make_client(db_session):
    """
    Each returned TestClient carries its own X-Test-User-* headers, so
    multiple "logged in as" clients can coexist and be used in any order
    within a test — identity travels with the request, not with mutable
    global state on `app`.
    """

    def override_get_db():
        yield db_session

    def override_get_current_user(
        x_test_user_id: str = Header(default=TEST_USER_ID),
        x_test_user_email: str = Header(default=TEST_USER_EMAIL),
    ):
        return {"user_id": x_test_user_id, "email": x_test_user_email}

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    created = []

    def _make(user_id: str = TEST_USER_ID, email: str = TEST_USER_EMAIL) -> TestClient:
        client = TestClient(
            app,
            headers={"X-Test-User-Id": user_id, "X-Test-User-Email": email},
        )
        created.append(client)
        return client

    yield _make

    app.dependency_overrides.clear()
    for c in created:
        c.close()


@pytest.fixture()
def client(make_client):
    return make_client()


@pytest.fixture()
def test_user_id() -> str:
    return TEST_USER_ID
