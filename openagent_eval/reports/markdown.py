"""Markdown report generator.

This module provides a Markdown-formatted report that renders evaluation
results as a structured .md file with tables, headers, and sections.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openagent_eval.reports.base import ReportGenerator


class MarkdownReport(ReportGenerator):
    """Generate Markdown-formatted evaluation reports.

    Produces a structured .md file with:
    - Title and metadata
    - Summary section with key statistics
    - Metrics table
    - Error analysis
    - Example evaluations
    - Configuration details
    """

    def generate(self, report: Any) -> str:
        """Generate a Markdown report string.

        Args:
            report: EvaluationReport containing config, results, and summary.

        Returns:
            Markdown-formatted report string.
        """
        result = report.result
        summary = report.summary
        config = report.config
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        sections: list[str] = []

        # Title
        sections.append(f"# {report.metadata.get('title', 'OpenAgent Eval Report')}")
        sections.append("")
        sections.append(f"*Generated on {now}*")
        sections.append("")

        # Summary
        sections.append("## Summary")
        sections.append("")
        sections.append("| Metric | Value |")
        sections.append("|--------|-------|")
        sections.append(f"| Total Items | {summary.get('total_items', 0)} |")
        sections.append(
            f"| Successful | {summary.get('successful_evaluations', 0)} |"
        )
        sections.append(f"| Failed | {summary.get('failed_evaluations', 0)} |")
        sections.append("")

        # Metrics
        metrics = summary.get("metrics_summary", {})
        if metrics:
            sections.append("## Metrics")
            sections.append("")
            sections.append("| Metric | Average Score |")
            sections.append("|--------|---------------|")
            for metric_name, avg_score in sorted(metrics.items()):
                # Add visual indicator
                if avg_score >= 0.8:
                    indicator = "🟢"
                elif avg_score >= 0.5:
                    indicator = "🟡"
                else:
                    indicator = "🔴"
                sections.append(
                    f"| {metric_name} | {indicator} {avg_score:.4f} |"
                )
            sections.append("")

            # Overall score
            if metrics:
                overall = sum(metrics.values()) / len(metrics)
                sections.append(f"**Overall Average Score: {overall:.4f}**")
                sections.append("")

        # Error Analysis
        if result.errors:
            sections.append("## Error Analysis")
            sections.append("")
            sections.append("| Error Type | Count |")
            sections.append("|------------|-------|")
            error_types: dict[str, int] = {}
            for err in result.errors:
                err_type = err.get("error_type", "Unknown")
                error_types[err_type] = error_types.get(err_type, 0) + 1
            for err_type, count in sorted(error_types.items()):
                sections.append(f"| {err_type} | {count} |")
            sections.append("")

            # Error details
            sections.append("### Error Details")
            sections.append("")
            for i, err in enumerate(result.errors[:config.report.max_examples], 1):
                sections.append(f"{i}. **{err.get('error_type', 'Unknown')}**: {err.get('error', 'No message')}")
            sections.append("")

        # Example Results
        if result.results:
            sections.append("## Sample Results")
            sections.append("")
            max_examples = min(len(result.results), config.report.max_examples)
            for i, eval_result in enumerate(result.results[:max_examples], 1):
                sections.append(f"### Result {i}")
                sections.append("")
                sections.append(f"**Question:** {eval_result.question}")
                sections.append("")
                if eval_result.answer:
                    sections.append(f"**Answer:** {eval_result.answer}")
                    sections.append("")
                if eval_result.ground_truth:
                    sections.append(f"**Ground Truth:** {eval_result.ground_truth}")
                    sections.append("")
                if eval_result.metrics:
                    sections.append("**Scores:**")
                    sections.append("")
                    for metric_name, score in eval_result.metrics.items():
                        sections.append(f"- {metric_name}: {score:.4f}")
                    sections.append("")
                if eval_result.contexts:
                    sections.append("<details>")
                    sections.append("<summary>Contexts</summary>")
                    sections.append("")
                    for ctx in eval_result.contexts:
                        sections.append(f"> {ctx[:200]}{'...' if len(ctx) > 200 else ''}")
                        sections.append("")
                    sections.append("</details>")
                    sections.append("")

        # Configuration
        sections.append("## Configuration")
        sections.append("")
        sections.append("```yaml")
        sections.append(f"dataset:")
        sections.append(f"  path: {config.dataset.path}")
        if config.dataset.format:
            sections.append(f"  format: {config.dataset.format}")
        sections.append(f"llm:")
        sections.append(f"  provider: {config.llm.provider}")
        sections.append(f"  model: {config.llm.model}")
        sections.append(f"retriever:")
        sections.append(f"  provider: {config.retriever.provider}")
        sections.append(f"report:")
        sections.append(f"  output: {config.report.output.value}")
        sections.append(f"  output_dir: {config.report.output_dir}")
        sections.append("```")
        sections.append("")

        # Footer
        sections.append("---")
        sections.append("")
        sections.append(
            f"*Report generated by [OpenAgent Eval](https://github.com/OpenAgentHQ/openagent-eval) v{report.metadata.get('version', '0.1.0')}*"
        )

        return "\n".join(sections)

    def generate_to_file(self, report: Any, output_path: Path | str) -> Path:
        """Generate Markdown report and write to file.

        Args:
            report: EvaluationReport containing config, results, and summary.
            output_path: Path to write the report file.

        Returns:
            Path to the written file.
        """
        path = Path(output_path)
        if path.suffix == "":
            path = path / "report.md"
        elif path.suffix.lower() != ".md":
            path = path.with_suffix(".md")
        path = self._prepare_output_file(path)
        content = self.generate(report)
        path.write_text(content, encoding="utf-8")
        return path
