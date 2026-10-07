"""
Invariant CI : le Core et le Runtime ne doivent JAMAIS importer un provider
concret. Ce test fait échouer le build si quelqu'un ajoute `import evidently`
(ou mlflow, psycopg2, github, prefect, requests) dans agentic/core/ ou
agentic/runtime/.
"""

import ast
from pathlib import Path

FORBIDDEN_MODULES = {
    "evidently",
    "mlflow",
    "psycopg2",
    "prefect",
    "github",
    "PyGithub",
    "requests",
}

PROTECTED_DIRS = [
    Path(__file__).parent.parent / "agentic" / "core",
    Path(__file__).parent.parent / "agentic" / "runtime",
]


def _imported_modules(py_file: Path) -> set[str]:
    tree = ast.parse(py_file.read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module.split(".")[0])
    return modules


def test_core_never_imports_concrete_providers():
    violations = []
    for directory in PROTECTED_DIRS:
        for py_file in directory.rglob("*.py"):
            found = _imported_modules(py_file) & FORBIDDEN_MODULES
            if found:
                violations.append(f"{py_file.name}: {found}")
    assert not violations, (
        "Violation architecturale — Core/Runtime importe un provider concret :\n"
        + "\n".join(violations)
    )


def test_agents_never_import_action_tools():
    """
    Empêche les agents (runtime/specialist) d'importer directement
    les outils d'action (ex: github) pour court-circuiter le PolicyEngine.
    """
    runtime_dir = Path(__file__).parent.parent / "agentic" / "runtime"
    violations = []

    for py_file in runtime_dir.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "github" in alias.name:
                        violations.append(f"{py_file.name}: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module and (
                    "github" in node.module or "tools.github" in node.module
                ):
                    violations.append(f"{py_file.name}: {node.module}")

    assert not violations, (
        "Violation de Sécurité — Un agent tente d'importer un outil d'action (GitHub) :\n"
        + "\n".join(violations)
    )


def test_prefect_never_leaks_into_core_or_runtime():
    """
    Invariant CI : Prefect est exclusivement autorisé dans agentic/entrypoints/.
    Aucun @task ou @flow ne doit apparaître dans agentic/core/ ou agentic/runtime/.
    """
    violations = []
    for directory in PROTECTED_DIRS:
        for py_file in directory.rglob("*.py"):
            mods = _imported_modules(py_file)
            if "prefect" in mods:
                violations.append(f"{py_file.name}: importe 'prefect'")

    assert not violations, (
        "Violation architecturale — Prefect a fuité hors de agentic/entrypoints/ :\n"
        + "\n".join(violations)
    )
