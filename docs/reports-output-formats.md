# Reports

OpenAgent Eval provides robust reporting tools to visualize and analyze evaluation results. You can generate reports in multiple formats depending on your workflow, whether you are running quick checks in the terminal, documenting results on GitHub, embedding dashboards in custom web apps, or parsing data programmatically in CI/CD pipelines.

## Configuring Reports

Reports are configured under the `report` block of your `config.yaml`.

```yaml title="config.yaml"
report:
  output: terminal          # Default output format
  output_dir: ./reports     # Directory to store reports
  include_examples: true    # Include individual evaluation details
  max_examples: 10          # Limit the number of examples included
```

### Configuration Options

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `report.output` | `str` | `terminal` | Default format: `terminal`, `markdown`, `html`, or `json`. |
| `report.output_dir` | `str` | `./reports` | Location where evaluation runs are serialized. |
| `report.include_examples` | `bool` | `true` | Include individual test cases and outputs. |
| `report.max_examples` | `int` | `10` | Maximum number of examples to include in the output. |

---

## 1. Terminal Report

The **Terminal Report** (`TerminalReport`) is the default report format designed for quick visual inspection directly inside your terminal or CI environment. It renders a clean, styled layout featuring:

* **Summary statistics**: Total, successful, and failed evaluation counts.
* **Metrics summary**: Average scores per metric.
* **Error breakdown**: Aggregated counts of exception types.
* **Sample results**: Highlights the first few runs with color-coded score indicators.
* **Configuration snapshot**: Overview of the dataset, LLM provider/model, and output format used.

### Generation

To view a Terminal report from the CLI, run:

```bash
# View the most recent report in the terminal
oaeval report latest

# Or view a specific report by its ID
oaeval report ffeaa75f-9717-4502-92ee-4c91fdfb7e9c --output terminal
```

!!! tip "Rich Styling"
    When outputting to a TTY, OpenAgent Eval uses `rich` to color-code scores (e.g. green for $\ge 0.8$, yellow for $0.5 \le \text{score} < 0.8$, and red for $<0.5$).

### Sample Output

```text
OpenAgent Eval - Report Viewer
Report: latest

╭──────────────────────────── Evaluation Complete ─────────────────────────────╮
│ OpenAgent Eval Report                                                        │
╰──────────────────────────────────────────────────────────────────────────────╯
      Summary      
┌─────────────┬───┐
│ Total Items │ 5 │
│ Successful  │ 3 │
│ Failed      │ 2 │
└─────────────┴───┘
         Metrics         
┏━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Metric       ┃  Score ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━┩
│ precision    │ 0.8500 │
│ recall       │ 0.8433 │
│ faithfulness │ 0.8567 │
└──────────────┴────────┘
                     Sample Results                     
┏━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ # ┃ Question        ┃ Metrics                        ┃
┡━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1 │ What is Python? │ precision=0.95, recall=0.88... │
│ 2 │ What is RAG?    │ precision=0.82, recall=0.90... │
└───┴─────────────────┴────────────────────────────────┘
╭─────────────────────────────── Configuration ────────────────────────────────╮
│ Dataset: tests/sample_data/test_dataset.json                                 │
│ LLM: openai/gpt-4o                                                           │
│ Output: terminal                                                             │
╰──────────────────────────────────────────────────────────────────────────────╯

Report ID: ffeaa75f-9717-4502-92ee-4c91fdfb7e9c
```

---

## 2. Markdown Report

The **Markdown Report** (`MarkdownReport`) formats evaluation results into a structured `.md` file, making it perfect for version control, documentation sites, and GitHub Pull Requests. It renders tables, sections, collapsible context details, and emojis as visual status indicators.

### Generation

Generate the Markdown report by running:

```bash
# Generate markdown from the latest evaluation
oaeval report latest --output markdown

# Save to a file directly
oaeval report latest --output markdown > reports/evaluation_report.md
```

### Sample Output

```markdown
# OpenAgent Eval Report

*Generated on 2026-07-14 12:30:46 UTC*

## Summary

| Metric | Value |
|--------|-------|
| Total Items | 5 |
| Successful | 3 |
| Failed | 2 |

## Metrics

| Metric | Average Score |
|--------|---------------|
| faithfulness | 🟢 0.8567 |
| precision | 🟢 0.8500 |
| recall | 🟢 0.8433 |

**Overall Average Score: 0.8500**

## Error Analysis

| Error Type | Count |
|------------|-------|
| ProviderConnectionError | 1 |
| ProviderExecutionError | 1 |

### Error Details

1. **ProviderConnectionError**: Connection timeout
2. **ProviderExecutionError**: Invalid response format

## Sample Results

### Result 1

**Question:** What is Python?

**Ground Truth:** Python is a programming language.

**Scores:**

- precision: 0.9500
- recall: 0.8800
- faithfulness: 0.9200

<details>
<summary>Contexts</summary>

> Python is a high-level programming language.

</details>

## Configuration

```yaml
dataset:
  path: data/questions.json
llm:
  provider: openai
  model: gpt-4o
retriever:
  provider: chroma
report:
  output: terminal
  output_dir: ./reports
```

---

*Report generated by [OpenAgent Eval](https://github.com/OpenAgentHQ/openagent-eval) v0.1.0*
```

---

## 3. HTML Report

The **HTML Report** (`HTMLReport`) generates a standalone, interactive, responsive web page using a Jinja2 template. It is best suited for sharing rich visualizations with cross-functional teams.

### Features
* **Responsive Layout**: Designed for mobile, tablet, and desktop viewports.
* **Visual Score Badges**: Renders colored score pill badges depending on performance thresholds.
* **Failures Section**: Clearly displays API errors, network issues, or parsing exceptions.
* **Sample Result Cards**: Showcases individual evaluations with detailed questions and answers.

### Custom Templates
By default, the generator uses a built-in template at `openagent_eval/reports/templates/report.html`. However, you can provide a custom Jinja2 template when using the Python SDK:

```python
from pathlib import Path
from openagent_eval.reports.html import HTMLReport

# Instantiate the HTMLReport with a custom Jinja2 template
custom_generator = HTMLReport(template_path="templates/my_custom_report.html")

# Generate the report content
html_content = custom_generator.generate(report)
```

### Generation

```bash
# View html report in stdout
oaeval report latest --output html

# Persist to a file
oaeval report latest --output html > reports/index.html
```

### Visual Structure

```text
+---------------------------------------------------------+
|                  OpenAgent Eval Report                  |
|          Generated on 2026-07-14 12:31:11 UTC           |
+---------------------------------------------------------+
| SUMMARY                                                 |
| [ 5 ] Total Items   [ 3 ] Successful   [ 2 ] Failed     |
| [ 0.8500 ] Overall Score                                |
+---------------------------------------------------------+
| METRICS                                                 |
| Metric Name                    Average Score            |
| faithfulness                  [ 0.8567 ] (Green Badge)  |
| precision                     [ 0.8500 ] (Green Badge)  |
| recall                        [ 0.8433 ] (Green Badge)  |
+---------------------------------------------------------+
| ERROR ANALYSIS                                          |
| Error Type                     Count                    |
| ProviderConnectionError       [ 1 ] (Red Badge)         |
+---------------------------------------------------------+
| SAMPLE RESULTS                                          |
| Result #1: What is Python?                              |
| [ faithfulness: 0.9200 ] [ precision: 0.9500 ]          |
+---------------------------------------------------------+
```

---

## 4. JSON Report

The **JSON Report** (`JSONReport`) produces structured, machine-readable documents. This is the optimal format for feeding evaluation statistics into dashboards, parsing metrics in automated CI/CD gating scripts, or archiving raw results.

### Schema Structure

* **`metadata`**: Engine name, package version, run timestamp, and report title.
* **`summary`**: Statistics on total, successful, and failed evaluations, alongside metric averages.
* **`results`**: Array containing evaluated items: question, answer, ground truth, retrieved contexts, individual metric scores, and metadata.
* **`errors`**: List of all execution errors, detailing the failed item, exception type, and message.
* **`failure_analysis`**: Aggregate analysis counting total errors and breaking them down by class name.
* **`configuration`**: A snapshot of the run configurations (dataset, LLM settings, retriever).

### Generation

To retrieve a JSON report:

```bash
oaeval report latest --output json
```

### Sample Output

```json
{
  "metadata": {
    "engine": "openagent-eval",
    "version": "0.1.0",
    "timestamp": "2026-07-14T12:30:48.123456+00:00",
    "title": "OpenAgent Eval Report"
  },
  "summary": {
    "total_items": 5,
    "successful_evaluations": 3,
    "failed_evaluations": 2,
    "metrics_summary": {
      "precision": 0.8500,
      "recall": 0.8433,
      "faithfulness": 0.8567
    }
  },
  "results": [
    {
      "question": "What is Python?",
      "answer": "Python is a programming language.",
      "ground_truth": "Python is a high-level programming language.",
      "contexts": [
        "Python is a programming language created by Guido van Rossum."
      ],
      "metrics": {
        "precision": 0.95,
        "recall": 0.88,
        "faithfulness": 0.92
      },
      "metadata": {
        "id": 1
      }
    }
  ],
  "errors": [
    {
      "item": {
        "question": "Failed question"
      },
      "error": "Connection timeout",
      "error_type": "ProviderConnectionError"
    }
  ],
  "failure_analysis": {
    "total_errors": 2,
    "error_breakdown": {
      "ProviderConnectionError": 1,
      "ProviderExecutionError": 1
    }
  },
  "configuration": {
    "dataset": {
      "path": "data/questions.json",
      "format": null,
      "limit": null
    },
    "llm": {
      "provider": "openai",
      "model": "gpt-4o",
      "temperature": 0.0
    },
    "retriever": {
      "provider": "chroma",
      "settings": {}
    },
    "report": {
      "output": "terminal",
      "output_dir": "./reports"
    }
  }
}
```

---

## 5. Comparison Report

The **Comparison Report** (`ComparisonReport`) is a dedicated utility used to compare two experiments side by side. It calculates the delta for each shared metric, assesses whether the overall score went up or down, and declares a winner.

### Key Metrics Covered
* **Metric Deltas**: Displays the exact difference (`Experiment - Baseline`) for every evaluated metric.
* **Overall Score Comparison**: Aggregated averages across all metrics.
* **Winner Determination**: Evaluates which experiment achieved a higher overall score, highlighting `WINNER` or declaring a `TIE`.
* **Error Count Comparison**: Compares the number of failures between the two runs.

### Generation

Run the `compare` CLI command with two report IDs:

```bash
oaeval compare ffeaa75f-9717-4502-92ee-4c91fdfb7e9c fa0aef0a-ec68-4318-9d25-c841c6be2004
```

### Sample Output

```text
============================================================
  Experiment Comparison Report
============================================================

  Generated: 2026-07-14 17:58:00 UTC
  Baseline:  exp-gpt-3.5-turbo
  Experiment: exp-gpt-4o

METRIC COMPARISON
------------------------------------------------------------
  Metric                           Baseline Experiment      Delta
  ----------------------------------------------------------
  answer_relevancy                   0.8200     0.8800 +  +0.0600
  context_precision                  0.8500     0.8500 =  +0.0000
  faithfulness                       0.7800     0.9200 +  +0.1400
  latency                            1.2000     0.8500    -0.3500

SUMMARY
------------------------------------------------------------
  Metrics improved:  3
  Metrics regressed: 0
  Metrics unchanged: 1

  Baseline overall:    0.9125
  Experiment overall:  0.8750
  Overall delta:       -0.0375

  >> WINNER: exp-gpt-4o
RESULT COUNTS
------------------------------------------------------------
  Baseline results:   100
  Experiment results: 100

============================================================
```
