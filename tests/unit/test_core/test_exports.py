"""Tests for the public import surface of ``openagent_eval.core``.

Regression guard for #55: every name in ``core.__all__`` must be importable
directly from the package, not only from its defining submodule, and must be
the exact same object as the one defined there (no accidental shadowing or
copying).
"""

from __future__ import annotations

import openagent_eval.core as core
from openagent_eval.core.engine import Engine as EngineEngine
from openagent_eval.core.engine import EvaluationReport as EngineEvaluationReport
from openagent_eval.core.executor import Executor as ExecutorExecutor
from openagent_eval.core.pipeline import EvaluationResult as PipelineEvaluationResult
from openagent_eval.core.pipeline import Pipeline as PipelinePipeline
from openagent_eval.core.pipeline import PipelineResult as PipelinePipelineResult
from openagent_eval.core.registry import Registry as RegistryRegistry


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


def test_reexported_names_are_the_defining_objects() -> None:
    """Every re-exported name must be the same object as its original."""
    from openagent_eval.core import (
        Engine,
        EvaluationReport,
        EvaluationResult,
        Executor,
        Pipeline,
        PipelineResult,
        Registry,
    )

    assert Engine is EngineEngine
    assert EvaluationReport is EngineEvaluationReport
    assert EvaluationResult is PipelineEvaluationResult
    assert Executor is ExecutorExecutor
    assert Pipeline is PipelinePipeline
    assert PipelineResult is PipelinePipelineResult
    assert Registry is RegistryRegistry
