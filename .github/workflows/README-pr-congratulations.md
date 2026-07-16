# PR Congratulations Workflow

Automatically posts a congratulatory comment on merged Pull Requests in OpenAgentHQ.

## Overview

When a Pull Request is merged into `main`, this workflow:

1. Posts a congratulations comment on the PR
2. Detects if it's the contributor's first merged PR
3. Checks for special labels (`first contribution`, `good first issue`)
4. Skips bot authors automatically
5. Logs all actions for audit purposes

## Trigger

| Property | Value |
|----------|-------|
| **Event** | `pull_request_target` |
| **Type** | `closed` |
| **Condition** | PR is merged AND target branch is `main` |

The workflow uses `pull_request_target` (not `pull_request`) for security reasons — it runs in the context of the base repository, which is safe for fork contributions.

### Why `pull_request_target`?

- Runs with access to repository secrets
- Safe for PRs from forks (no secret exposure)
- Executes in the base branch context, not the PR branch
- Required for `github.rest.search.issuesAndPullRequests` to work correctly

## Permissions

```yaml
permissions:
  pull-requests: write  # Post comments on PRs
  contents: read        # Read repository metadata
```

**Least privilege**: The workflow only requests the minimum permissions needed. It cannot modify code, merge PRs, or access sensitive data.

## How First Contribution Detection Works

The workflow uses the GitHub Search API to count merged PRs by the author:

```javascript
const { data: mergedPRs } = await github.rest.search.issuesAndPullRequests({
  q: `is:pr is:merged author:${author} base:main repo:${owner}/${repo}`,
  per_page: 1,
});
isFirstContribution = mergedPRs.total_count <= 1;
```

**Logic:**
- Query all merged PRs by the author targeting `main`
- If the count is 0 or 1, this is their first contribution
- The current PR may not appear in search results immediately (indexing delay), so 0 also counts as first

**Fallback:** If the API call fails, `isFirstContribution` defaults to `false` — the workflow never breaks on API errors.

## Comment Messages

### Default (All Contributors)

```
🎉 Congratulations @username!

Your pull request has been successfully merged into **main**. 🚀

Thank you for contributing to OpenAgentHQ and helping improve the project.

We truly appreciate your contribution and hope to see you back with more amazing PRs!

Happy Open Sourcing! ❤️
```

### First Contribution (Auto-detected)

Appends:

```
🌟 This is your first merged contribution to this repository.
Welcome to the OpenAgentHQ contributors family!
```

### Special Labels

If the PR has either label:
- `first contribution`
- `good first issue`

Appends:

```
🎊 Great first contribution!
```

## Customization

### Change the Target Branch

Edit the `if` condition in the job:

```yaml
if: >
  github.event.pull_request.merged == true &&
  github.event.pull_request.base.ref == 'main'  # Change to 'develop', 'release', etc.
```

### Add More Labels

Edit the label checks in the workflow:

```javascript
const hasMyCustomLabel = labels.some(
  l => l.toLowerCase() === 'my-custom-label'
);
```

### Modify the Message

Edit the `comment` string in the "Detect first contribution" step:

```javascript
let comment = `Your custom message here @${author}!\n\n`;
// ... rest of the message
```

### Disable First Contribution Detection

Remove or comment out the search API step and the first contribution logic.

## Bot Filtering

The workflow automatically skips:

- Accounts with GitHub type `Bot`
- Accounts whose login ends in `[bot]`

This prevents automated PRs (e.g., Dependabot, Renovate) from receiving congratulations.

## Logging

The workflow logs structured information for every execution:

| Field | Description |
|-------|-------------|
| `PR Number` | The PR number |
| `PR Title` | The title of the PR |
| `Author` | GitHub username of the PR author |
| `Merge Commit SHA` | The SHA of the merge commit |
| `First Contrib.` | Whether this is the author's first contribution |
| `Action Taken` | `commented`, `skipped_bot`, or error |

## Files

| File | Purpose |
|------|---------|
| `.github/workflows/pr-congratulations.yml` | Main workflow definition |
| `.github/workflows/README-pr-congratulations.md` | This documentation |

## Security Considerations

1. **`pull_request_target`**: Runs in base branch context — safe for forks
2. **Least privilege**: Only `pull-requests: write` and `contents: read`
3. **No external actions**: Uses only `actions/github-script@v7`
4. **Bot filtering**: Prevents automated accounts from triggering comments
5. **Graceful degradation**: API failures don't break the workflow

## Troubleshooting

### Comment not posted

1. Check if the PR was actually merged (not just closed)
2. Check if the target branch is `main`
3. Check if the author is a bot
4. Check workflow logs for API errors

### Wrong first contribution detection

GitHub's search index may lag behind. If a contributor's PR isn't showing up:
- Wait a few minutes for indexing
- The workflow defaults to `false` on API failure

### Workflow not triggering

Ensure:
- The workflow file is on the default branch (`main`)
- `pull_request_target` is configured correctly
- The PR targets `main` specifically
