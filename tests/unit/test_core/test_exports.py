"""Tests for the public import surface of ``openagent_eval.core``.

Regression guard for #55: the core dataclasses (``EvaluationReport``,
``EvaluationResult``, ``PipelineResult``) must be importable directly from the
package, not only from their defining submodules.
"""

from __future__ import annotations

import openagent_eval.core as core
from openagent_eval.core.engine import EvaluationReport as EngineEvaluationReport
from openagent_eval.core.pipeline import EvaluationResult as PipelineEvaluationResult
from openagent_eval.core.pipeline import PipelineResult as PipelinePipelineResult


def test_all_lists_the_full_public_surface() -> None:
    """``__all__`` must enumerate exactly the intended public names."""
    assert set(core.__all__) == {
        "Engine",
        "EvaluationReport",
        "EvaluationResult",
        "Executor",
        "Pipeline",
        "PipelineResult",
        "Registry",
    }


def test_every_name_in_all_is_importable() -> None:
    """Every name in ``__all__`` must actually be a package attribute."""
    for name in core.__all__:
        assert hasattr(core, name), f"{name} listed in __all__ but not importable"


def test_dataclasses_reexported_are_the_defining_objects() -> None:
    """The re-exported dataclasses must be the same objects as their originals."""
    from openagent_eval.core import (
        EvaluationReport,
        EvaluationResult,
        PipelineResult,
    )

    assert EvaluationReport is EngineEvaluationReport
    assert EvaluationResult is PipelineEvaluationResult
    assert PipelineResult is PipelinePipelineResult
