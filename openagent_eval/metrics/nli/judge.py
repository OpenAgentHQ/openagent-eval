"""NLI Judge using DeBERTa Natural Language Inference model.

Provides NLI-based scoring for faithfulness and relevancy metrics.
Uses a pretrained DeBERTa model fine-tuned on NLI tasks to determine
whether a hypothesis is entailed by a premise.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Any

from loguru import logger


class NLILabel(str, Enum):
    """NLI prediction labels."""

    ENTAILMENT = "entailment"
    CONTRADICTION = "contradiction"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class NLIResult:
    """Result of an NLI evaluation.

    Attributes:
        label: The NLI prediction (entailment, contradiction, neutral).
        score: Confidence score for the prediction (0.0 to 1.0).
        entailed_score: Score specifically for entailment label.
    """

    label: NLILabel
    score: float
    entailed_score: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got {self.score}")
        if not 0.0 <= self.entailed_score <= 1.0:
            raise ValueError(
                f"Entailed score must be between 0.0 and 1.0, got {self.entailed_score}"
            )


class NLIJudge:
    """NLI-based judge using DeBERTa model for natural language inference.

    Uses a pretrained NLI model to determine whether a hypothesis is
    entailed by a premise. This provides more accurate scoring than
    word-overlap methods.

    Example:
        ```python
        judge = NLIJudge()
        result = judge.evaluate(
            premise="The sky is blue and clear today.",
            hypothesis="The sky is blue."
        )
        print(result.label)  # NLILabel.ENTAILMENT
        print(result.entailed_score)  # 0.98
        ```
    """

    DEFAULT_MODEL = "microsoft/deberta-v3-base-mnli"

    def __init__(self, model_name: str | None = None) -> None:
        """Initialize the NLI judge.

        Args:
            model_name: HuggingFace model name. Defaults to DeBERTa MNLI.
        """
        self._model_name = model_name or self.DEFAULT_MODEL
        self._pipeline: Any = None

    @property
    def pipeline(self) -> Any:
        """Lazily load the NLI pipeline (heavy import)."""
        if self._pipeline is None:
            logger.debug("Loading NLI model: {}", self._model_name)
            from transformers import pipeline as hf_pipeline

            self._pipeline = hf_pipeline(
                "text-classification",
                model=self._model_name,
                top_k=None,
                device=-1,  # CPU; use 0 for GPU if available
            )
            logger.debug("NLI model loaded successfully")
        return self._pipeline

    def evaluate(self, premise: str, hypothesis: str) -> NLIResult:
        """Evaluate NLI between premise and hypothesis.

        Args:
            premise: The context/premise text.
            hypothesis: The claim/hypothesis to verify.

        Returns:
            NLIResult with label, score, and entailed_score.
        """
        if not premise.strip() or not hypothesis.strip():
            return NLIResult(
                label=NLILabel.NEUTRAL,
                score=1.0,
                entailed_score=0.0,
            )

        inputs = f"{premise} [SEP] {hypothesis}"
        predictions = self.pipeline(inputs)

        # predictions is a list of dicts: [{"label": "entailment", "score": 0.99}, ...]
        score_map = {
            pred["label"].lower(): pred["score"]
            for pred in predictions[0]
        }

        entailed_score = score_map.get("entailment", 0.0)
        contradiction_score = score_map.get("contradiction", 0.0)
        neutral_score = score_map.get("neutral", 0.0)

        # Determine winning label
        scores = {
            NLILabel.ENTAILMENT: entailed_score,
            NLILabel.CONTRADICTION: contradiction_score,
            NLILabel.NEUTRAL: neutral_score,
        }
        winning_label = max(scores, key=scores.get)  # type: ignore[arg-type]
        winning_score = scores[winning_label]

        return NLIResult(
            label=winning_label,
            score=winning_score,
            entailed_score=entailed_score,
        )

    def batch_evaluate(
        self, pairs: list[tuple[str, str]]
    ) -> list[NLIResult]:
        """Evaluate multiple premise-hypothesis pairs.

        Args:
            pairs: List of (premise, hypothesis) tuples.

        Returns:
            List of NLIResult, one per pair.
        """
        return [self.evaluate(premise, hyp) for premise, hyp in pairs]


@lru_cache(maxsize=1)
def get_default_judge() -> NLIJudge:
    """Get a cached default NLI judge instance.

    Returns:
        Cached NLIJudge instance.
    """
    return NLIJudge()
