import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

_MODEL_DIR = Path(__file__).resolve().parents[1] / "backend" / "model"


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
