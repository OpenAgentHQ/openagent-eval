"""Report generation for OpenAgent Eval.

This package provides multiple report formats for evaluation results:
- Terminal (Rich): Styled console output
- Markdown: Structured .md files
- HTML: Styled web pages via Jinja2
- JSON: Machine-readable structured data
- EvalPort: Portable ResultSet JSON (https://github.com/adhabnr-ux/evalport)
- Comparison: Side-by-side experiment comparison
"""

from openagent_eval.reports.base import (
    ExperimentComparison,
    FailureInfo,
    ReportConfig,
    ReportGenerator,
    ReportInput,
)
from openagent_eval.reports.comparison import ComparisonReport
from openagent_eval.reports.evalport import EvalPortReport
from openagent_eval.reports.html import HTMLReport
from openagent_eval.reports.json_report import JSONReport
from openagent_eval.reports.markdown import MarkdownReport
from openagent_eval.reports.terminal import TerminalReport

__all__ = [
    "ReportGenerator",
    "ReportConfig",
    "ReportInput",
    "FailureInfo",
    "ExperimentComparison",
    "TerminalReport",
    "MarkdownReport",
    "HTMLReport",
    "JSONReport",
    "EvalPortReport",
    "ComparisonReport",
]
