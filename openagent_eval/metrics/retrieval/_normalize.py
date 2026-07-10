"""Shared text helpers for retrieval metrics."""

from __future__ import annotations


def normalize_context(text: str) -> str:
    """Normalize a context string for relevance comparison.

    Lowercases and collapses all whitespace (including newlines/tabs) to single
    spaces, and strips leading/trailing whitespace. This makes exact-match
    relevance checks robust to harmless formatting differences (whitespace,
    casing) between retrieved and gold contexts while preserving true exact
    matches.
    """
    return " ".join(text.lower().split())
