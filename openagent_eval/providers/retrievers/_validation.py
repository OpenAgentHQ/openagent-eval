"""Early validation for retriever ``settings`` keys.

Retriever providers accept a free-form ``settings`` dict from user config
(``retriever.settings`` in the YAML). Without validation, a typo such as
``collectoin_name`` is either swallowed by a provider's ``**kwargs`` or blows
up with an opaque ``TypeError`` deep inside a constructor -- and only at
runtime. This module surfaces unknown keys early, at provider-build time, with
a "did you mean" suggestion.

The behaviour mirrors how unknown/misspelled metric names are handled in
:mod:`openagent_eval.config.loader` (see the metrics block around
``loader.py:139``): the offending keys are dropped and a ``logging.warning`` is
emitted naming them, rather than hard-failing. This keeps a single stray key
from aborting an otherwise-valid evaluation run.
"""

from __future__ import annotations

import difflib
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

logger = logging.getLogger(__name__)


def validate_retriever_settings(
    provider_name: str,
    settings: Mapping[str, Any],
    allowed_keys: Iterable[str],
) -> list[str]:
    """Warn about unknown ``settings`` keys for a retriever provider.

    Args:
        provider_name: Name of the retriever provider (for the log message).
        settings: The user-supplied settings mapping to check.
        allowed_keys: The setting keys the provider actually understands.

    Returns:
        The list of unknown keys found (in the order they appear in
        ``settings``). Empty when every key is recognised.
    """
    allowed = set(allowed_keys)
    unknown = [key for key in settings if key not in allowed]

    for key in unknown:
        match = difflib.get_close_matches(key, allowed, n=1)
        suggestion = f" Did you mean '{match[0]}'?" if match else ""
        logger.warning(
            "Unknown setting '%s' for retriever '%s'; it will be ignored.%s "
            "Known settings: %s",
            key,
            provider_name,
            suggestion,
            ", ".join(sorted(allowed)),
        )

    return unknown
