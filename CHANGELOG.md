# Changelog

All notable changes to OpenAgent Eval will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [Unreleased]
### Added
- Added `oaeval doctor` warnings for configured providers whose optional extras are not installed.
- Created `scripts/changelog_validator.py` to automatically verify Keep a Changelog formatting.
- Added a section to `CONTRIBUTING.md` documenting the changelog update process for future contributors.
- Added `EvalPortReport` (`openagent_eval/reports/evalport.py`), a `ReportGenerator` that exports an `EvaluationReport` as an [EvalPort](https://github.com/adhabnr-ux/evalport) `ResultSet` for interop with other EvalPort-speaking evaluation tools; install with the new optional `evalport` extra (design agreed in Discussion #296).

### Fixed
- **EvalPortReport double-counting failed items** — `evaluation_report_to_result_set` no longer builds a second failed `Result` from `PipelineResult.errors` on top of the zeroed `EvaluationResult` already present in `PipelineResult.results`, which was silently corrupting `summary.total`/`summary.pass_rate` for any run with failures. Failed items are now sourced from `results` alone (via `metadata["failed"]`), which also sidesteps an ordering hazard: `errors` is appended to from inside each item's own coroutine and reflects completion order under the parallel executor, not dataset order, so it was never safe to zip against `results` by index. `Pipeline._evaluate_item`'s failure path also now preserves the source item's `metadata` (matching the success path) and records `error_type`, so a failed item's `test_case_id`/custom metadata survive the same way a successful item's do. (review feedback from @himanshu231204 on PR #369)

---

## [0.4.10] - 2026-08-24

### Fixed

- **Report Version Metadata** — use package version in report metadata instead of hardcoded value (#292)
- **CLI Test Command** — add missing `EvaluationResult` import in CI/CD test command
- **Exception Chaining** — add proper `raise ... from` in exception handlers across codebase
- **pgvector Availability Check** — use `importlib.util.find_spec` for psycopg availability check

### Changed

- **Opencode Model** — update opencode model to MiMo V2.5 Free (#293)
- **Opencode Model ID** — correct MiMo model ID format in opencode workflow (#294)

### Testing

- **Audit Path Test** — fix path assertion in audit error message test for Windows path wrapping
- **CLI Help Test** — fix encoding issue in pytest-import regression test on Windows

---

