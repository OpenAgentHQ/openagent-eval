# Release Checklist

Quick reference for releasing new versions of OpenAgent Eval.

---

## Pre-Release

- [ ] All tests pass (`pytest`)
- [ ] Linting passes (`ruff check .`)
- [ ] Formatting passes (`ruff format .`)
- [ ] CI is green
- [ ] Package builds successfully (`uv build`)
- [ ] Documentation is up to date

---

## Update Version

- [ ] Update `pyproject.toml` version
- [ ] Update `openagent_eval/__init__.py` version (must match)
- [ ] Update `CHANGELOG.md` with all changes since last release
- [ ] Update comparison links in CHANGELOG.md

---

## Create Release Branch & PR

```bash
git checkout main
git pull origin main
git checkout -b release/vX.Y.Z
git add pyproject.toml openagent_eval/__init__.py CHANGELOG.md uv.lock
git commit -m "chore: release vX.Y.Z"
git push -u origin release/vX.Y.Z
gh pr create --title "chore: release vX.Y.Z" --base main
```

- [ ] PR created and reviewed
- [ ] PR merged

---

## Tag Release

```bash
git checkout main
git pull origin main
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

- [ ] Tag created and pushed

---

## GitHub Release

- [ ] GitHub Release created with descriptive title: `vX.Y.Z – [Title]`
- [ ] Release notes include PR links: `- **Name** — description (#PR_NUMBER)`
- [ ] Release notes include Contributors section

---

## Post-Release Verification

- [ ] Git tag exists (`git tag -l "vX.Y.Z"`)
- [ ] GitHub Release exists (`gh release view vX.Y.Z`)
- [ ] Package available on PyPI (`pip install openagent-eval==X.Y.Z`)
- [ ] CLI reports correct version (`oaeval --version`)
- [ ] CI workflow completed successfully

---

## Semantic Versioning

| Change | Example |
|--------|---------|
| PATCH (bug fixes, docs, internal) | 0.4.5 → 0.4.6 |
| MINOR (backward-compatible features) | 0.4.5 → 0.5.0 |
| MAJOR (breaking changes) | 1.x.x → 2.0.0 |

---

## Release Notes Format

```markdown
## What's Changed

### ✨ Features
- **Feature Name** — description (#PR_NUMBER)

### 🐛 Bug Fixes
- **Fix Name** — description (#PR_NUMBER)

### 📚 Documentation
- **Doc Change** — description (#PR_NUMBER)

### ⚙️ Testing
- **Test Change** — description (#PR_NUMBER)

### ⚙️ Internal
- **Internal Change** — description (#PR_NUMBER)

### ❤️ Contributors
- @contributor1

**Full Changelog**: https://github.com/openagenthq/openagent-eval/compare/vPREV...vX.Y.Z
```

---

## Files Involved

| File | Purpose |
|------|---------|
| `pyproject.toml` | Canonical version |
| `openagent_eval/__init__.py` | Runtime version |
| `CHANGELOG.md` | Release history |
| `uv.lock` | Lock file |
| `.github/workflows/release.yml` | PyPI publish |

---

## Troubleshooting

### Version mismatch
Always update both `pyproject.toml` and `__init__.py` — they must match.

### Push rejected
Use PR workflow — direct push to `main` is blocked.

### Tag exists
```bash
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z
```
