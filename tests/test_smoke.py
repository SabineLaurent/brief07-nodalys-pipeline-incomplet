"""Tests fumigènes minimes. À étoffer."""

from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent


def test_pyproject_present():
    assert (REPO_ROOT / "pyproject.toml").exists()


def test_alembic_config_present():
    assert (REPO_ROOT / "alembic.ini").exists()
