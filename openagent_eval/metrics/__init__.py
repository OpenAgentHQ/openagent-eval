"""Evaluation metrics for OpenAgent Eval.

This package provides all evaluation metrics organized by category:
- Retrieval metrics: Context precision, recall, MRR, NDCG, etc.
- Generation metrics: Faithfulness, relevancy, hallucination, BLEU, ROUGE, etc.
- Performance metrics: Latency tracking
- Cost metrics: Token counting and cost estimation

All metrics implement the BaseMetric interface and return MetricResult.
"""

from openagent_eval.metrics.base import BaseMetric, MetricResult
from openagent_eval.metrics.cost import TokenCountMetric
from openagent_eval.metrics.generation import (
    AnswerRelevancy,
    BERTScore,
    BLEU,
    ExactMatch,
    F1Score,
    Faithfulness,
    HallucinationDetection,
    ROUGE,
    SemanticSimilarity,
)
from openagent_eval.metrics.performance import LatencyMetric
from openagent_eval.metrics.retrieval import (
    ContextPrecision,
    ContextRecall,
    HitRate,
    MRR,
    NDCG,
    PrecisionAtK,
    RecallAtK,
)

__all__ = [
    # Base
    "BaseMetric",
    "MetricResult",
    # Retrieval
    "ContextPrecision",
    "ContextRecall",
    "HitRate",
    "MRR",
    "NDCG",
    "PrecisionAtK",
    "RecallAtK",
    # Generation
    "AnswerRelevancy",
    "BERTScore",
    "BLEU",
    "ExactMatch",
    "F1Score",
    "Faithfulness",
    "HallucinationDetection",
    "ROUGE",
    "SemanticSimilarity",
    # Performance
    "LatencyMetric",
    # Cost
    "TokenCountMetric",
]

# Metric registry for dynamic lookup
METRIC_REGISTRY: dict[str, type[BaseMetric]] = {
    "context_precision": ContextPrecision,
    "context_recall": ContextRecall,
    "recall_at_k": RecallAtK,
    "precision_at_k": PrecisionAtK,
    "hit_rate": HitRate,
    "mrr": MRR,
    "ndcg": NDCG,
    "faithfulness": Faithfulness,
    "answer_relevancy": AnswerRelevancy,
    "hallucination": HallucinationDetection,
    "semantic_similarity": SemanticSimilarity,
    "exact_match": ExactMatch,
    "f1_score": F1Score,
    "bleu": BLEU,
    "rouge": ROUGE,
    "bertscore": BERTScore,
    "latency": LatencyMetric,
    "token_count": TokenCountMetric,
}


def get_metric(name: str) -> type[BaseMetric]:
    """Get a metric class by name.

    Args:
        name: The metric name.

    Returns:
        The metric class.

    Raises:
        KeyError: If metric not found.
    """
    if name not in METRIC_REGISTRY:
        available = ", ".join(sorted(METRIC_REGISTRY.keys()))
        raise KeyError(
            f"Metric '{name}' not found. Available metrics: {available}"
        )
    return METRIC_REGISTRY[name]


def list_metrics() -> list[str]:
    """List all available metric names.

    Returns:
        Sorted list of metric names.
    """
    return sorted(METRIC_REGISTRY.keys())
