"""Corpus Health Auditor module.

Scans knowledge bases before connecting to RAG to detect issues
that no existing evaluation tool can see — contradictions, staleness,
duplicates, and thematic coverage gaps.
"""

from openagent_eval.corpus.auditor import CorpusAuditor
from openagent_eval.corpus.base import BaseCorpusAnalyzer
from openagent_eval.corpus.contradiction import ContradictionDetector
from openagent_eval.corpus.coverage import CoverageAnalyzer
from openagent_eval.corpus.duplicates import DuplicateDetector
from openagent_eval.corpus.models import (
    AuditReport,
    CorpusIssue,
    IssueSeverity,
    IssueType,
)
from openagent_eval.corpus.staleness import StalenessDetector

__all__ = [
    "BaseCorpusAnalyzer",
    "ContradictionDetector",
    "CoverageAnalyzer",
    "DuplicateDetector",
    "StalenessDetector",
    "CorpusAuditor",
    "CorpusIssue",
    "AuditReport",
    "IssueType",
    "IssueSeverity",
]
