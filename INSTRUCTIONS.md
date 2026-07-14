# Writing Rules

These rules apply to **all generated GitHub content**, including:

- Issues
- Pull Requests
- PR Reviews
- Issue Comments
- Discussions
- Release Notes
- Changelogs
- Commit Messages
- Documentation
- README updates
- Wiki pages

---

## Markdown

- Always use GitHub Flavored Markdown (GFM).
- Ensure the output renders correctly on GitHub.
- Never generate malformed Markdown.
- Never escape Markdown characters unnecessarily.

---

## Headings

Use proper Markdown headings.

```md
## Description

## Current Behavior

## Expected Behavior

## Steps to Reproduce

## Acceptance Criteria
```

Do not use bold text as section headings.

---

## File Paths

Always use forward slashes.

✅ `openagent_eval/diagnosis/chunking.py`

❌ `\openagent_eval\diagnosis\chunking.py`

Always wrap file paths in backticks.

---

## Code

Always use fenced code blocks with language identifiers.

```python
def hello():
    print("Hello")
```

Never place multi-line code inline.

---

## Commands

Always use fenced bash blocks.

```bash
pip install openagent-eval
pytest
```

---

## Lists

Use proper Markdown lists.

- First item
- Second item
- Third item

Do not create fake lists using manual spacing.

---

## Checklists

Use GitHub task lists.

```md
- [ ] Tests added
- [ ] Documentation updated
- [ ] Existing tests pass
```

---

## Tables

Use Markdown tables whenever comparing information.

| Metric | Value |
|--------|-------|
| Speed  | 42ms  |
| Memory | 128MB |

---

## Links

Use descriptive Markdown links whenever appropriate.

✅ `See the [installation guide](/docs/install.md) for details.`

❌ `See https://github.com/owner/repo/blob/main/docs/install.md for details.`

Avoid dumping raw URLs inside paragraphs.

---

## Release Notes

Always use the following structure:

```md
## 🚀 What's Changed

## ✨ New Features

## 🐛 Bug Fixes

## 📚 Documentation

## 🧪 Tests

## 👥 Contributors

## Full Changelog
```

---

## Pull Requests

Always include:

```md
## Summary

## Changes

## Testing

## Checklist
```

---

## Issues

Always include:

```md
## Description

## Current Behavior

## Expected Behavior

## Files to Look At

## Acceptance Criteria
```

---

## Comments

- Be concise.
- Be professional.
- Be friendly.
- Avoid unnecessary emojis.
- Use at most one emoji per section.

---

## Tone

Write like a professional maintainer of a large open-source project.

Be clear, concise, and technically accurate.

Avoid unnecessary verbosity.

---

## Final Validation

Before generating any GitHub content, verify that:

- Markdown renders correctly.
- File paths use `/`.
- Code blocks are fenced and syntax highlighted.
- Headings are consistent.
- Lists and checklists are valid.
- Links are formatted correctly.
- The output is ready to copy and paste into GitHub without modification.
