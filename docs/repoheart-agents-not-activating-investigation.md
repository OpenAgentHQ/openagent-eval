# RepoHeart: workflow runs green, agents never visibly activate

## TL;DR

The `.github/workflows/repoheart.yml` workflow and `repoheart.yml` config in
this repo are correct — routing, agent registration, provider wiring, event
parsing, and permissions all check out. The reason nothing visible happens is
upstream, in the `OpenAgentHQ/repo-heart` action image itself:

**`ruff`, `mypy`, and `detect-secrets` are declared as `dev`-only extras in
`repo-heart`'s `pyproject.toml`, but the Dockerfile only runs `pip install .`
(base dependencies). So the shipped `ghcr.io/openagenthq/repo-heart:latest`
image never has these binaries on `PATH`.**

`Orchestrator._run_linters()` / `_scan_secrets()` shell out to them via
`subprocess.run(...)`, catch `FileNotFoundError`, and silently return `""`
(`repoheart/orchestrator/orchestrator.py`, `_run_linters`/`_scan_secrets`).
That empty output then hits an explicit early-return in `CodeQualityAgent.run()`:

```python
if not context.linter_output:
    return AgentResult(
        findings=[Finding(summary="No linter output available; tools may not be installed")]
    )
```

(`repoheart/agents/code_quality.py:62-65`)

So on **every single PR**, `code_quality` degrades to a no-op `Finding` (never
posted as a comment), and `security`'s secret-scan context is always empty
too. The orchestrator counts this as a normal, successful agent run
(`agent_run ... status=ok`), so `main()` returns `0` and the Action step goes
green — even though nothing was actually reviewed. This exactly matches the
reported symptom: the job completes successfully with no evidence any agent
did real work.

## Execution trace

```
GitHub Event (pull_request.opened)
 ↓  .github/workflows/repoheart.yml — on.pull_request.types ✅ correct
GitHub Actions Workflow
 ↓  uses: OpenAgentHQ/repo-heart@main → docker://ghcr.io/openagenthq/repo-heart:latest ✅ pulls fine
RepoHeart Container
 ↓  ENTRYPOINT ["python", "-m", "repoheart.main"] ✅ starts
Application Entrypoint (repoheart/main.py:main)
 ↓  GITHUB_EVENT_PATH / GITHUB_EVENT_NAME read correctly ✅
Event Detection / Router (events/context.py, events/router.py)
 ↓  routing_key "pull_request.opened" → [pr_review, code_quality, security, test, conflict_resolution] ✅
Agent Selection / Registration (agents/registry.py — AGENT_REGISTRY)
 ↓  all 5 classes registered and enabled per repoheart.yml ✅
Agent Initialization (Orchestrator._build_context)
 ↓  provider constructed via providers/registry.py ✅ (fails fast only on missing SDK, not on missing linters)
Provider Initialization
 ↓  OpenCodeProvider(...) instantiated fine ✅
Agent Execution — CodeQualityAgent.run()
 ✗  STOPS HERE: context.linter_output == "" (ruff/mypy not on PATH in the
    image) → early return, "skipping code quality check", no LLM call made,
    no comment posted. Reported as agent_run status=ok — indistinguishable
    from a real, clean run in the logs.
GitHub API Action
    never reached for code_quality; security's diff review still runs but
    without secret-scan context.
```

## Evidence

- `OpenAgentHQ/repo-heart` — `pyproject.toml` (before fix):
  ```toml
  dependencies = [
      "pyyaml>=6.0",
  ]
  [project.optional-dependencies]
  dev = [
      "pytest>=8.0",
      "ruff>=0.6",
      "mypy>=1.11",
      "types-PyYAML>=6.0",
  ]
  ```
- `OpenAgentHQ/repo-heart` — `Dockerfile`:
  ```dockerfile
  COPY pyproject.toml README.md ./
  COPY repoheart ./repoheart
  RUN pip install --no-cache-dir .
  ```
  `pip install .` only pulls `[project.dependencies]` — the `dev` extra
  (and therefore `ruff`/`mypy`) is never installed in the image.
- `OpenAgentHQ/repo-heart` — `repoheart/orchestrator/orchestrator.py`,
  `_run_linters()` (ruff/mypy) and `_scan_secrets()` (detect-secrets): both
  wrap `subprocess.run([...])` in `except (FileNotFoundError, ...): pass` /
  `return ""` — correct behavior for "tool not installed", but nothing
  upstream distinguishes "genuinely nothing to report" from "the binary
  doesn't exist," so it never surfaces as an error.
- `OpenAgentHQ/repo-heart` — `repoheart/agents/code_quality.py:62-65`: hard
  early-return whenever `context.linter_output` is empty, which is
  unconditionally the case in the shipped image.
- `tests/agents/test_code_quality.py` in `repo-heart` injects
  `linter_output` directly in every test — nothing in the existing suite
  exercises `_run_linters()` actually finding `ruff`/`mypy` on `PATH`, so this
  gap was untested.

Reproduced locally: cloned `OpenAgentHQ/repo-heart` at the pinned `main` ref,
installed the package the same way the Dockerfile does (`pip install .`,
base deps only), and ran the real pipeline against a synthetic
`pull_request.opened` event pointed at two real commits in this repo:

```
event_msg=routed agents=pr_review,code_quality,security,test,conflict_resolution
event_msg=agent_run agent=code_quality status=ok findings=1 actions=0
```
— `findings[0].summary == "No linter output available; tools may not be installed"`,
confirming the silent no-op, while the step/job itself reports success.

## This repo's own configuration — verified correct, not the cause

- `.github/workflows/repoheart.yml`: `on.issues/issue_comment/pull_request/
  pull_request_review/push/workflow_run/release` all present and correctly
  typed; `permissions` (`contents: write`, `issues: write`,
  `pull-requests: write`, `checks: read`, `actions: read`) are sufficient for
  every `ActionKind` the orchestrator dispatches; the `uses:` action reference
  (`OpenAgentHQ/repo-heart@main`) was already corrected in commit `97c04d3`.
- `repoheart.yml`: correctly nested under the required top-level
  `repoheart:` key, `provider.name: opencode` is a valid provider, and all
  agents including `code_quality` are enabled.
- `GITHUB_EVENT_NAME` / `GITHUB_EVENT_PATH` / `GITHUB_TOKEN` are supplied to
  the container as expected for a Docker container action; routing, agent
  registry, and provider resolution all behaved correctly in the local
  reproduction above.

## Fix

Applied upstream, in `OpenAgentHQ/repo-heart` (verified locally against a
clone of that repo; not part of this repo's diff since the affected code
lives there):

- `pyproject.toml`: moved `ruff`, `mypy`, and added `detect-secrets` to
  `[project.dependencies]` (base install), leaving only `pytest` and
  `types-PyYAML` under the `dev` extra. `pip install .` (what the Dockerfile
  runs) now installs everything `_run_linters`/`_scan_secrets` need.
- Added `tests/test_runtime_deps.py`:
  - asserts `ruff`/`mypy`/`detect-secrets` are listed in
    `[project.dependencies]`, not only `dev` — this test fails against the
    pre-fix `pyproject.toml`.
  - asserts the three binaries actually resolve on `PATH` once installed.
  - a smoke test that `ruff check` on a deliberately bad snippet produces a
    real finding (`F401`), guarding against a future "installed but broken"
    regression.

## Verification (in the `repo-heart` clone)

```
$ pip install -e .            # base deps only, mirrors Dockerfile's `pip install .`
$ pytest -q tests/test_runtime_deps.py
...                                                                      [100%]
3 passed in 0.02s

$ pytest -q                    # full existing suite
... 4 pre-existing failures in tests/test_retrieval_lexical.py, unrelated to
    this change (ripgrep-fallback tests failing in this sandbox regardless
    of the pyproject/runtime-deps fix — reproduced identically before and
    after the change)

$ ruff check pyproject.toml
All checks passed!

$ mypy repoheart/agents/code_quality.py
Success: no issues found in 1 source file
```

Re-running the same synthetic `pull_request.opened` reproduction after
installing the fixed dependency set: `ruff`/`mypy` resolve on `PATH`,
`_run_linters()` returns real output, and `code_quality` proceeds past the
early-return into the actual LLM-backed review path instead of the
"no linter output" `Finding`.

## Note on scope

This session's write access is scoped to `OpenAgentHQ/openagent-eval`. The
defect and its fix live in `OpenAgentHQ/repo-heart`'s `pyproject.toml` /
`Dockerfile` / test suite, which was cloned read-only for investigation and
reproduction (`/home/user/openagenthq/repo-heart` locally). The fix described
above was implemented and verified in that clone but is not pushed anywhere
by this session; it should be applied as a PR against `OpenAgentHQ/repo-heart`
directly. Nothing in this repo's `repoheart.yml` or workflow needed to
change.
