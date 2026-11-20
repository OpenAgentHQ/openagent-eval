---
name: Provider Request
about: Propose a new LLM, retriever, or embedder provider for OpenAgent Eval
title: "[PROVIDER] "
labels: enhancement, provider
assignees: ''
---

## Provider Details

- **Provider Name**: [e.g., Anthropic, Bedrock, Qdrant, Cohere]
- **Category**:
  - [ ] LLM (`providers/llm/`)
  - [ ] Retriever (`providers/retrievers/`)
  - [ ] Embedder (`providers/embedders/`)
- **Homepage / API Docs**: [URL to official SDK or API documentation]
- **Python SDK / Package**: [e.g., `anthropic>=0.40.0` (lazy optional dependency)]

## Authentication & Configuration Shape

Describe the environment variables and Pydantic config fields needed to initialize this provider:

```yaml
# Example configuration shape (redact any secrets)
provider:
  name: my-provider
  model: ...
  api_key_env: MY_PROVIDER_API_KEY
  base_url: https://...
```

## Capabilities & Interface Mapping

How should the provider map to the base interface (`LLMProvider`, `Retriever`, or `Embedder`)?

- **Async support**: [native async SDK / thread-wrapped sync client / REST via httpx]
- **Supported features**: [e.g., streaming, token counting, structured output / JSON mode, batching, hybrid search]
- **Rate limits / retry considerations**: [if applicable]

## Use Case

Describe the evaluation workflow or integration scenario that needs this provider.

## Would you be willing to contribute this provider?

- [ ] Yes, I'd like to implement this provider
- [ ] I can help with testing
- [ ] No, I'm just suggesting
