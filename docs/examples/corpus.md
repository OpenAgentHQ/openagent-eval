# Corpus Health Auditor Tutorial

A Jupyter notebook tour of OpenAgent Eval's corpus, diagnosis and synthesis modules:

- Auditing a document corpus for **staleness**, **duplicates** and **coverage** gaps
- Detecting **contradictions** with an LLM-as-judge
- Combining the checks into a single corpus health report
- Diagnosing evaluation failures with `DiagnosisAnalyzer`
- Generating synthetic and adversarial test cases

**Download:** [`corpus_and_related_modules.ipynb`](https://github.com/OpenAgentHQ/openagent-eval/blob/main/examples/corpus_and_related_modules.ipynb)

### What you'll learn

| Section | Topic |
|---------|-------|
| 1–3 | Installation and preparing a sample corpus |
| 4 | Corpus health: staleness, duplicate, coverage and contradiction detectors |
| 5 | A combined corpus audit report |
| 6 | Failure diagnosis with `DiagnosisAnalyzer` |
| 7 | Synthetic and adversarial test-case generation |

### Prerequisites

```bash
pip install openagent-eval jupyter
```

The staleness, duplicate, coverage and diagnosis sections run fully offline. The
contradiction detector and the synthesis sections use an LLM-as-judge — set a
`GROQ_API_KEY` (a free key from [Groq](https://console.groq.com)) to run them; without
a key those cells are skipped.

### Quick start

```bash
cd examples/
jupyter notebook corpus_and_related_modules.ipynb
```
