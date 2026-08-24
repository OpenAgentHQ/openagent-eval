"""Regression tests for the Docker workflow's fork-safe write policy."""

import re
from pathlib import Path

import yaml

WORKFLOW_PATH = Path(__file__).parents[3] / ".github" / "workflows" / "docker.yml"
MAIN_PUSH_GUARD = "github.event_name == 'push' && github.ref == 'refs/heads/main'"
BUILDX_ACTION = "docker/setup-buildx-action@v3"
BUILD_PUSH_ACTION = "docker/build-push-action@v5"
LOGIN_ACTION = "docker/login-action@v3"
EXPECTED_IMAGE_TAG = "ghcr.io/${{ steps.repo.outputs.name }}/openagent-eval:latest"
REGISTRY_CACHE_FROM = "type=registry,ref=ghcr.io/{0}/openagent-eval:cache"
REGISTRY_CACHE_TO = "type=registry,ref=ghcr.io/{0}/openagent-eval:cache,mode=max"
GHA_CACHE_FROM = "type=gha"
GHA_CACHE_TO = "type=gha,mode=max"


def _load_workflow() -> dict:
    """Load the workflow without YAML 1.1 coercing GitHub's ``on`` key."""
    with WORKFLOW_PATH.open(encoding="utf-8") as workflow_file:
        return yaml.load(workflow_file, Loader=yaml.BaseLoader)


def _workflow_jobs(workflow: dict) -> dict:
    """Return workflow jobs, rejecting a malformed top-level structure."""
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "workflow must define a jobs mapping"
    return jobs


def _build_job(workflow: dict) -> dict:
    """Return the required Docker build job with an explanatory assertion."""
    job = _workflow_jobs(workflow).get("build-and-push")
    assert isinstance(job, dict), "workflow must define the 'build-and-push' Docker job"
    return job


def _workflow_steps(workflow: dict) -> list[dict]:
    """Return every step, rejecting malformed workflow structure explicitly."""
    steps = []
    for job_name, job in _workflow_jobs(workflow).items():
        assert isinstance(job, dict), f"job {job_name!r} must be a mapping"
        job_steps = job.get("steps", [])
        assert isinstance(job_steps, list), (
            f"job {job_name!r} must define steps as a list"
        )
        for index, step in enumerate(job_steps):
            assert isinstance(step, dict), (
                f"job {job_name!r} step {index} must be a mapping"
            )
            steps.append(step)
    return steps


def _action_steps(workflow: dict, action: str) -> list[dict]:
    """Return every workflow step using one pinned action."""
    return [step for step in _workflow_steps(workflow) if step.get("uses") == action]


def _exactly_one_action(workflow: dict, action: str) -> dict:
    """Return one pinned action, with a clear assertion for missing/duplicates."""
    matches = _action_steps(workflow, action)
    assert len(matches) == 1, (
        f"expected exactly one {action!r} action, found {len(matches)}"
    )
    return matches[0]


def _named_step(workflow: dict, name: str) -> dict:
    """Return one named step, with an explanatory assertion on drift."""
    matches = [step for step in _workflow_steps(workflow) if step.get("name") == name]
    assert len(matches) == 1, (
        f"expected exactly one workflow step named {name!r}, found {len(matches)}"
    )
    return matches[0]


def _login_step(workflow: dict) -> dict:
    """Return the sole named GHCR login action."""
    step = _named_step(workflow, "Log in to GHCR")
    assert step.get("uses") == LOGIN_ACTION, (
        "the 'Log in to GHCR' step must use the pinned Docker login action"
    )
    action_matches = _action_steps(workflow, LOGIN_ACTION)
    assert len(action_matches) == 1, (
        f"expected exactly one {LOGIN_ACTION!r} action, found {len(action_matches)}"
    )
    assert action_matches[0] is step, (
        "the named GHCR login step must be the workflow's sole login action"
    )
    return step


def _buildx_step(workflow: dict) -> dict:
    """Return the sole Buildx setup action and pin its expected step name."""
    step = _exactly_one_action(workflow, BUILDX_ACTION)
    assert step.get("name") == "Set up Docker Buildx", (
        "the sole Buildx setup action must remain named 'Set up Docker Buildx'"
    )
    return step


def _build_step(workflow: dict) -> dict:
    """Return the sole named Docker build-push action."""
    step = _named_step(workflow, "Build and push")
    assert step.get("uses") == BUILD_PUSH_ACTION, (
        "the 'Build and push' step must use the pinned Docker build-push action"
    )
    action_matches = _action_steps(workflow, BUILD_PUSH_ACTION)
    assert len(action_matches) == 1, (
        f"expected exactly one {BUILD_PUSH_ACTION!r} action, "
        f"found {len(action_matches)}"
    )
    assert action_matches[0] is step, (
        "the named Docker build step must be the workflow's sole build-push action"
    )
    return step


def _build_inputs(build_step: dict) -> dict:
    """Return build inputs, rejecting a malformed action mapping explicitly."""
    inputs = build_step.get("with")
    assert isinstance(inputs, dict), (
        "the Docker build-push step must define with inputs"
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
    login_step = _login_step(_load_workflow())

    assert login_step.get("if") == f"${{{{ {MAIN_PUSH_GUARD} }}}}", (
        "GHCR login must run only for a push to refs/heads/main"
    )


def test_image_push_is_limited_to_main_push() -> None:
    """Fork pull requests must build without pushing an image."""
    build_step = _build_step(_load_workflow())
    inputs = _build_inputs(build_step)

    assert inputs.get("push") == f"${{{{ {MAIN_PUSH_GUARD} }}}}", (
        "image publication must be enabled only for a push to refs/heads/main"
    )
    assert "outputs" not in inputs, (
        "the Docker build action must not define an unguarded registry output"
    )
    tags = inputs.get("tags")
    assert isinstance(tags, str), "the Docker build action must define image tags"
    assert [line.strip() for line in tags.splitlines() if line.strip()] == [
        EXPECTED_IMAGE_TAG
    ], "the main-push image tag must be the sole expected GHCR tag"


def test_workflow_triggers_include_pull_request_and_main_push() -> None:
    """Docker CI must run for PRs and pushes to the main branch."""
    workflow = _load_workflow()
    triggers = workflow.get("on")

    assert isinstance(triggers, dict), (
        "workflow must define event triggers as a mapping"
    )
    pull_request = triggers.get("pull_request")
    assert isinstance(pull_request, dict), (
        "workflow must retain a pull_request mapping for the main branch"
    )
    assert pull_request == {"branches": ["main"]}, (
        "workflow must retain exactly pull_request branches: [main] without qualifiers"
    )
    push = triggers.get("push")
    assert isinstance(push, dict), "workflow must retain a push mapping for main"
    assert push == {"branches": ["main"]}, (
        "workflow must retain exactly push branches: [main]"
    )


def test_workflow_has_one_buildx_and_docker_build_action() -> None:
    """Docker CI must have exactly one setup and one build-push action."""
    workflow = _load_workflow()

    _buildx_step(workflow)
    _build_step(workflow)


def test_docker_build_step_remains_runnable_for_pull_requests() -> None:
    """The Docker build step must not skip pull-request events."""
    workflow = _load_workflow()
    build_job = _build_job(workflow)
    build_step = _build_step(workflow)

    assert build_job.get("if") is None, (
        "the containing Docker build job must remain unconditional so pull requests build"
    )
    assert build_step.get("if") is None, (
        "the Docker build-push step must remain unconditional so pull requests build"
    )


def test_buildx_setup_remains_runnable_for_pull_requests() -> None:
    """The configured Buildx setup must not skip pull-request events."""
    buildx_step = _buildx_step(_load_workflow())

    assert buildx_step.get("if") is None, (
        "the Buildx setup step must remain unconditional so pull requests build"
    )


def test_registry_cache_import_is_limited_to_main_push() -> None:
    """Fork pull requests must not import their cache from GHCR."""
    inputs = _build_inputs(_build_step(_load_workflow()))

    _assert_cache_expression(
        inputs.get("cache-from"),
        "cache-from",
        REGISTRY_CACHE_FROM,
        GHA_CACHE_FROM,
    )


def test_registry_cache_export_is_limited_to_main_push() -> None:
    """Fork pull requests must use a non-registry cache export."""
    inputs = _build_inputs(_build_step(_load_workflow()))

    _assert_cache_expression(
        inputs.get("cache-to"),
        "cache-to",
        REGISTRY_CACHE_TO,
        GHA_CACHE_TO,
    )
