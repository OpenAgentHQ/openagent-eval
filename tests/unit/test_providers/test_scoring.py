"""Tests for the shared score-normalization helpers."""

from __future__ import annotations

import pytest

from openagent_eval.providers.retrievers._scoring import (
    minmax_normalize,
    normalize_distance,
    rank_based_normalize,
)


class TestNormalizeDistance:
    def test_cosine_divided_by_two(self):
        assert normalize_distance(0.0, "cosine") == 0.0
        assert normalize_distance(1.0, "cosine") == 0.5
        assert normalize_distance(2.0, "cosine") == 1.0

    def test_l2_clamped(self):
        assert normalize_distance(0.0, "l2") == 0.0
        assert normalize_distance(0.5, "l2") == 0.5
        assert normalize_distance(5.0, "l2") == 1.0

    def test_ip_clamped(self):
        assert normalize_distance(-1.0, "ip") == 0.0
        assert normalize_distance(0.3, "ip") == 0.3
        assert normalize_distance(2.0, "ip") == 1.0

    def test_similarity_passthrough(self):
        assert normalize_distance(0.7, "similarity") == 0.7

    def test_unknown_space_clamped(self):
        assert normalize_distance(-3.0, "weird") == 0.0
        assert normalize_distance(9.0, "weird") == 1.0


class TestMinmaxNormalize:
    def test_basic(self):
        assert minmax_normalize([0.0, 5.0, 10.0]) == [0.0, 0.5, 1.0]

    def test_constant_list_maps_to_one(self):
        assert minmax_normalize([3.0, 3.0, 3.0]) == [1.0, 1.0, 1.0]

    def test_empty(self):
        assert minmax_normalize([]) == []


class TestRankBasedNormalize:
    def test_top_rank_is_one(self):
        scores = rank_based_normalize(3)
        assert scores[0] == 1.0
        assert scores == [1.0, pytest.approx(2 / 3), pytest.approx(1 / 3)]

    def test_empty(self):
        assert rank_based_normalize(0) == []
