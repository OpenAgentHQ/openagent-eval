# Issue Claim System

> Automatic issue assignment via GitHub Actions using slash commands.

## Overview

The Issue Claim System allows contributors to claim, assign, and release issues directly from issue comments using slash commands. It runs entirely on GitHub Actions — no external servers or paid services required.

## How It Works

1. A contributor comments on an open issue with a slash command
2. GitHub Actions triggers the workflow
3. The workflow validates the context (PR vs issue, open vs closed, bot vs human)
4. The command is parsed and routed to the appropriate handler
5. The issue is assigned/released and a confirmation comment is posted

## Supported Commands

### `/claim`

Claims an unassigned issue for the commenter.

**Usage:**
```
/claim
```

**Behavior:**
- ✅ If issue is unassigned → assigns to commenter, adds `in-progress` label, posts success message
- ❌ If issue is already assigned → posts rejection with current assignee info
- ❌ If commenter is a bot → silently ignored
- ❌ If issue is closed → silently ignored

**Example response:**
> 🎉 Thanks @username!
>
> This issue has been assigned to you.
>
> Happy coding! 🚀

---

### `/assign @username`

Assigns an issue to a specific user. **Maintainer-only command.**

**Usage:**
```
/assign @target-user
```

**Behavior:**
- ✅ If commenter is a maintainer → assigns target user, adds `in-progress` label
- ❌ If commenter is not a maintainer → rejected with permission error
- ❌ If no target user specified → shows usage instructions
- ❌ If target user already assigned → shows info message

**Example response (success):**
> ✅ @target-user has been assigned to this issue by @maintainer.
>
> Happy coding! 🚀

**Example response (rejected):**
> ❌ Only maintainers can manually assign issues.

---

### `/release`

Releases a claimed issue back to the contributor pool. **Current assignee only.**

**Usage:**
```
/release
```

**Behavior:**
- ✅ If commenter is the assignee → removes assignee, removes `in-progress` label
- ❌ If commenter is not the assignee → rejected with current assignee info
- ❌ If issue is not assigned → shows info message

**Example response:**
> 🔄 Issue has been released and is now available for contributors.

## Labels

The workflow manages these labels automatically:

| Label | Added | Removed |
|-------|-------|---------|
| `in-progress` | On `/claim` or `/assign` | On `/release` |
| `good first issue` | Manual only | — |
| `help wanted` | Manual only | — |

> **Note:** If a label doesn't exist in the repository, the workflow skips it gracefully without failing.

## Required Permissions

The workflow uses these GitHub Actions permissions:

```yaml
permissions:
  issues: write       # Assign/unassign users, add labels, post comments
  contents: read      # Read repository metadata
  pull-requests: read # Detect PR vs issue comments
```

These are **minimum required permissions** following the principle of least privilege.

## Edge Cases Handled

| Scenario | Behavior |
|----------|----------|
| Comment on a PR | Silently ignored (issue_comment fires on PRs too) |
| Comment on a closed issue | Silently ignored |
| Bot comments | Silently ignored |
| Non-slash comments | Silently ignored |
| Unknown commands (e.g., `/help`) | Silently ignored |
| Target user doesn't exist | Error message posted |
| Label doesn't exist | Warning logged, workflow continues |
| GitHub API failure | Error logged, user-friendly message posted |
| Multiple assignees | Handled correctly in all commands |
| Concurrent comments | Serialized via concurrency control |

## Architecture

```
.github/workflows/issue-claim.yml
├── Context Extraction    — Pure functions to extract data from event payload
├── Logging               — Structured logging for debugging and audit
├── Permission Checks     — Verify user roles and access
├── Label Management      — Safe label operations (never fails)
├── Comment Helpers       — Post formatted comments
├── Command Handlers      — Isolated handlers for each command
│   ├── handleClaim       — /claim logic
│   ├── handleAssign      — /assign logic
│   └── handleRelease     — /release logic
├── Command Router        — Routes commands to handlers
├── Guard Clauses         — Pre-flight validation
└── Main Entry Point      — Orchestrates the workflow
```

## Security Considerations

1. **Least privilege permissions** — Only requests permissions needed for the workflow
2. **Maintainer-only commands** — `/assign` verifies collaborator permission level
3. **Bot detection** — Ignores comments from GitHub Apps bots
4. **PR guard** — Skips PR comments to prevent unintended assignments
5. **No secrets exposed** — Only uses `GITHUB_TOKEN` (auto-generated)
6. **Input sanitization** — Comment body is trimmed and parsed safely
7. **Concurrency control** — Prevents race conditions on simultaneous comments

## Testing

### Manual Testing

1. **Test `/claim`:**
   - Open an unassigned issue
   - Comment `/claim`
   - Verify: Issue assigned to you, `in-progress` label added, success comment posted

2. **Test `/claim` on assigned issue:**
   - Open an issue assigned to someone else
   - Comment `/claim`
   - Verify: Rejection comment with current assignee info

3. **Test `/assign`:**
   - Open an unassigned issue (as a maintainer)
   - Comment `/assign @some-user`
   - Verify: User assigned, `in-progress` label added, confirmation comment

4. **Test `/assign` (non-maintainer):**
   - Open an unassigned issue (as a non-maintainer)
   - Comment `/assign @some-user`
   - Verify: Permission error message

5. **Test `/release`:**
   - Open an issue assigned to you
   - Comment `/release`
   - Verify: Assignee removed, `in-progress` label removed, confirmation comment

6. **Test PR comment:**
   - Open a PR
   - Comment `/claim`
   - Verify: Workflow ignores the comment

### Automated Testing

To add automated tests, create a test workflow that:
1. Uses `peter-evans/create-or-update-comment` to post test comments
2. Uses `actions/github-script` to verify issue state
3. Cleans up test issues after testing

## Customization

### Adding New Commands

1. Add a new handler function in the `Command Handlers` module
2. Add the command to the `routeCommand` switch statement
3. Update the `parseCommand` function if the command has special syntax

Example:
```javascript
const handleThank = async (github, ctx) => {
  await postComment(github, ctx,
    `Thank you @${ctx.commenter} for your contribution! 🙏`
  );
};

// In routeCommand:
case '/thank':
  await handleThank(github, ctx);
  break;
```

### Adding Discord/Slack Notifications

Add a notification step after successful assignment:

```javascript
// After handleClaim succeeds:
const notifyDiscord = async (ctx) => {
  const webhookUrl = process.env.DISCORD_WEBHOOK_URL;
  if (!webhookUrl) return;

  await fetch(webhookUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      content: `🎉 @${ctx.commenter} claimed issue #${ctx.issueNumber}: ${ctx.issueTitle}`
    }),
  });
};
```

### Adding Auto-Unassign (7-Day Inactivity)

Use a scheduled workflow to check for inactive assignments:

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  auto-unassign:
    runs-on: ubuntu-latest
    steps:
      - name: Check inactive assignments
        uses: actions/github-script@v7
        with:
          script: |
            // Query issues with in-progress label
            // Check last activity date
            // Release if inactive for 7+ days
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Workflow doesn't trigger | Verify the comment starts with `/` and the issue is open |
| Assignment fails | Check that `GITHUB_TOKEN` has `issues: write` permission |
| Label not added | Verify the label exists in repository settings |
| `/assign` rejected | Verify you have write access to the repository |
| Comment not posted | Check workflow logs for API errors |

## Future Enhancements

- [ ] Auto-unassign after 7 days of inactivity
- [ ] Contributor leaderboard tracking
- [ ] Welcome messages for first-time contributors
- [ ] Automatic thank-you comments after merge
- [ ] Discord/Slack notifications
- [ ] Metrics collection (claim frequency, resolution time)
- [ ] Priority-based claiming (contributors with more merges get priority)
- [ ] Time-limited claims (auto-release after X days)

## Related Files

- `.github/workflows/issue-claim.yml` — Main workflow file
- `.github/ISSUE_TEMPLATE/` — Issue templates (optional)
- `CONTRIBUTING.md` — Contribution guidelines
- `CODE_OF_CONDUCT.md` — Community standards
