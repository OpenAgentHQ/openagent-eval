"""NLI-based scoring module for OpenAgent Eval.

Provides Natural Language Inference (NLI) based metrics for more accurate
faithfulness and relevancy scoring. Uses DeBERTa NLI model to determine
whether claims are entailed by context, replacing simple word-overlap.

Components:
- NLIJudge: Core NLI scoring using DeBERTa model
- ClaimExtractor: Split answers into atomic claims
- EvidenceFinder: Match claims to supporting context via NLI

Example:
    ```python
    from openagent_eval.metrics.nli import NLIJudge, ClaimExtractor, EvidenceFinder

    # Direct NLI scoring
    judge = NLIJudge()
    result = judge.evaluate(
        premise="The sky is blue.",
        hypothesis="The sky is blue and clear."
    )

    # Extract claims and find evidence
    extractor = ClaimExtractor()
    claims = extractor.extract("Python was created in 1991. It is open source.")

    finder = EvidenceFinder(judge)
    score, matches = finder.score_faithfulness(claims, contexts)
    ```
"""

from openagent_eval.metrics.nli.claim_extractor import Claim, ClaimExtractor
from openagent_eval.metrics.nli.evidence_finder import EvidenceFinder, EvidenceMatch
from openagent_eval.metrics.nli.judge import NLIJudge, NLIResult, NLILabel

__all__ = [
    "Claim",
    "ClaimExtractor",
    "EvidenceFinder",
    "EvidenceMatch",
    "NLIJudge",
    "NLIResult",
    "NLILabel",
]
