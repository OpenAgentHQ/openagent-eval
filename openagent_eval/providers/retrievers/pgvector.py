"""pgvector retriever adapter for OpenAgent Eval.

Queries a Postgres table with the ``pgvector`` extension using cosine (or L2)
similarity. Documents/queries are embedded locally with the configured
:class:`~openagent_eval.providers.embedders.base.Embedder`.
"""

from __future__ import annotations

from typing import Any

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.base.retriever import Retriever
from openagent_eval.providers.embedders.base import Embedder
from openagent_eval.providers.models import Document


class PGVectorRetriever(Retriever):
    """Postgres + pgvector retriever."""

    name: str = "pgvector"
    description: str = "PostgreSQL pgvector retriever"

    def __init__(
        self,
        table: str,
        embedder: Embedder | None = None,
        dsn: str | None = None,
        content_column: str = "content",
        embedding_column: str = "embedding",
        metric: str = "cosine",
        **_: Any,
    ) -> None:
        """Initialize the pgvector retriever.

        Args:
            table: Table (or view) containing the embeddings.
            embedder: Required embedder for the query vector.
            dsn: Postgres DSN (or ``DATABASE_URL`` env).
            content_column: Column holding document text.
            embedding_column: Column holding the ``vector``.
            metric: ``"cosine"`` (default) or ``"l2"``.
        """
        if embedder is None:
            raise ProviderConnectionError(
                message="PGVectorRetriever requires an embedder (set retriever.embedder)",
                provider_name=self.name,
            )
        self._table = table
        self._embedder = embedder
        self._dsn = dsn
        self._content_column = content_column
        self._embedding_column = embedding_column
        self._metric = metric
        self._conn: Any = None

        try:
            import psycopg
        except ImportError as exc:  # pragma: no cover - depends on installed dep
            raise ImportError(
                "psycopg + pgvector are required for the pgvector retriever. "
                "Install it with: pip install openagent-eval[pgvector]"
            ) from exc

    async def _ensure_connection(self) -> None:
        """Lazily open the async Postgres connection on first use.

        The async cursor API requires an :class:`psycopg.AsyncConnection`,
        which can only be created with ``await``. We therefore defer
        connection establishment out of ``__init__`` and into the async
        ``retrieve`` path.
        """
        if self._conn is not None:
            return
        import psycopg

        try:
            self._conn = await psycopg.AsyncConnection.connect(
                self._dsn, autocommit=True
            )
        except Exception as exc:
            raise ProviderConnectionError(
                message=f"Failed to connect to Postgres: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

    async def retrieve(self, query: str, k: int = 5) -> list[Document]:
        """Embed the query and run a similarity SQL query."""
        self.validate_inputs(query=query, k=k)

        # Connection failures must surface as ProviderConnectionError, not be
        # swallowed into the query-execution error below.
        await self._ensure_connection()

        try:
            vector = await self._embedder.embed_query(query)
            vec_literal = "[" + ",".join(f"{v:.8f}" for v in vector) + "]"

            if self._metric == "l2":
                sql = (
                    f"SELECT {self._content_column}, "
                    f"{self._embedding_column} <-> %s::vector AS dist "
                    f"FROM {self._table} "
                    f"ORDER BY {self._embedding_column} <-> %s::vector LIMIT %s"
                )
                params: tuple[Any, ...] = (vec_literal, vec_literal, k)
            else:
                sql = (
                    f"SELECT {self._content_column}, "
                    f"1 - ({self._embedding_column} <=> %s::vector) AS score "
                    f"FROM {self._table} "
                    f"ORDER BY {self._embedding_column} <=> %s::vector LIMIT %s"
                )
                params = (vec_literal, vec_literal, k)

            async with self._conn.cursor() as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()
        except Exception as exc:
            raise ProviderExecutionError(
                message=f"pgvector query failed: {exc}",
                provider_name=self.name,
                original_error=exc,
            ) from exc

        documents: list[Document] = []
        for row in rows:
            content = row[0]
            if self._metric == "l2":
                score = max(0.0, 1.0 - float(row[1]))
            else:
                score = float(row[1])
            documents.append(
                Document(
                    content=str(content),
                    metadata={},
                    score=max(0.0, min(1.0, score)),
                    id=None,
                )
            )
        return documents

    async def close(self) -> None:
        """Close the underlying async connection if open."""
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
