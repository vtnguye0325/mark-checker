import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

_MODEL_DIR = Path(__file__).resolve().parents[1] / "backend" / "model"


@pytest.fixture(autouse=True)
def _auth_and_db_overrides():
    """Batch C put a session and a database write on the three check routes.

    The API tests have no Postgres and no Google sign-in, so override
    ``current_user`` with a fixed user and ``get_session`` with a session whose
    writes are no-ops. ``update_query_stage`` reads ``result.rowcount``, so the
    fake ``execute`` returns a row count of 1.
    """
    from app.auth import SessionUser, current_user
    from app.db import get_session
    from app.main import app

    test_user = SessionUser(id=uuid.uuid4(), email="test@example.com")

    class _FakeSession:
        def add(self, _obj):
            pass

        async def commit(self):
            pass

        async def rollback(self):
            pass

        async def execute(self, *_args, **_kwargs):
            result = MagicMock()
            result.rowcount = 1
            return result

    async def _fake_get_session():
        yield _FakeSession()

    app.dependency_overrides[current_user] = lambda: test_user
    app.dependency_overrides[get_session] = _fake_get_session
    yield
    app.dependency_overrides.pop(current_user, None)
    app.dependency_overrides.pop(get_session, None)


def pytest_collection_modifyitems(items: list) -> None:
    """Skip model-dependent tests when backend/model/ is absent."""
    if _MODEL_DIR.exists():
        return
    skip = pytest.mark.skip(reason="backend/model/ not present")
    for item in items:
        fname = item.fspath.basename
        tname = item.name
        if fname == "test_model_predictions.py":
            item.add_marker(skip)
        elif fname == "test_model_service.py" and not tname.startswith("test_explain_one"):
            item.add_marker(skip)
        elif fname == "test_api.py" and "predict" in tname and "422" not in tname and "missing" not in tname:
            item.add_marker(skip)
