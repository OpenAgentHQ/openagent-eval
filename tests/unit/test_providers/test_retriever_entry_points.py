"""Resolve retrievers through installed distribution metadata."""

import pytest

from openagent_eval.config.models import EmbedderConfig, RetrieverConfig
from openagent_eval.exceptions.provider import ProviderError, ProviderNotFoundError
from openagent_eval.providers.factory import get_retriever
from openagent_eval.providers.retrievers.mock import MockRetriever


class ArchiveRetriever(MockRetriever):
    SETTINGS_KEYS = {"collection_name"}

    def __init__(self, collection_name="archive", embedder=None):
        super().__init__(collection_name=collection_name)
        self.embedder = embedder


@pytest.fixture
def installed_retrievers(tmp_path, monkeypatch):
    dist = tmp_path / "archive_search-1.0.dist-info"
    dist.mkdir()
    (dist / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: archive-search\nVersion: 1.0\n"
    )
    (dist / "entry_points.txt").write_text(
        "[openagent_eval.retrievers]\n"
        f"archive = {__name__}:ArchiveRetriever\n"
        f"mock = {__name__}:ArchiveRetriever\n"
        "unavailable = missing_retriever_package:Retriever\n"
        "invalid = builtins:str\n"
        "duplicate = builtins:int\n"
        "Duplicate = builtins:str\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))


def test_plugin_uses_existing_settings_and_embedder_path(installed_retrievers, caplog):
    config = RetrieverConfig(
        provider=" Archive ",
        settings={"collection_name": "notices", "collectoin_name": "typo"},
        embedder=EmbedderConfig(provider="mock", model="mock"),
    )
    retriever = get_retriever(config)
    assert isinstance(retriever, ArchiveRetriever)
    assert retriever.collection_name == "notices"
    assert retriever.embedder.name == "mock"
    assert "collectoin_name" in caplog.text
    assert "collectoin_name" in config.settings


def test_plugin_precedes_builtin(installed_retrievers):
    assert isinstance(get_retriever(RetrieverConfig(provider="mock")), ArchiveRetriever)


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("unavailable", "Cannot load"),
        ("invalid", "Retriever subclass"),
        ("duplicate", "Multiple installed"),
    ],
)
def test_invalid_plugin_reports_reason(installed_retrievers, name, message):
    with pytest.raises(ProviderError, match=message):
        get_retriever(RetrieverConfig(provider=name))


def test_unknown_name_lists_plugins_and_builtins(installed_retrievers):
    with pytest.raises(ProviderNotFoundError) as error:
        get_retriever(RetrieverConfig(provider="absent"))
    choices = error.value.details["available_retrievers"].split(", ")
    assert {"archive", "memory"} <= set(choices)
