import sys
from pathlib import Path

# Make backend importable from the tests directory
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
