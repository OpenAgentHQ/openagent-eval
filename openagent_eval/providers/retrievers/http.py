"""Generic HTTP retriever for OpenAgent Eval.

A zero-dependency (uses the already-installed ``httpx``) retriever that calls
any REST search endpoint and maps the JSON response into
``Document`` objects via simple field paths. This lets you point OpenAgent Eval
at an existing search service (Elasticsearch ``_search``, a custom API, a
managed vector DB's REST endpoint) without writing a dedicated adapter.

Configuration (``retriever.settings``):
    url:          Endpoint URL (required).
    method:       HTTP method (default ``POST``).
    headers:      Optional dict of request headers (e.g. auth).
    query_field:  JSON key in the request body holding the query
                  (default ``"query"``). For GET, the query is sent as this
                  query-parameter name.
    k_field:      JSON key in the request body holding ``k`` (default ``"k"``).
    content_path: Dot-path to the content string in each result
                  (default ``"content"``).
    id_path:      Dot-path to the id in each result (optional).
    score_path:   Dot-path to the raw score in each result (optional). When
                  omitted, results are ranked by array order.
    metadata_path:Dot-path to a metadata object in each result (optional).
    results_path: Optional dot-path to the result list in the response
                  (optional; if omitted the top-level response is treated as
                  the list).
    score_mode:  How to treat ``score_path`` values: ``"passthrough"`` (default,
                 clamp to ``[0, 1]``) or ``"minmax"`` (rescale the batch into
                 ``[0, 1]``). Ignored when ``score_path`` is omitted (rank-based
                 scoring is used instead).
"""

from __future__ import annotations

from typing import Any

import httpx

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.base.retriever import Retriever
from openagent_eval.providers.models import Document
from openagent_eval.providers.retrievers._scoring import (
    minmax_normalize,
    rank_based_normalize,
)


def _dig(obj: Any, path: str | None) -> Any:
    """Resolve a dot-path (e.g. ``"hits.hits"``) inside a nested mapping."""
    if not path:
        return obj
    cur: Any = obj
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list) and part.isdigit():
            idx = int(part)
            cur = cur[idx] if idx < len(cur) else None
        else:
            return None
        if cur is None:
            return None
    return cur


class HttpRetriever(Retriever):
    """Generic REST search retriever (httpx)."""

    name: str = "http"
    description: str = "Generic HTTP/REST search retriever (httpx)"

    def __init__(
        self,
        url: str,
        method: str = "POST",
        headers: dict[str, str] | None = None,
        query_field: str = "query",
        k_field: str = "k",
        content_path: str = "content",
        id_path: str | None = None,
        score_path: str | None = None,
        metadata_path: str | None = None,
        results_path: str | None = None,
        score_mode: str = "passthrough",
        timeout: float = 30.0,
        **_: Any,
    ) -> None:
        """Initialize the HTTP retriever.

        Args:
            url: Endpoint URL (required).
            method: HTTP method (default ``POST``).
            headers: Optional request headers.
            query_field: Request body/query-param key for the query.
            k_field: Request body key for ``k``.
            content_path: Dot-path to content in each result.
            id_path: Optional dot-path to id in each result.
            score_path: Optional dot-path to raw score in each result.
            metadata_path: Optional dot-path to metadata object.
            results_path: Optional dot-path to the result list in the response.
            score_mode: ``"passthrough"`` (clamp) or ``"minmax"`` for scores.
            timeout: Request timeout in seconds.
        """
        if not url:
            raise ProviderConnectionError(
                message="HttpRetriever requires a 'url' setting",
                provider_name=self.name,
            )
        self._url = url
        self._method = method.upper()
        self._headers = headers or {}
        self._query_field = query_field
        self._k_field = k_field
        self._content_path = content_path
        self._id_path = id_path
        self._score_path = score_path
        self._metadata_path = metadata_path
        self._results_path = results_path
        self._score_mode = score_mode
        self._timeout = timeout

    async def retrieve(self, query: str, k: int = 5) -> list[Document]:
        """Send the query to the endpoint and map the response to Documents."""
        self.validate_inputs(query=query, k=k)

        if self._method == "GET":
            params = {self._query_field: query, self._k_field: k}
            body: dict[str, Any] | None = None
        else:
            params = None
            body = {self._query_field: query, self._k_field: k}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.request(
                    self._method,
                    self._url,
                    json=body,
                    params=params,
                    headers=self._headers,
                )
                resp.raise_for_status()
                payload = resp.json()
        except httpx.HTTPError as exc:
            raise ProviderExecutionError(
                message=f"HTTP retriever request to {self._url} failed: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

        items = _dig(payload, self._results_path)
        if items is None:
            items = payload  # treat top-level response as the list
        if not isinstance(items, list):
            raise ProviderExecutionError(
                message=f"HTTP retriever: expected a list at '{self._results_path or '<root>'}', "
                f"got {type(items).__name__}",
                provider_name=self.name,
            )

        items = items[:k]
        if not items:
            return []

        if self._score_path:
            raw_scores = [float(_dig(item, self._score_path)) for item in items]
            if self._score_mode == "minmax":
                norm = minmax_normalize(raw_scores)
            else:
                norm = [max(0.0, min(1.0, s)) for s in raw_scores]
        else:
            norm = rank_based_normalize(len(items))

        documents: list[Document] = []
        for i, item in enumerate(items):
            content = _dig(item, self._content_path)
            if content is None:
                continue
            documents.append(
                Document(
                    content=str(content),
                    metadata=_dig(item, self._metadata_path) or {},
                    score=norm[i],
                    id=_dig(item, self._id_path) if self._id_path else None,
                )
            )
        return documents
