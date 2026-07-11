"""Evidence finder for matching claims to supporting context.

Uses NLI scoring to find the best supporting evidence for each claim,
enabling more accurate faithfulness evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass

from openagent_eval.metrics.nli.claim_extractor import Claim
from openagent_eval.metrics.nli.judge import NLIJudge, NLIResult, get_default_judge


@dataclass(frozen=True)
class EvidenceMatch:
    """A claim matched with its best supporting evidence.

    Attributes:
        claim: The extracted claim.
        evidence: The best matching context snippet.
        nli_result: NLI evaluation result for the pair.
        all_scores: NLI scores for all contexts tried.
    """

    claim: Claim
    evidence: str
    nli_result: NLIResult
    all_scores: tuple[NLIResult, ...]


class EvidenceFinder:
    """Find supporting evidence for claims using NLI scoring.

    For each claim, evaluates it against all available contexts using
    NLI and returns the best matching evidence.

    Example:
        ```python
        finder = EvidenceFinder()
        matches = finder.find_evidence(
            claim=Claim(text="Python was created in 1991", index=0),
            contexts=[
                "Python is a programming language.",
                "Python was created by Guido van Rossum in 1991.",
            ]
        )
        print(matches.evidence)  # "Python was created by Guido van Rossum in 1991."
        print(matches.nli_result.label)  # NLILabel.ENTAILMENT
        ```
    """

    def __init__(self, judge: NLIJudge | None = None) -> None:
        """Initialize the evidence finder.

        Args:
            judge: NLI judge instance. Uses default if None.
        """
        self._judge = judge or get_default_judge()

    def find_evidence(
        self, claim: Claim, contexts: list[str]
    ) -> EvidenceMatch | None:
        """Find the best supporting evidence for a claim.

        Args:
            claim: The claim to find evidence for.
            contexts: List of context strings to search.

        Returns:
            EvidenceMatch with best evidence, or None if no contexts.
        """
        if not contexts:
            return None

        results: list[NLIResult] = []
        for ctx in contexts:
            result = self._judge.evaluate(premise=ctx, hypothesis=claim.text)
            results.append(result)

        # Find the context with highest entailment score
        best_idx = max(range(len(results)), key=lambda i: results[i].entailed_score)

        return EvidenceMatch(
            claim=claim,
            evidence=contexts[best_idx],
            nli_result=results[best_idx],
            all_scores=tuple(results),
        )

    def find_evidence_batch(
        self, claims: list[Claim], contexts: list[str]
    ) -> list[EvidenceMatch | None]:
        """Find evidence for multiple claims.

        Args:
            claims: List of claims to find evidence for.
            contexts: List of context strings to search.

        Returns:
            List of EvidenceMatch (or None for empty contexts).
        """
        return [self.find_evidence(claim, contexts) for claim in claims]

    def score_faithfulness(
        self, claims: list[Claim], contexts: list[str], threshold: float = 0.5
    ) -> tuple[float, list[EvidenceMatch | None]]:
        """Score faithfulness as fraction of claims with supporting evidence.

        Args:
            claims: List of extracted claims.
            contexts: List of context strings.
            threshold: Minimum entailment score to consider a claim supported.

        Returns:
            Tuple of (faithfulness_score, list_of_matches).
        """
        if not claims:
            return 0.0, []

        matches = self.find_evidence_batch(claims, contexts)
        supported = sum(
            1 for m in matches
            if m is not None and m.nli_result.entailed_score >= threshold
        )

        score = supported / len(claims)
        return score, matches
