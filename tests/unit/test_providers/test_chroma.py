"""Tests for ChromaDB retriever adapter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# Skip tests if chromadb is not installed
chromadb = pytest.importorskip("chromadb", reason="chromadb not installed")

from openagent_eval.exceptions.provider import (
    ProviderConnectionError,
    ProviderExecutionError,
)
from openagent_eval.providers.models import Document
from openagent_eval.providers.retrievers._scoring import normalize_distance
from openagent_eval.providers.retrievers.chroma import ChromaRetriever


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_chromadb():
    """Create a mock chromadb module."""
    with patch("openagent_eval.providers.retrievers.chroma.chromadb") as mock_chroma:
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_chroma.Client.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_collection.count.return_value = 10  # Default count for most tests
        yield mock_chroma, mock_client, mock_collection


@pytest.fixture
def retriever(mock_chromadb):
    """Create a ChromaRetriever with mocked chromadb."""
    _, _, mock_collection = mock_chromadb
    mock_collection.query.return_value = {
        "ids": [["doc-1", "doc-2"]],
        "documents": [["First document", "Second document"]],
        "metadatas": [[{"source": "file1.txt"}, {"source": "file2.txt"}]],
        "distances": [[0.1, 0.3]],
    }
    return ChromaRetriever(collection_name="test_collection")


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------
class TestChromaRetrieverInit:
    """Tests for ChromaRetriever initialization."""

    def test_init_in_memory(self, mock_chromadb):
        """Retriever initializes in-memory when no persist_directory."""
        mock_chroma, mock_client, _ = mock_chromadb
        retriever = ChromaRetriever(collection_name="test")
        assert retriever.name == "chroma"
        assert retriever.collection_name == "test"
        assert retriever.distance_fn == "cosine"
        mock_chroma.Client.assert_called_once()

    def test_init_persistent(self, mock_chromadb):
        """Retriever initializes with PersistentClient when persist_directory given."""
        mock_chroma, mock_client, _ = mock_chromadb
        retriever = ChromaRetriever(
            collection_name="test",
            persist_directory="/tmp/chroma_db",
        )
        assert retriever.collection_name == "test"
        mock_chroma.PersistentClient.assert_called_once()

    def test_init_custom_distance_fn(self, mock_chromadb):
        """Retriever uses custom distance function."""
        _, _, mock_collection = mock_chromadb
        retriever = ChromaRetriever(
            collection_name="test",
            distance_fn="l2",
        )
        assert retriever.distance_fn == "l2"
        mock_collection.metadata == {"hnsw:space": "l2"}

    def test_init_connection_error(self):
        """Retriever raises ProviderConnectionError on init failure."""
        with patch("openagent_eval.providers.retrievers.chroma.chromadb") as mock_chroma:
            mock_chroma.Client.side_effect = Exception("Connection failed")
            with pytest.raises(ProviderConnectionError, match="Failed to initialize"):
                ChromaRetriever(collection_name="test")


# ---------------------------------------------------------------------------
# retrieve() tests
# ---------------------------------------------------------------------------
class TestChromaRetrieve:
    """Tests for ChromaRetriever.retrieve()."""

    @pytest.mark.asyncio
    async def test_retrieve_success(self, retriever: ChromaRetriever):
        """retrieve() returns Document list on success."""
        docs = await retriever.retrieve("machine learning", k=2)
        assert len(docs) == 2
        assert docs[0].content == "First document"
        assert docs[0].id == "doc-1"
        assert docs[0].metadata == {"source": "file1.txt"}
        assert docs[1].content == "Second document"
        assert docs[1].id == "doc-2"

    @pytest.mark.asyncio
    async def test_retrieve_scores_normalised(self, retriever: ChromaRetriever):
        """retrieve() normalises cosine distance to 0-1 range."""
        docs = await retriever.retrieve("test", k=2)
        # Cosine distance 0.1 / 2.0 = 0.05
        assert docs[0].score == pytest.approx(0.05)
        # Cosine distance 0.3 / 2.0 = 0.15
        assert docs[1].score == pytest.approx(0.15)

    @pytest.mark.asyncio
    async def test_retrieve_empty_results(self, mock_chromadb):
        """retrieve() returns empty list when no results."""
        _, _, mock_collection = mock_chromadb
        mock_collection.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        retriever = ChromaRetriever(collection_name="empty")
        docs = await retriever.retrieve("nonexistent query")
        assert docs == []

    @pytest.mark.asyncio
    async def test_retrieve_query_error(self, mock_chromadb):
        """retrieve() raises ProviderExecutionError on query failure."""
        _, _, mock_collection = mock_chromadb
        mock_collection.query.side_effect = Exception("Query failed")
        retriever = ChromaRetriever(collection_name="error")

        with pytest.raises(ProviderExecutionError, match="query failed"):
            await retriever.retrieve("test query")

    @pytest.mark.asyncio
    async def test_retrieve_with_l2_distance(self, mock_chromadb):
        """retrieve() handles L2 distance normalisation (clamped)."""
        _, _, mock_collection = mock_chromadb
        mock_collection.query.return_value = {
            "ids": [["doc-1"]],
            "documents": [["Test doc"]],
            "metadatas": [[{}]],
            "distances": [[2.5]],  # L2 distance > 1, should be clamped
        }
        retriever = ChromaRetriever(collection_name="l2_test", distance_fn="l2")
        docs = await retriever.retrieve("test", k=1)
        assert docs[0].score == 1.0  # Clamped to 1.0

    @pytest.mark.asyncio
    async def test_retrieve_negative_distance_clamped(self, mock_chromadb):
        """retrieve() clamps negative distances to 0.0."""
        _, _, mock_collection = mock_chromadb
        mock_collection.query.return_value = {
            "ids": [["doc-1"]],
            "documents": [["Test doc"]],
            "metadatas": [[{}]],
            "distances": [[-0.5]],  # Negative distance, should be clamped
        }
        retriever = ChromaRetriever(collection_name="neg_test")
        docs = await retriever.retrieve("test", k=1)
        assert docs[0].score == 0.0  # Clamped to 0.0

    @pytest.mark.asyncio
    async def test_retrieve_passes_query_to_collection(self, retriever: ChromaRetriever):
        """retrieve() passes query and k to collection.query()."""
        await retriever.retrieve("test query", k=3)
        retriever._collection.query.assert_called_once_with(
            query_texts=["test query"],
            n_results=3,
            include=["documents", "metadatas", "distances"],
        )

    # --- M16 regression test ---
    @pytest.mark.asyncio
    async def test_retrieve_clamps_n_results(self, mock_chromadb):
        """M16: n_results must be clamped to collection.count()."""
        _, _, mock_collection = mock_chromadb
        mock_collection.count.return_value = 2
        mock_collection.query.return_value = {
            "ids": [["d1", "d2"]],
            "documents": [["A", "B"]],
            "metadatas": [[{}, {}]],
            "distances": [[0.1, 0.2]],
        }
        retriever = ChromaRetriever(collection_name="small")
        docs = await retriever.retrieve("query", k=10)
        assert len(docs) == 2
        # The actual call should have n_results=2 (clamped), not 10.
        mock_collection.query.assert_called_once_with(
            query_texts=["query"],
            n_results=2,
            include=["documents", "metadatas", "distances"],
        )


# ---------------------------------------------------------------------------
# Distance normalisation tests
# ---------------------------------------------------------------------------
class TestChromaNormaliseDistance:
    """Tests for normalize_distance() from _scoring module."""

    def test_cosine_normalisation(self):
        """Cosine distance is divided by 2."""
        assert normalize_distance(0.0, space="cosine") == 0.0
        assert normalize_distance(1.0, space="cosine") == 0.5
        assert normalize_distance(2.0, space="cosine") == 1.0

    def test_l2_normalisation_clamped(self):
        """L2 distance is clamped to 0-1."""
        assert normalize_distance(0.0, space="l2") == 0.0
        assert normalize_distance(0.5, space="l2") == 0.5
        assert normalize_distance(1.5, space="l2") == 1.0

    def test_negative_distance_clamped(self):
        """Negative distances are clamped to 0."""
        assert normalize_distance(-1.0, space="cosine") == 0.0
