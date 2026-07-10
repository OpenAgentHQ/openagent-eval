# HTTP (generic REST)

The HTTP retriever calls **any REST search endpoint** and maps the JSON
response into documents via simple field paths. Zero additional dependencies
beyond `httpx` (already installed).

## When should you use this?

Use it when you have an existing search API — Elasticsearch `_search`, a
custom backend, a managed vector DB's REST endpoint — and want to evaluate it
without writing a dedicated adapter.

## Prerequisites

No extra installation needed — `httpx` is already a dependency.

## Step 1 — Configure

=== "POST (JSON body)"

    ```yaml title="config.yaml"
    retriever:
      provider: http
      settings:
        url: http://localhost:8080/api/search
        method: POST
        query_field: q
        k_field: limit
        results_path: hits
        content_path: _source.text
        id_path: _id
        score_path: _score
        score_mode: minmax
    ```

=== "GET (query params)"

    ```yaml title="config.yaml"
    retriever:
      provider: http
      settings:
        url: http://localhost:8080/api/search
        method: GET
        query_field: q
        k_field: limit
        results_path: results
        content_path: content
        score_path: relevance
    ```

## Step 2 — Run

```bash
oaeval run config.yaml
```

## Python SDK example

```python title="eval_http.py"
import asyncio

from openagent_eval.config.models import Config, RetrieverConfig
from openagent_eval.core.engine import Engine

config = Config(
    dataset={"path": "data/questions.json"},
    llm={"provider": "mock"},
    retriever=RetrieverConfig(
        provider="http",
        settings={
            "url": "http://localhost:8080/api/search",
            "method": "POST",
            "query_field": "q",
            "results_path": "hits",
            "content_path": "_source.text",
            "score_path": "_score",
            "score_mode": "minmax",
        },
    ),
    metrics={"retrieval": ["context_precision", "context_recall", "mrr"]},
)

engine = Engine(config)
report = asyncio.run(engine.run(dataset))
print(report.summary["metrics_summary"])
```

## All configuration options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `url` | `str` | — | **Required.** Endpoint URL. |
| `method` | `str` | `POST` | HTTP method (`POST` or `GET`). |
| `headers` | `dict \| null` | `null` | Request headers (e.g., auth). |
| `query_field` | `str` | `query` | JSON key for the query text. |
| `k_field` | `str` | `k` | JSON key for the result count. |
| `content_path` | `str` | `content` | Dot-path to content in each result. |
| `id_path` | `str \| null` | `null` | Dot-path to the document id. |
| `score_path` | `str \| null` | `null` | Dot-path to the raw score. |
| `metadata_path` | `str \| null` | `null` | Dot-path to metadata object. |
| `results_path` | `str \| null` | `null` | Dot-path to the result list. |
| `score_mode` | `str` | `passthrough` | `passthrough` (clamp) or `minmax`. |
| `timeout` | `float` | `30.0` | Request timeout in seconds. |

## How scoring works

- **With `score_path`**: Raw scores are extracted from each result. Use
  `score_mode: minmax` to normalize the batch into `[0, 1]`, or
  `passthrough` to clamp to `[0, 1]`.
- **Without `score_path`**: Rank-based scoring is used (first result = 1.0,
  last = lowest).

## Troubleshooting

- **`ProviderConnectionError`** — Ensure `url` is set and the endpoint is
  reachable.
- **Empty results** — Check `results_path` matches your response structure.
  If the response is a flat list, omit `results_path`.
- **Wrong content** — Adjust `content_path` to match the JSON structure of
  each hit.

## Related

- Need a dedicated Elasticsearch adapter? See
  [Elasticsearch](elasticsearch.md).
- Need a lexical baseline? See [BM25](bm25.md).
- Pair with an LLM from [../llm/index.md](../llm/index.md).
