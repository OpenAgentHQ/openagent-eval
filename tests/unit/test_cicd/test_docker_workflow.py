"""Regression tests for the Docker workflow's fork-safe write policy."""

from pathlib import Path

import yaml

WORKFLOW_PATH = Path(__file__).parents[3] / ".github" / "workflows" / "docker.yml"
MAIN_PUSH_GUARD = "github.event_name == 'push' && github.ref == 'refs/heads/main'"


def _load_workflow() -> dict:
    """Load the workflow without YAML 1.1 coercing GitHub's ``on`` key."""
    with WORKFLOW_PATH.open(encoding="utf-8") as workflow_file:
        return yaml.load(workflow_file, Loader=yaml.BaseLoader)


def _step(workflow: dict, name: str) -> dict:
    """Return a workflow step by its human-readable name."""
    return next(
        step
        for step in workflow["jobs"]["build-and-push"]["steps"]
        if step["name"] == name
    )


def test_ghcr_login_is_limited_to_main_push() -> None:
    """Fork pull requests must not log in to the organization GHCR."""
    login_step = _step(_load_workflow(), "Log in to GHCR")

    assert login_step.get("if") == f"${{{{ {MAIN_PUSH_GUARD} }}}}"


def test_image_push_is_limited_to_main_push() -> None:
    """Fork pull requests must build without pushing an image."""
    build_step = _step(_load_workflow(), "Build and push")

    assert build_step["with"]["push"] == f"${{{{ {MAIN_PUSH_GUARD} }}}}"


def test_registry_cache_export_is_limited_to_main_push() -> None:
    """Fork pull requests must use a non-registry cache export."""
    build_step = _step(_load_workflow(), "Build and push")
    cache_to = build_step["with"]["cache-to"]

    assert cache_to.startswith(f"${{{{ {MAIN_PUSH_GUARD} && ")
    assert "type=registry" in cache_to
    assert cache_to.endswith(" || 'type=gha,mode=max' }}")
