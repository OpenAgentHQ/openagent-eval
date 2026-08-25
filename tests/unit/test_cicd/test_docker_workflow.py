"""Regression tests for the Docker workflow's fork-safe write policy."""

import re
from pathlib import Path

import yaml

WORKFLOW_PATH = Path(__file__).parents[3] / ".github" / "workflows" / "docker.yml"
MAIN_PUSH_GUARD = "github.event_name == 'push' && github.ref == 'refs/heads/main'"
MAIN_PUSH_EXPRESSION = f"${{{{ {MAIN_PUSH_GUARD} }}}}"
CHECKOUT_ACTION = "actions/checkout@v4"
BUILDX_ACTION = "docker/setup-buildx-action@v3"
BUILD_PUSH_ACTION = "docker/build-push-action@v5"
LOGIN_ACTION = "docker/login-action@v3"
EXPECTED_IMAGE_TAG = "ghcr.io/${{ steps.repo.outputs.name }}/openagent-eval:latest"
REGISTRY_CACHE_FROM = "type=registry,ref=ghcr.io/{0}/openagent-eval:cache"
REGISTRY_CACHE_TO = "type=registry,ref=ghcr.io/{0}/openagent-eval:cache,mode=max"
GHA_CACHE_FROM = "type=gha"
GHA_CACHE_TO = "type=gha,mode=max"
EXPECTED_BUILD_JOB_KEYS = {"runs-on", "permissions", "steps"}
EXPECTED_PERMISSIONS = {"contents": "read", "packages": "write"}
EXPECTED_BUILD_INPUT_KEYS = {"context", "push", "tags", "cache-from", "cache-to"}

EXPECTED_STEP_SCHEMA = (
    ("Checkout repository", {"uses": CHECKOUT_ACTION}, {"name", "uses"}),
    ("Set up Docker Buildx", {"uses": BUILDX_ACTION}, {"name", "uses"}),
    (
        "Log in to GHCR",
        {"uses": LOGIN_ACTION},
        {"name", "if", "uses", "with"},
    ),
    (
        "Lowercase repository owner",
        {
            "id": "repo",
            "run": 'echo "name=${GITHUB_REPOSITORY_OWNER@L}" >> "$GITHUB_OUTPUT"',
        },
        {"name", "id", "run"},
    ),
    ("Build and push", {"uses": BUILD_PUSH_ACTION}, {"name", "uses", "with"}),
)


def _load_workflow() -> dict:
    """Load the workflow without YAML 1.1 coercing GitHub's ``on`` key."""
    with WORKFLOW_PATH.open(encoding="utf-8") as workflow_file:
        return yaml.load(workflow_file, Loader=yaml.BaseLoader)


def _workflow_schema() -> tuple[dict, dict, dict[str, dict]]:
    """Validate the sole build job and return its semantic five-step schema."""
    workflow = _load_workflow()
    assert isinstance(workflow, dict), "workflow must be a mapping"

    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "workflow must define a jobs mapping"
    assert list(jobs) == ["build-and-push"], (
        "workflow must define only the 'build-and-push' Docker job"
    )
    build_job = jobs.get("build-and-push")
    assert isinstance(build_job, dict), (
        "workflow must define the 'build-and-push' Docker job as a mapping"
    )
    assert set(build_job) == EXPECTED_BUILD_JOB_KEYS, (
        "the Docker build job must have only runs-on, permissions, and steps"
    )
    assert build_job.get("if") is None, (
        "the Docker build job must not define a job-level if condition"
    )
    assert build_job.get("runs-on") == "ubuntu-latest", (
        "the Docker build job must run on ubuntu-latest"
    )
    permissions = build_job.get("permissions")
    assert isinstance(permissions, dict), (
        "the Docker build job permissions must be a mapping"
    )
    assert permissions == EXPECTED_PERMISSIONS, (
        "the Docker build job must grant exactly contents: read and packages: write"
    )

    steps = build_job.get("steps")
    assert isinstance(steps, list), "the Docker build job must define steps as a list"
    assert len(steps) == len(EXPECTED_STEP_SCHEMA), (
        "the Docker build job must retain its exact five-step inventory"
    )

    steps_by_name = {}
    for index, (expected_name, expected_fields, expected_keys) in enumerate(
        EXPECTED_STEP_SCHEMA
    ):
        step = steps[index]
        assert isinstance(step, dict), (
            f"workflow step {index} must be a mapping for {expected_name!r}"
        )
        assert step.get("name") == expected_name, (
            f"workflow step {index} must remain {expected_name!r}"
        )
        assert set(step) == expected_keys, (
            f"workflow step {expected_name!r} must have exactly keys {expected_keys}"
        )
        for field, expected_value in expected_fields.items():
            assert step.get(field) == expected_value, (
                f"workflow step {expected_name!r} must keep {field}={expected_value!r}"
            )
        steps_by_name[expected_name] = step

    return workflow, build_job, steps_by_name


def _build_inputs(build_step: dict) -> dict:
    """Return build inputs, rejecting a malformed action mapping explicitly."""
    inputs = build_step.get("with")
    assert isinstance(inputs, dict), (
        "the Docker build-push step must define with inputs"
    )
    assert set(inputs) == EXPECTED_BUILD_INPUT_KEYS, (
        "the Docker build-push step must define only context, push, tags, cache-from, and cache-to"
    )
    return inputs


def _parse_cache_expression(expression: object, input_name: str) -> tuple[str, str]:
    """Parse and validate the workflow's guarded registry/GHA cache expression."""
    assert isinstance(expression, str), (
        f"{input_name} must be a guarded registry/GHA expression string"
    )
    normalized = " ".join(expression.split())
    match = re.fullmatch(
        r"\$\{\{ (?P<guard>.+?) && format\('(?P<registry>[^']+)', "
        r"steps\.repo\.outputs\.name\) \|\| '(?P<gha>[^']+)' \}\}",
        normalized,
    )
    assert match is not None, (
        f"{input_name} must use guarded format(registry) with a GHA fallback; "
        f"got {expression!r}"
    )
    assert match.group("guard") == MAIN_PUSH_GUARD, (
        f"{input_name} must use the exact main-push guard; got {match.group('guard')!r}"
    )
    return match.group("registry"), match.group("gha")


def _assert_cache_expression(
    expression: object,
    input_name: str,
    expected_registry: str,
    expected_gha: str,
) -> tuple[str, str]:
    """Assert one cache input's exact semantic branches and return both values."""
    registry, gha = _parse_cache_expression(expression, input_name)
    assert registry == expected_registry, (
        f"{input_name} must preserve the expected registry cache reference"
    )
    assert gha == expected_gha, (
        f"{input_name} must use the expected non-registry GHA fallback"
    )
    return registry, gha


def test_ghcr_login_is_limited_to_main_push() -> None:
    """Fork pull requests must not log in to the organization GHCR."""
    _, _, steps = _workflow_schema()
    login_step = steps["Log in to GHCR"]

    assert login_step.get("if") == MAIN_PUSH_EXPRESSION, (
        "GHCR login must run only for a push to refs/heads/main"
    )
    assert login_step.get("with") == {
        "registry": "ghcr.io",
        "username": "${{ github.actor }}",
        "password": "${{ secrets.GITHUB_TOKEN }}",
    }, "GHCR login must use the exact GitHub Container Registry credentials"


def test_image_push_is_limited_to_main_push() -> None:
    """Fork pull requests must build without pushing an image."""
    _, _, steps = _workflow_schema()
    inputs = _build_inputs(steps["Build and push"])

    assert inputs.get("push") == MAIN_PUSH_EXPRESSION, (
        "image publication must be enabled only for a push to refs/heads/main"
    )
    assert "outputs" not in inputs, (
        "the Docker build action must not define an unguarded registry output"
    )
    assert inputs.get("context") == ".", (
        "the Docker build action must build the checked-out repository context"
    )
    tags = inputs.get("tags")
    assert isinstance(tags, str), "the Docker build action must define image tags"
    assert [line.strip() for line in tags.splitlines() if line.strip()] == [
        EXPECTED_IMAGE_TAG
    ], "the main-push image tag must be the sole expected GHCR tag"


def test_workflow_triggers_include_pull_request_and_main_push() -> None:
    """Docker CI must run for PRs and pushes to the main branch."""
    workflow, _, _ = _workflow_schema()
    triggers = workflow.get("on")

    assert isinstance(triggers, dict), (
        "workflow must define event triggers as a mapping"
    )
    assert triggers.get("pull_request") == {"branches": ["main"]}, (
        "workflow must retain exactly pull_request branches: [main] without qualifiers"
    )
    assert triggers.get("push") == {"branches": ["main"]}, (
        "workflow must retain exactly push branches: [main]"
    )


def test_workflow_has_one_buildx_and_docker_build_action() -> None:
    """Docker CI must have exactly one setup and one build-push action."""
    _, _, steps = _workflow_schema()

    assert steps["Set up Docker Buildx"]["uses"] == BUILDX_ACTION
    assert steps["Build and push"]["uses"] == BUILD_PUSH_ACTION


def test_docker_build_step_remains_runnable_for_pull_requests() -> None:
    """The Docker build job and step must not skip pull-request events."""
    _, build_job, steps = _workflow_schema()

    assert build_job.get("if") is None, (
        "the containing Docker build job must remain unconditional so pull requests build"
    )
    assert steps["Build and push"].get("if") is None, (
        "the Docker build-push step must remain unconditional so pull requests build"
    )


def test_buildx_setup_remains_runnable_for_pull_requests() -> None:
    """The configured Buildx setup must not skip pull-request events."""
    _, _, steps = _workflow_schema()

    assert steps["Set up Docker Buildx"].get("if") is None, (
        "the Buildx setup step must remain unconditional so pull requests build"
    )


def test_registry_cache_import_is_limited_to_main_push() -> None:
    """Fork pull requests must not import their cache from GHCR."""
    _, _, steps = _workflow_schema()
    inputs = _build_inputs(steps["Build and push"])

    _assert_cache_expression(
        inputs.get("cache-from"),
        "cache-from",
        REGISTRY_CACHE_FROM,
        GHA_CACHE_FROM,
    )


def test_registry_cache_export_is_limited_to_main_push() -> None:
    """Fork pull requests must use a non-registry cache export."""
    _, _, steps = _workflow_schema()
    inputs = _build_inputs(steps["Build and push"])

    _assert_cache_expression(
        inputs.get("cache-to"),
        "cache-to",
        REGISTRY_CACHE_TO,
        GHA_CACHE_TO,
    )
