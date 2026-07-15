"""Experiment comparison report generator.

This module provides comparison reporting for evaluating changes between
two experiment runs, showing metric deltas and statistical significance.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openagent_eval.reports.base import ExperimentComparison, ReportGenerator


class ComparisonReport(ReportGenerator):
    """Generate side-by-side experiment comparison reports.

    Compares two PipelineResult objects and shows:
    - Per-metric deltas (improvement/regression)
    - Overall score comparison
    - Statistical summary
    - Winner determination
    """

    def generate(self, report: Any) -> str:
        """Generate a comparison report string.

        Note: ``report`` should be an ExperimentComparison object.

        Args:
            report: ExperimentComparison with baseline and experiment results.

        Returns:
            Formatted comparison report string.
        """
        if not isinstance(report, ExperimentComparison):
            raise TypeError(
                f"ComparisonReport requires ExperimentComparison, got {type(report).__name__}"
            )

        lines: list[str] = []
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Header
        lines.append("=" * 60)
        lines.append("  Experiment Comparison Report")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"  Generated: {now}")
        lines.append(f"  Baseline:  {report.baseline_name}")
        lines.append(f"  Experiment: {report.experiment_name}")
        lines.append("")

        # Compute metric averages for both
        baseline_metrics = self._extract_metric_averages(report.baseline_results)
        experiment_metrics = self._extract_metric_averages(report.experiment_results)

        # All metric names
        all_metrics = sorted(set(baseline_metrics) | set(experiment_metrics))

        if all_metrics:
            # Metrics comparison table
            lines.append("METRIC COMPARISON")
            lines.append("-" * 60)
            lines.append(
                f"  {'Metric':<30} {'Baseline':>10} {'Experiment':>10} {'Delta':>10}"
            )
            lines.append("  " + "-" * 58)

            improved = 0
            regressed = 0
            for metric_name in all_metrics:
                base_val = baseline_metrics.get(metric_name, 0.0)
                exp_val = experiment_metrics.get(metric_name, 0.0)
                delta = exp_val - base_val

                if delta > 0.001:
                    indicator = "+"
                    improved += 1
                elif delta < -0.001:
                    indicator = ""
                    regressed += 1
                else:
                    indicator = "="

                lines.append(
                    f"  {metric_name:<30} {base_val:>10.4f} {exp_val:>10.4f} "
                    f"{indicator}{delta:>+9.4f}"
                )

            lines.append("")

            # Summary
            lines.append("SUMMARY")
            lines.append("-" * 60)
            lines.append(f"  Metrics improved:  {improved}")
            lines.append(f"  Metrics regressed: {regressed}")
            lines.append(f"  Metrics unchanged: {len(all_metrics) - improved - regressed}")
            lines.append("")

            # Overall scores (common metrics only for fair comparison)
            if baseline_metrics and experiment_metrics:
                common_metrics = sorted(
                    set(baseline_metrics) & set(experiment_metrics)
                )
                if common_metrics:
                    base_overall = (
                        sum(baseline_metrics[m] for m in common_metrics)
                        / len(common_metrics)
                    )
                    exp_overall = (
                        sum(experiment_metrics[m] for m in common_metrics)
                        / len(common_metrics)
                    )
                    lines.append(f"  Baseline overall:    {base_overall:.4f}")
                    lines.append(f"  Experiment overall:  {exp_overall:.4f}")
                    overall_delta = exp_overall - base_overall
                    lines.append(f"  Overall delta:       {overall_delta:+.4f}")
                    lines.append("")

                    # Winner
                    if exp_overall > base_overall:
                        lines.append(f"  >> WINNER: {report.experiment_name}")
                    elif exp_overall < base_overall:
                        lines.append(f"  >> WINNER: {report.baseline_name}")
                    else:
                        lines.append("  >> TIE")
                else:
                    lines.append("  No common metrics to compare overall scores.")
                    lines.append("")
            elif baseline_metrics:
                lines.append(f"  Baseline overall:    {sum(baseline_metrics.values()) / len(baseline_metrics):.4f}")
                lines.append("")
            elif experiment_metrics:
                lines.append(f"  Experiment overall:  {sum(experiment_metrics.values()) / len(experiment_metrics):.4f}")
                lines.append("")
        else:
            lines.append("  No metrics available for comparison.")
            lines.append("")

        # Error comparison
        baseline_errors = len(report.baseline_results.errors)
        experiment_errors = len(report.experiment_results.errors)
        if baseline_errors or experiment_errors:
            lines.append("ERROR COMPARISON")
            lines.append("-" * 60)
            lines.append(f"  Baseline errors:  {baseline_errors}")
            lines.append(f"  Experiment errors: {experiment_errors}")
            lines.append("")

        # Result count comparison
        lines.append("RESULT COUNTS")
        lines.append("-" * 60)
        lines.append(
            f"  Baseline results:   {len(report.baseline_results.results)}"
        )
        lines.append(
            f"  Experiment results: {len(report.experiment_results.results)}"
        )
        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def generate_to_file(self, report: Any, output_path: Path | str) -> Path:
        """Generate comparison report and write to file.

        Args:
            report: ExperimentComparison with baseline and experiment results.
            output_path: Path to write the report file.

        Returns:
            Path to the written file.
        """
        path = self._ensure_output_dir(output_path)
        if not str(path).endswith(".txt"):
            path = path / "comparison.txt"
        content = self.generate(report)
        path.write_text(content, encoding="utf-8")
        return path
