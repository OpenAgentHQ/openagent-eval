"""Claim extractor for splitting answers into atomic claims.

Extracts individual factual claims from a generated answer so each
can be independently verified against context using NLI.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Claim:
    """An atomic factual claim extracted from an answer.

    Attributes:
        text: The claim text.
        index: Position of the claim in the original answer.
    """

    text: str
    index: int


class ClaimExtractor:
    """Extracts atomic claims from generated answers.

    Splits an answer into individual factual statements that can each
    be independently verified against context using NLI scoring.

    Example:
        ```python
        extractor = ClaimExtractor()
        claims = extractor.extract(
            "Python was created by Guido van Rossum. It was released in 1991."
        )
        # [Claim(text="Python was created by Guido van Rossum", index=0),
        #  Claim(text="It was released in 1991", index=1)]
        ```
    """

    # Sentence-ending patterns
    _SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')

    def extract(self, answer: str) -> list[Claim]:
        """Extract atomic claims from an answer.

        Args:
            answer: The generated answer text.

        Returns:
            List of Claim objects, one per extracted claim.
        """
        if not answer or not answer.strip():
            return []

        # Split into sentences
        sentences = self._split_sentences(answer)

        # Further split compound sentences
        claims: list[Claim] = []
        for sentence in sentences:
            sub_claims = self._split_compound(sentence)
            for sub_claim in sub_claims:
                cleaned = self._clean_claim(sub_claim)
                if cleaned:
                    claims.append(Claim(text=cleaned, index=len(claims)))

        return claims

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        sentences = self._SENTENCE_SPLIT.split(text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def _split_compound(self, sentence: str) -> list[str]:
        """Split compound sentences into simpler claims.

        Handles conjunctions like 'and', 'but', 'also'.
        """
        # Split on coordinating conjunctions preceded by comma
        parts = re.split(r',\s*(?:and|but|also|moreover|furthermore|however)\s+', sentence, flags=re.IGNORECASE)

        # If no split happened, try splitting on semicolons
        if len(parts) == 1:
            parts = re.split(r';\s*', sentence)

        return parts if len(parts) > 1 else [sentence]

    def _clean_claim(self, text: str) -> str:
        """Clean and normalize a claim string."""
        text = text.strip()
        # Remove leading/trailing punctuation
        text = text.strip('.,;:!?')
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text

    def extract_with_context(
        self, answer: str, contexts: list[str]
    ) -> list[tuple[Claim, str]]:
        """Extract claims and pair each with the most relevant context.

        Uses simple keyword overlap to find the best matching context
        for each claim. For NLI-based matching, use EvidenceFinder.

        Args:
            answer: The generated answer text.
            contexts: List of context strings.

        Returns:
            List of (Claim, best_matching_context) tuples.
        """
        claims = self.extract(answer)
        if not contexts:
            return [(claim, "") for claim in claims]

        paired: list[tuple[Claim, str]] = []
        for claim in claims:
            best_ctx = self._find_best_context(claim.text, contexts)
            paired.append((claim, best_ctx))

        return paired

    def _find_best_context(self, claim: str, contexts: list[str]) -> str:
        """Find the context with highest keyword overlap to the claim."""
        claim_words = set(claim.lower().split())
        best_score = -1
        best_ctx = contexts[0] if contexts else ""

        for ctx in contexts:
            ctx_words = set(ctx.lower().split())
            overlap = len(claim_words & ctx_words)
            if overlap > best_score:
                best_score = overlap
                best_ctx = ctx

        return best_ctx
