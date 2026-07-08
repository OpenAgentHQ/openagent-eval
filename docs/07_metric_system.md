# Metric System

## Overview

OpenAgent Eval provides a comprehensive metric system for evaluating RAG pipelines. All metrics implement the `BaseMetric` interface and return `MetricResult` objects.

---

## Base Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class MetricResult:
    """Result of a metric evaluation."""
    score: float
    reason: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BaseMetric(ABC):
    """Base class for all evaluation metrics."""
    
    name: str
    description: str
    
    @abstractmethod
    def evaluate(self, **kwargs) -> MetricResult:
        """Evaluate the metric and return a result."""
        ...
```

---

## Retrieval Metrics

### Context Precision

Measures the proportion of retrieved documents that are relevant.

```python
class ContextPrecision(BaseMetric):
    name = "context_precision"
    description = "Proportion of retrieved documents that are relevant"
    
    def evaluate(self, retrieved_docs: List[Document], 
                 ground_truth: str) -> MetricResult:
        relevant_count = sum(1 for doc in retrieved_docs 
                          if doc.is_relevant(ground_truth))
        score = relevant_count / len(retrieved_docs) if retrieved_docs else 0.0
        return MetricResult(score=score, reason=f"{relevant_count}/{len(retrieved_docs)} relevant")
```

### Context Recall

Measures how many relevant documents were retrieved.

```python
class ContextRecall(BaseMetric):
    name = "context_recall"
    description = "Proportion of relevant documents that were retrieved"
    
    def evaluate(self, retrieved_docs: List[Document],
                 all_relevant_docs: List[Document]) -> MetricResult:
        retrieved_set = {doc.id for doc in retrieved_docs}
        relevant_set = {doc.id for doc in all_relevant_docs}
        recalled = len(retrieved_set & relevant_set)
        score = recalled / len(relevant_set) if relevant_set else 0.0
        return MetricResult(score=score, reason=f"{recalled}/{len(relevant_set)} recalled")
```

### Hit Rate

Measures whether at least one relevant document was retrieved.

```python
class HitRate(BaseMetric):
    name = "hit_rate"
    description = "Whether at least one relevant document was retrieved"
    
    def evaluate(self, retrieved_docs: List[Document],
                 ground_truth: str) -> MetricResult:
        hit = any(doc.is_relevant(ground_truth) for doc in retrieved_docs)
        return MetricResult(score=1.0 if hit else 0.0, 
                          reason="Hit" if hit else "Miss")
```

### Mean Reciprocal Rank (MRR)

Measures the rank of the first relevant document.

```python
class MRR(BaseMetric):
    name = "mrr"
    description = "Mean reciprocal rank of first relevant document"
    
    def evaluate(self, retrieved_docs: List[Document],
                 ground_truth: str) -> MetricResult:
        for i, doc in enumerate(retrieved_docs):
            if doc.is_relevant(ground_truth):
                score = 1.0 / (i + 1)
                return MetricResult(score=score, 
                                  reason=f"First relevant at rank {i+1}")
        return MetricResult(score=0.0, reason="No relevant documents found")
```

### NDCG

Normalized Discounted Cumulative Gain - measures ranking quality.

```python
class NDCG(BaseMetric):
    name = "ndcg"
    description = "Normalized Discounted Cumulative Gain"
    
    def evaluate(self, retrieved_docs: List[Document],
                 ground_truth: str, k: int = 10) -> MetricResult:
        # Calculate DCG
        dcg = sum(
            (1.0 if doc.is_relevant(ground_truth) else 0.0) / np.log2(i + 2)
            for i, doc in enumerate(retrieved_docs[:k])
        )
        
        # Calculate ideal DCG
        ideal_hits = min(sum(1 for doc in retrieved_docs 
                        if doc.is_relevant(ground_truth)), k)
        idcg = sum(1.0 / np.log2(i + 2) for i in range(ideal_hits))
        
        score = dcg / idcg if idcg > 0 else 0.0
        return MetricResult(score=score, reason=f"NDCG@{k}")
```

---

## Generation Metrics

### Faithfulness

Measures whether the answer is faithful to the retrieved context.

```python
class Faithfulness(BaseMetric):
    name = "faithfulness"
    description = "Whether the answer is faithful to the context"
    
    def evaluate(self, answer: str, context: str) -> MetricResult:
        # Uses LLM to evaluate faithfulness
        prompt = f"""Evaluate if the answer is faithful to the context.
        
Context: {context}
Answer: {answer}

Is the answer faithful? (yes/no)
"""
        result = self.llm.generate(prompt)
        score = 1.0 if "yes" in result.lower() else 0.0
        return MetricResult(score=score, reason="Faithful" if score else "Unfaithful")
```

### Answer Relevancy

Measures whether the answer addresses the question.

```python
class AnswerRelevancy(BaseMetric):
    name = "answer_relevancy"
    description = "Whether the answer addresses the question"
    
    def evaluate(self, question: str, answer: str) -> MetricResult:
        prompt = f"""Evaluate if the answer addresses the question.
        
Question: {question}
Answer: {answer}

Rate relevancy (0-1):
"""
        result = self.llm.generate(prompt)
        score = float(result)
        return MetricResult(score=score, reason=f"Relevancy: {score:.2f}")
```

### Hallucination Detection

Measures whether the answer contains information not in the context.

```python
class HallucinationDetection(BaseMetric):
    name = "hallucination"
    description = "Whether the answer contains hallucinated information"
    
    def evaluate(self, answer: str, context: str) -> MetricResult:
        prompt = f"""Identify any information in the answer that is not supported by the context.

Context: {context}
Answer: {answer}

List any hallucinated claims (or "none"):
"""
        result = self.llm.generate(prompt)
        hallucinated = result.lower() != "none"
        score = 0.0 if hallucinated else 1.0
        return MetricResult(score=score, 
                          reason="No hallucination" if score else "Hallucination detected")
```

### Semantic Similarity

Measures semantic similarity between answer and ground truth.

```python
class SemanticSimilarity(BaseMetric):
    name = "semantic_similarity"
    description = "Semantic similarity between answer and ground truth"
    
    def evaluate(self, answer: str, ground_truth: str) -> MetricResult:
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode([answer, ground_truth])
        
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return MetricResult(score=float(similarity), 
                          reason=f"Similarity: {similarity:.3f}")
```

---

## Classic Metrics

### Exact Match

```python
class ExactMatch(BaseMetric):
    name = "exact_match"
    description = "Whether answer exactly matches ground truth"
    
    def evaluate(self, answer: str, ground_truth: str) -> MetricResult:
        match = answer.strip().lower() == ground_truth.strip().lower()
        return MetricResult(score=1.0 if match else 0.0, 
                          reason="Exact match" if match else "No match")
```

### F1 Score

```python
class F1Score(BaseMetric):
    name = "f1_score"
    description = "Token-level F1 score"
    
    def evaluate(self, answer: str, ground_truth: str) -> MetricResult:
        answer_tokens = set(answer.lower().split())
        ground_truth_tokens = set(ground_truth.lower().split())
        
        if not answer_tokens or not ground_truth_tokens:
            return MetricResult(score=0.0, reason="Empty input")
        
        common = answer_tokens & ground_truth_tokens
        precision = len(common) / len(answer_tokens)
        recall = len(common) / len(ground_truth_tokens)
        
        if precision + recall == 0:
            score = 0.0
        else:
            score = 2 * (precision * recall) / (precision + recall)
        
        return MetricResult(score=score, reason=f"P={precision:.2f}, R={recall:.2f}")
```

### BLEU

```python
class BLEU(BaseMetric):
    name = "bleu"
    description = "BLEU score for text generation"
    
    def evaluate(self, answer: str, ground_truth: str) -> MetricResult:
        from evaluate import load
        
        bleu = load("bleu")
        result = bleu.compute(predictions=[answer], references=[[ground_truth]])
        score = result["bleu"]
        return MetricResult(score=score, reason=f"BLEU: {score:.4f}")
```

### ROUGE

```python
class ROUGE(BaseMetric):
    name = "rouge"
    description = "ROUGE score for text generation"
    
    def evaluate(self, answer: str, ground_truth: str) -> MetricResult:
        from evaluate import load
        
        rouge = load("rouge")
        result = rouge.compute(predictions=[answer], references=[ground_truth])
        score = result["rougeL"]
        return MetricResult(score=score, reason=f"ROUGE-L: {score:.4f}")
```

---

## Performance Metrics

### Latency

```python
class LatencyMetric(BaseMetric):
    name = "latency"
    description = "Execution time in milliseconds"
    
    def evaluate(self, start_time: float, end_time: float) -> MetricResult:
        latency_ms = (end_time - start_time) * 1000
        return MetricResult(score=latency_ms, 
                          reason=f"{latency_ms:.0f}ms",
                          metadata={"unit": "milliseconds"})
```

---

## Cost Metrics

### Token Usage

```python
class TokenUsage(BaseMetric):
    name = "token_usage"
    description = "Token usage and estimated cost"
    
    def evaluate(self, prompt_tokens: int, completion_tokens: int,
                 cost_per_1k_input: float, cost_per_1k_output: float) -> MetricResult:
        total_tokens = prompt_tokens + completion_tokens
        cost = (prompt_tokens / 1000 * cost_per_1k_input + 
                completion_tokens / 1000 * cost_per_1k_output)
        
        return MetricResult(
            score=cost,
            reason=f"{total_tokens} tokens, ${cost:.4f}",
            metadata={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
        )
```

---

## Custom Metrics

Users can create custom metrics by implementing `BaseMetric`:

```python
from openagent_eval.metrics import BaseMetric, MetricResult

class MyCustomMetric(BaseMetric):
    name = "my_custom_metric"
    description = "A custom evaluation metric"
    
    def evaluate(self, answer: str, context: str, **kwargs) -> MetricResult:
        # Your custom logic here
        score = calculate_my_score(answer, context)
        return MetricResult(
            score=score,
            reason=f"Custom score: {score:.2f}",
            metadata={"custom_field": "value"}
        )
```

Register via entry points:

```toml
# pyproject.toml
[project.entry-points."openagent_eval.metrics"]
my_metric = "my_package.metrics:MyCustomMetric"
```
