# RepoHeart: workflow runs green, agents never visibly activate

## TL;DR — primary root cause

**`OpenCodeProvider` (`OpenAgentHQ/repo-heart`, `repoheart/providers/opencode.py`)
hardcodes the wrong API host.** It defaults to:

```python
base_url: str = "https://api.opencode.ai/v1"
```

but the real, documented OpenCode Zen hosted API — the one `OPENCODE_API_KEY`
actually authenticates against, and the one every Zen model (including
`mimo-v2.5-free`, the model configured in this repo's `repoheart.yml`) is
served from — lives at:

```
https://opencode.ai/zen/v1/chat/completions
```

(confirmed against OpenCode's own docs at `opencode.ai/docs/zen` and
`opencode.ai/docs/providers`, and independently corroborated by Docker
Agent's OpenCode Zen integration docs and third-party OpenCode Zen guides —
all agree on `https://opencode.ai/zen/v1` as the base URL).

`api.opencode.ai` is not that host. Every single `OpenCodeProvider.complete()`
call — regardless of how correctly `OPENCODE_API_KEY` is configured — hits
the wrong domain and fails (connection/DNS error or a 404 HTML page, not a
JSON API response). Every agent wraps its provider call in
`except Exception: return AgentResult(findings=[Finding(summary="Provider
error ...")])` (see `issue_triage.py`, `code_quality.py`, `security.py`,
etc.) — so the failure is caught, turned into an internal `Finding` (which is
diagnostic-only, never posted to GitHub — see `agents/base.py`), and the
orchestrator logs a perfectly normal `agent_run ... status=ok`. The job
exits `0`. **This is why the workflow is green, `OPENCODE_API_KEY` is
correctly set, and yet every review comes back blank: not one LLM call this
repo's RepoHeart workflow has ever made against the `opencode` provider could
have succeeded.**

Confirmed directly from this repo's own RepoHeart workflow logs (run
[`32976363682`](https://github.com/OpenAgentHQ/openagent-eval/actions/runs/32976363682),
job `repoheart`, triggered by a real `issues.opened` event):

```
##[group]Run OpenAgentHQ/repo-heart@main
with:
  config: repoheart.yml
env:
  GITHUB_TOKEN: ***
  OPENCODE_API_KEY: ***          # <- present and non-empty
  ...
event_msg=routed agents=issue_triage,duplicate_detection,issue_resolution
event_msg=agent_run agent=issue_triage status=ok findings=1 actions=0
event_msg=agent_run agent=duplicate_detection status=ok findings=1 actions=0
event_msg=agent_run agent=issue_resolution status=ok findings=1 actions=0
event_msg=run_complete agents_run=issue_triage,duplicate_detection,issue_resolution actions_taken=0 actions_escalated=0 actions_denied=0 errors=0
```

`findings=1, actions=0` on every single agent, with **no**
`issue_comment_posted` / `issue_comment_denied` / `issue_comment_skipped` log
line anywhere in the run — even though every one of these agents
unconditionally attaches an `IssueComment` on its success path. The only way
to get `findings=1` with nothing downstream is the internal
`except Exception` branch: the provider call itself failed before ever
reaching the JSON-parsing / comment-building code. That is only possible if
`context.provider.complete()` raised — i.e. every OpenCode HTTP request in
this run failed, consistent with every request going to the wrong host.

## Execution trace

```
GitHub Event (issues.opened / pull_request.opened / ...)
 ↓  .github/workflows/repoheart.yml — on.* triggers ✅ correct
GitHub Actions Workflow
 ↓  uses: OpenAgentHQ/repo-heart@main → docker://ghcr.io/openagenthq/repo-heart:latest ✅ pulls fine
RepoHeart Container / Entrypoint (repoheart/main.py)
 ↓  GITHUB_EVENT_PATH / GITHUB_EVENT_NAME / GITHUB_TOKEN / OPENCODE_API_KEY all present ✅
Event Detection / Router (events/context.py, events/router.py)
 ↓  routing_key correctly maps to the right agent set ✅
Agent Selection / Registration (agents/registry.py)
 ↓  all agents registered and enabled per repoheart.yml ✅
Agent Initialization → Provider Initialization
 ↓  OpenCodeProvider(model="mimo-v2.5-free") constructed fine — no fail-fast
    check catches a wrong base_url; construction never makes a network call ✅
AI Model Call — OpenCodeProvider._do_complete()
 ✗  STOPS HERE: POST to https://api.opencode.ai/v1/chat/completions — a host
    that does not serve the OpenCode Zen API. The request fails (DNS/connect
    error or non-JSON 404 response). urllib raises; retried 3x by
    `_retry_with_backoff` where applicable, then propagates.
Agent Execution
 ✗  Each agent's `try: response = context.provider.complete(request) except
    Exception as exc: return AgentResult(findings=[Finding(...)])` swallows
    the failure. Orchestrator logs `agent_run status=ok findings=1
    actions=0` — indistinguishable from a real, clean, "nothing to report"
    run in the logs or in the job's exit code.
GitHub API Action
    never reached — there is nothing to post; no comment, no label, no
    review.
```

## Fix

Implemented and verified in a local clone of `OpenAgentHQ/repo-heart`
(`repoheart/providers/opencode.py`):

```python
base_url: str = "https://opencode.ai/zen/v1",   # was: "https://api.opencode.ai/v1"
```

Added two regression tests to `tests/test_providers_opencode.py`:

- `test_default_base_url_is_the_real_opencode_zen_endpoint` — asserts the
  provider's default `base_url` is the real Zen host.
- `test_request_url_hits_the_real_zen_chat_completions_path` — captures the
  actual URL `urllib.request.urlopen` is called with during `.complete()`
  and asserts it's `https://opencode.ai/zen/v1/chat/completions`.

Both tests were confirmed to **fail** against the pre-fix `base_url` (asserted
`https://api.opencode.ai/v1/chat/completions` — the wrong host — was what the
provider actually requested), and pass after the one-line fix.

```
$ pytest -q tests/test_providers_opencode.py
13 passed in 0.06s
$ ruff check repoheart/providers/opencode.py tests/test_providers_opencode.py
All checks passed!
$ mypy repoheart/providers/opencode.py
Success: no issues found in 1 source file
```

## Secondary finding — `code_quality`/`security` still degrade even with a working provider

Separately, once the provider itself is fixed, `code_quality` and `security`
remain unable to fully do their job specifically for **PR** agents, because
`ruff`, `mypy`, and `detect-secrets` are declared as `dev`-only extras in
`repo-heart`'s `pyproject.toml`, while its `Dockerfile` only runs
`pip install .` (base dependencies) — so the shipped image never has these
binaries on `PATH`. `Orchestrator._run_linters()` / `_scan_secrets()` catch
the resulting `FileNotFoundError` and return `""`, which trips
`CodeQualityAgent.run()`'s explicit early return:

```python
if not context.linter_output:
    return AgentResult(findings=[Finding(summary="No linter output available; tools may not be installed")])
```

(`repoheart/agents/code_quality.py:62-65`)

Fix (implemented and verified in the same local clone): moved `ruff`,
`mypy`, and added `detect-secrets` from `[project.optional-dependencies].dev`
into `[project.dependencies]` in `pyproject.toml`, and added
`tests/test_runtime_deps.py` (3 tests) asserting these tools are declared as
base dependencies and resolve on `PATH` once installed — fails pre-fix,
passes post-fix.

## This repo's own configuration — verified correct, not the cause

- `.github/workflows/repoheart.yml`: all relevant `on:` triggers present and
  correctly typed; `permissions` sufficient for every `ActionKind` the
  orchestrator dispatches; the `uses:` action reference was already
  corrected in commit `97c04d3`.
- `repoheart.yml`: correctly nested under the required top-level
  `repoheart:` key; `provider.name: opencode` / `model: mimo-v2.5-free` are
  valid and match a real, currently-served OpenCode Zen model; all agents
  enabled as intended.
- `OPENCODE_API_KEY` is genuinely present in the environment at run time
  (confirmed non-empty in the masked workflow logs above) — this was never a
  missing-secret problem.

## Note on scope

This session's write access is scoped to `OpenAgentHQ/openagent-eval`. Both
defects and their fixes live in `OpenAgentHQ/repo-heart`
(`repoheart/providers/opencode.py`, `pyproject.toml`, `Dockerfile`), which
was cloned read-only for investigation and reproduction
(`/home/user/openagenthq/repo-heart` locally). Both fixes described above
were implemented and verified in that clone but are not pushed anywhere by
this session; they should be applied as a PR against
`OpenAgentHQ/repo-heart` directly — the primary `base_url` fix in
particular is what will make `code_quality`, `security`, `pr_review`,
`issue_triage`, and every other `opencode`-backed agent actually produce
real output in this repo's own workflow. Nothing in this repo's
`repoheart.yml` or workflow needs to change.
