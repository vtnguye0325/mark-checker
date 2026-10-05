"""The dependency direction is api -> services -> rag -> core.

A lower layer that imports an upper layer creates the import cycle this
package was restructured to remove. Fail the build when that happens.
"""

import ast
from pathlib import Path

_PACKAGE = Path(__file__).resolve().parents[2] / "backend" / "mark_checker"

# layer -> the layers it must never import
_FORBIDDEN = {
    "core": ("api", "services", "rag"),
    "rag": ("api", "services"),
    "services": ("api",),
}


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
    return names


def test_layers_only_import_downwards():
    violations = []
    for layer, forbidden in _FORBIDDEN.items():
        for path in sorted((_PACKAGE / layer).rglob("*.py")):
            for module in _imported_modules(path):
                for upper in forbidden:
                    if module == f"mark_checker.{upper}" or module.startswith(
                        f"mark_checker.{upper}."
                    ):
                        rel = path.relative_to(_PACKAGE.parent)
                        violations.append(f"{rel} imports {module}")
    assert not violations, "The dependency direction is broken:\n" + "\n".join(violations)
