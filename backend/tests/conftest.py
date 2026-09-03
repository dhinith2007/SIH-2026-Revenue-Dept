import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal, is_db_available
from app.db.seed import seed_database


@pytest.fixture(autouse=True, scope="module")
def reset_test_state():
    """Ensures deterministic demo dataset baseline is restored before each test module."""
    if is_db_available():
        with SessionLocal() as db:
            seed_database(db=db, refresh_apps=True)
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

