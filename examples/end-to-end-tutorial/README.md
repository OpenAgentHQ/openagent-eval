# End-to-End Tutorial — Free APIs + Local Embeddings

A complete, **executed** walkthrough of the OpenAgent Eval workflow using only free-tier
services: [Google Gemini](https://aistudio.google.com/apikey) as the LLM and a local
`sentence-transformers` model for embeddings. No paid API key, no external vector database, no
GPU. Built for [issue #241](https://github.com/OpenAgentHQ/openagent-eval/issues/241).

Start with [`tutorial.ipynb`](tutorial.ipynb) — this README covers setup, the honest notes from
actually running it, and troubleshooting.

## Files

| File | Purpose |
|---|---|
| `tutorial.ipynb` | The 6-section notebook: setup → data → config → run → analyze → improve |
| `openagent_eval_colab_tutorial.ipynb` | Comprehensive Google Colab tutorial for OpenAgent Eval |
| `config.yaml` | Evaluation configuration referenced throughout the notebook |
| `data/sample_qa.json` | 16 hand-authored QA pairs (question, ground truth, context) |
| `data/corpus.json` | 19 passages indexed by the local retriever (16 relevant + 3 distractors) |
| `requirements.txt` | Dependencies for this tutorial |

## Setup

### 1. Get a free Gemini API key

1. Go to <https://aistudio.google.com/apikey> and sign in with a Google account.
2. Click **Create API key**.
3. Export it in your shell before starting Jupyter:
   ```bash
   export GEMINI_API_KEY="your-key-here"
   ```
   (Never put the key in `config.yaml` or a notebook cell that gets committed — see
   "How the API key is handled" below.)

### 2. Install and run

```bash
cd examples/end-to-end-tutorial
pip install -r requirements.txt
jupyter notebook tutorial.ipynb
```

Or open it directly in Colab via the badge at the top of the notebook (you'll need to enter
your key with the `getpass` prompt in Section 1, or store it in Colab's Secrets manager under
the name `GEMINI_API_KEY`).

Works the same way on Windows, macOS, and Linux — everything here is plain Python and YAML, no
OS-specific paths or shell syntax beyond the one `export` line above (on Windows, use
`set GEMINI_API_KEY=your-key-here` in `cmd`, or `$env:GEMINI_API_KEY="your-key-here"` in
PowerShell).

## How the API key is handled

`config.yaml` never sets `llm.api_key`. When it's left unset, OpenAgent Eval's Gemini provider
falls back to the `GEMINI_API_KEY` environment variable automatically
(`openagent_eval/providers/llm/gemini.py`):

```python
resolved_api_key = api_key or os.environ.get("GEMINI_API_KEY")
```

So the key lives only in your shell/OS environment (or Colab Secrets) — it is never written to
disk, logged, or committed.

## What was actually run and verified

Everything below was executed for real while building this tutorial, not written from memory:

- **`data/sample_qa.json`'s 16 facts** were each independently verified by running the
  corresponding `sqlite3` code in this environment before being written down. Two facts that
  were initially planned — `Connection.backup()` and cross-thread reuse raising
  `ProgrammingError` — were **dropped** because both hung indefinitely in this sandbox
  (likely a threading restriction); they were replaced with facts confirmed to actually run
  (`cursor.description`, `check_same_thread=False`).
- **`sentence-transformers`** (`all-MiniLM-L6-v2`, CPU) was installed and loads real vectors —
  confirmed standalone in Section 2 of the notebook (`(2, 384)` float32 output) and again as
  part of the `memory` retriever during the live run in Section 4.
- **The full pipeline** (`oaeval run config.yaml`) was executed against the **live Gemini API**:
  6/6 items succeeded, 0 errors, with real generated answers and real metric scores (see
  Section 4-5 of the executed notebook for the exact numbers).
- **`jupyter nbconvert --to notebook --execute`** ran the whole notebook end to end with no
  errors; its outputs are committed (see "Notebook outputs" below).

## Two things that did NOT work as the issue's own config example assumed

The issue's proposed `config.yaml` used `api_key: ${GROQ_API_KEY}` / `${VAR}`-style
interpolation. That syntax is **not implemented anywhere in this codebase** — there is no
`${VAR}` expansion in `openagent_eval/config/loader.py` or elsewhere. Setting a literal
`${GEMINI_API_KEY}` string as `llm.api_key` would pass that literal (broken) string to the
provider. The working pattern, used throughout this tutorial, is to **omit `api_key` entirely**
and let each provider read its own environment variable directly (verified above).

The issue's config also nested embeddings under `retriever.settings.embeddings.provider`. The
actual schema (`openagent_eval/config/models.py`) is a sibling `retriever.embedder` block, not
a `settings.embeddings` sub-key — see `config.yaml` in this folder for the verified shape.

## Troubleshooting

**`gemini-2.5-flash` returns a 429 "quota exceeded" error after a handful of calls.** While
building this tutorial, `gemini-2.5-flash` hit a **free-tier daily quota of 20 requests per
project** (`quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier`) — a stricter limit than
the commonly-quoted 15 requests/*minute* figure, and one that resets daily rather than
per-minute. `gemini-2.5-flash-lite` (used in `config.yaml`) had independent quota headroom and
is what this tutorial actually runs against. If you hit a 429 on whichever model you're using,
either wait for the daily reset or switch to a different Gemini model / provider (Groq's free
tier is a good alternative — see the "Other providers" note in Section 3 of the notebook).

**`gemini-2.5-flash` intermittently returns `503 UNAVAILABLE: high demand`.** Observed under
`parallel: true` (the default) with 4 concurrent requests. `config.yaml` sets `parallel: false`
so requests go out one at a time — slower, but far more reliable on the free tier.

**`context_precision` / `context_recall` / `mrr` all read `0.0`.** These metrics compare
*retrieved* contexts against `ground_truth_contexts` (a **list** field) — not the singular
`context` field also present on each dataset item. `data/sample_qa.json` sets both;
if you add your own QA pairs, make sure to populate `ground_truth_contexts` too.

**`sentence-transformers` import/first-load is slow (10-20s or more).** That's normal —
it downloads and loads `all-MiniLM-L6-v2` (~90MB) on first use and caches it under
`~/.cache/huggingface/hub/` afterwards. Subsequent runs are much faster.

**`ModuleNotFoundError` for `openai`/`anthropic`/`groq`.** The retriever/LLM provider factory
imports several provider SDKs unconditionally, so `pip install openagent-eval` alone is not
enough — install with the `providers` extra: `pip install "openagent-eval[providers]"` (already
in `requirements.txt`).

## Notebook outputs

The committed `tutorial.ipynb` has **executed outputs**, matching the precedent set by
[`examples/openagent_eval_colab_tutorial.ipynb`](../openagent_eval_colab_tutorial.ipynb) (PR
#226), which also ships with real, executed output rather than a blank notebook — outputs are
what make "this actually runs" checkable without re-running it yourself. Absolute paths and the
API key were confirmed absent before committing (see the PR description for the verification
commands). One cell's animated progress-bar output (hundreds of near-duplicate spinner frames
from the live 6-call Gemini run) was collapsed to its header and final summary line, to keep the
diff readable — no content was fabricated, only repeated terminal-redraw frames were trimmed.

Generated evaluation reports (`reports/*.json`, `reports/*.md`) are **not** committed — they are
regenerated every time you run the notebook, the same convention the repo root already uses for
its own `/reports/` directory (see the local `.gitignore` in this folder).

## Note for maintainers: `config.yaml` needed a forced add

The repo root `.gitignore` has a blanket, unanchored `config.yaml` rule (and `config.*.yaml`) —
originally added to stop contributors' local eval configs from being committed by accident. It
also silently matches `examples/end-to-end-tutorial/config.yaml`, which the issue explicitly
asks for by that exact name. This file was added with `git add -f`, so it is intentionally
tracked despite being `.gitignore`d; anyone running a blanket `git add -A`/`git add .` in this
directory later won't accidentally re-add or drop it, since it's already tracked, but `git
status` conventions that assume "ignored == not a real file" may find that surprising. Worth a
follow-up: either carve an exception for `examples/**/config.yaml` in the root `.gitignore`, or
rename this file if that's preferred.

## Scope note on the issue's acceptance criteria

Every item in [issue #241](https://github.com/OpenAgentHQ/openagent-eval/issues/241)'s
requirements is met, with one deliberate scoping choice: the live-executed run in Section 4
evaluates **6 of the 16** dataset items (`dataset.limit: 6` in `config.yaml`), not all 16, to
stay comfortably inside the Gemini free tier's per-project daily quota discovered above. The
full 16-item dataset is present, valid, and ready to run — delete or raise `dataset.limit` to
evaluate all of it; expect that to take several minutes and to use closer to the daily quota.
