# Provider contract tests

`provider_contracts.py` defines reusable public-interface checks for LLM providers
and retrievers. `test_provider_contract.py` applies them to the offline mock
implementations, so the shared expectations run without credentials or network
access.

When adding or updating a provider, add a `Test<Name>ProviderContract` or
`Test<Name>RetrieverContract` subclass in `test_provider_contract.py` and override
its fixture with a local provider or mocked client. Keep network-dependent behavior
in the provider-specific tests; contract tests should exercise the common interface
only. Run them with `uv run pytest tests/contract`.
