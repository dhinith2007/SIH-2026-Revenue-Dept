import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal, is_db_available
from app.db.seed import seed_database


from datetime import datetime, timezone

@pytest.fixture(autouse=True)
def reset_test_state():
    """Ensures deterministic demo dataset baseline is restored before each test case."""

    if is_db_available():
        with SessionLocal() as db:
            seed_database(db=db, refresh_apps=True)
    from app.repositories.user_repository import _MEM_USERS
    from app.repositories.application_repository import _MEM_APPLICATIONS
    from app.db.seed import get_seeded_users_with_hashes
    from app.db.seed_applications import get_seeded_applications
    _MEM_USERS.clear()
    for u in get_seeded_users_with_hashes():
        _MEM_USERS[u["id"]] = {
            **u,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "last_login_at": None,
            "failed_login_attempts": 0,
            "locked_until": None,
        }
    _MEM_APPLICATIONS.clear()
    for app_item in get_seeded_applications():
        _MEM_APPLICATIONS[app_item["application_id"]] = app_item
    yield



from app.core.rate_limit import reset_rate_limiter


@pytest.fixture(autouse=True)
def reset_rate_limit_fixture():
    """Resets authentication rate limiter between test cases."""
    reset_rate_limiter()
    yield
    reset_rate_limiter()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client

