# INSTRUCTIONS.md — Writing Rules

> Rules for all generated GitHub content (issues, PRs, commits, docs).

---

## Markdown Rules

- Always use GitHub Flavored Markdown (GFM)
- Never generate malformed Markdown
- Use proper `##` headings, never bold text as headings
- Wrap file paths in backticks: `openagent_eval/diagnosis/chunking.py`
- Use forward slashes only (never `\`)

---

## Code & Commands

- Fenced code blocks with language identifiers
- Fenced bash blocks for commands
- Never place multi-line code inline

```python
def hello():
    print("Hello")
```

---

## File Paths

✅ `openagent_eval/diagnosis/chunking.py`
❌ `\openagent_eval\diagnosis\chunking.py`

---

## Lists & Checklists

- Use proper Markdown lists
- Use GitHub task lists: `- [ ] Tests added`

---

## Templates

**PR**: Summary · Changes · Testing · Checklist

**Issue**: Description · Current Behavior · Expected Behavior · Files to Look At · Acceptance Criteria

**Release Notes**: What's Changed · New Features · Bug Fixes · Documentation · Tests · Contributors

---

## Tone

Professional maintainer. Clear, concise, technically accurate. At most one emoji per section.

---

## Validation

Before output: Markdown renders correctly, file paths use `/`, code blocks fenced, headings consistent, links formatted.
