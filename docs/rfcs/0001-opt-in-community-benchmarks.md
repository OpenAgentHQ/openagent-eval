# RFC 0001: Opt-in community benchmark submissions

- **Status:** Draft
- **Authors:** OpenAgent Eval contributors
- **Created:** 2026-11-13
- **Discussion:** OpenAgent Eval issue proposing community benchmark submissions
- **Decision:** Pending maintainer and community review

## Summary

This RFC proposes an optional way for users to submit a small, anonymized summary of an evaluation run to a public community benchmark project. The feature must be explicitly invoked for each submission. OpenAgent Eval remains local-first: installing, configuring, running, or upgrading the tool never sends benchmark data automatically.

This document requests feedback on whether to build the feature and on the policy and operational questions listed below. It does not authorize or describe an implementation in this repository.

## Motivation

Users may want to compare the quality of their RAG evaluation with results from other configurations. A shared benchmark could help users understand relative performance and encourage sharing useful, reproducible evaluation setups. That benefit is only acceptable if users control every submission and the project avoids collecting prompts, answers, corpora, credentials, or other raw evaluation data.

## Goals

- Preserve local-first behavior and make network submission opt-in at the point of use.
- Submit only an explicitly defined aggregate summary, with no raw evaluation examples.
- Keep benchmark storage and presentation separate from the OpenAgent Eval source repository.
- Explain exactly what will be sent and where before the user confirms submission.
- Let users inspect a submission locally before sending it.
- Make failures non-blocking: a benchmark service outage must not affect evaluation results.

## Non-goals

- Telemetry, analytics, usage tracking, or background reporting.
- Uploading datasets, prompts, generated answers, retrieved context, traces, logs, or reports.
- Collecting provider credentials, account identifiers, machine identifiers, or IP addresses as benchmark fields.
- Automatically publishing benchmark results during normal evaluation runs.
- Creating a hosted dashboard or user accounts as part of this proposal.
- Treating a community benchmark as a universal ranking of model or RAG quality.

## Proposed data contract

The submission should be a versioned JSON document containing only allowlisted aggregate fields. The first version should consider:

- Schema version and OpenAgent Eval version.
- User-selected benchmark category and a short, allowlisted task/domain label (for example, `general_qa`), not a free-form dataset name.
- Aggregate metric names and values already produced by the run, such as mean faithfulness or context precision, plus sample count.
- Coarse configuration descriptors only where needed to make comparisons meaningful (for example, chunk size bucket or retrieval strategy from a fixed vocabulary).

The exact field list must be finalized before implementation. Default-deny rules apply: arbitrary configuration values and user-provided strings are excluded unless a reviewed schema explicitly allows them. In particular, submissions must never include prompts, answers, retrieved passages, corpus contents or identifiers, raw per-example results, local file paths, environment variables, API keys, provider request/response bodies, or free-form run names.

Aggregate metrics can still reveal information, especially for small or sensitive datasets. The implementation should require a minimum sample count (proposed initial threshold: 10 evaluated examples) and should reject a submission if the run cannot meet it. Reviewers should decide whether further protections, such as rounding metric values or suppressing rare categories, are needed.

“Anonymized” must not be presented as a guarantee of anonymity. A public endpoint may observe network metadata such as an IP address even if the payload contains no identifier. The submission flow must explain this limitation, and the benchmark service should avoid retaining request metadata beyond what is operationally necessary.

## Opt-in and user experience

- No setting is enabled by default. No background upload or automatic submission is permitted.
- Submission requires an explicit command or action (proposed CLI shape: `oaeval benchmark submit <run-id>`), separate from `oaeval run`.
- Before network access, show the destination, the exact payload or a readable equivalent, and the fact that it will be public. Require a positive confirmation for that submission.
- Provide a non-interactive confirmation flag only for automation (for example, `--yes`); the flag must be explicit and documented. It must not be stored as a global or project default.
- Offer a local preview/export command so users can inspect the candidate payload without sending it.
- Do not save a lasting consent preference. Consent applies to one submission at a time.
- Submission errors should report that the local evaluation completed and allow retrying submission separately.

## Destination and separation

Submissions should land in a separate `openagent-eval-benchmarks` repository or service, not in the OpenAgent Eval code repository. The destination should accept only the versioned schema, validate and sanitize input, and publish entries through a documented contribution process. Whether this is a Git-based contribution flow or a small hosted ingestion service is an open design decision; either choice needs abuse prevention and an accountable maintainer group.

The client should use a stable, documented endpoint configured in a way that can be reviewed. Redirects to unapproved hosts should not be followed automatically. The benchmark destination must not require users to provide provider credentials or create an OpenAgent Eval account.

## Results shown to users

Results should be presented as descriptive community distributions, not as a single universal score or leaderboard ranking. A later implementation could show percentile bands or metric distributions for comparable task categories and configuration buckets. Comparisons must disclose sample sizes, schema/version differences, and the fact that submitted runs may not be comparable due to different datasets, providers, or evaluation conditions.

The feature should not transmit local run details just to display community results. If fetching benchmark summaries is added, it should be a separate read-only request, disclose the remote source, and remain optional. This RFC does not require a live results service; an initial approved implementation could instead link to published benchmark reports.

## Privacy, security, and operations

- Publish the schema and payload examples before launch.
- Validate and bound payload size and field values on both client and destination.
- Keep the client allowlist strict and avoid serializing arbitrary run/config objects.
- Use HTTPS and document the destination's maintainers, retention policy, moderation process, and takedown contact.
- Define how accidental sensitive submissions can be removed from the benchmark repository and its history or backups.
- Make clear that once public data is copied or cached, complete removal may not be possible.
- Never include secrets in error messages or request diagnostics.
- Provide an offline mode or allow users to disable the submission command if their environment forbids outbound requests.

## Alternatives considered

1. **No submission feature:** Safest and simplest; users can compare runs locally. This remains a valid outcome if privacy and operations costs outweigh the benefit.
2. **Automatic or default-on reporting:** Rejected. It conflicts with local-first expectations and makes consent unclear.
3. **Upload full reports to this repository:** Rejected. Reports may contain raw examples and would couple benchmark data to the source repository.
4. **Separate opt-in aggregate submissions:** Proposed for discussion because it provides a bounded path to community comparison while keeping normal evaluation local.

## Rollout and compatibility

If accepted, implementation should be delivered behind an explicit command and reviewed schema. No existing config should gain an enabled-by-default network behavior. The feature should remain optional when benchmark dependencies or network access are unavailable. Any schema change that expands submitted data requires a new review and a schema version change.

## Open questions for discussion

1. Is the community benefit sufficient to justify operating a public benchmark destination?
2. Which aggregate metrics and coarse configuration fields are useful without making runs identifiable?
3. Is 10 examples an appropriate minimum, or should the threshold be higher or configurable?
4. Should metric values be rounded or categories suppressed to reduce inference risk?
5. Should the destination be a Git repository with reviewed pull requests, or a hosted service with a public export?
6. Who will operate, moderate, and respond to removal requests for the separate benchmark project?
7. Should results be shown only in published reports initially, or is a read-only CLI comparison worth the added service?
8. What retention policy should apply to payloads and operational request metadata?

## Decision process

Maintainers should record one of the following in this document after discussion:

- **Accepted:** approve the policy and create a separate implementation issue with the final schema, destination, and operational owner.
- **Rejected:** document the reason and close the proposal without implementing submission behavior.
- **Revised:** update this RFC and continue discussion before creating implementation work.

Until a decision is recorded, the feature remains a proposal and no telemetry or submission code should be added.
