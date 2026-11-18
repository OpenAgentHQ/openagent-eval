"""Local disk response cache for LLM generation calls."""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from openagent_eval.providers.models import TokenUsage

logger = logging.getLogger(__name__)


class ResponseCache:
    """Content-hash-keyed disk cache for LLM provider responses.

    Entries are keyed by a SHA-256 digest of ``(provider, model, prompt)`` and
    stored as individual JSON files under ``cache_dir``.
    """

    def __init__(
        self,
        cache_dir: str | Path = ".cache/openagent_eval",
        *,
        enabled: bool = True,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled

    @staticmethod
    def build_key(provider: str, model: str, prompt: str) -> str:
        """Compute a deterministic hex key from ``(provider, model, prompt)``."""
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        payload = json.dumps(
            {
                "provider": provider or "",
                "model": model or "",
                "prompt_hash": prompt_hash,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _entry_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(
        self, provider: str, model: str, prompt: str
    ) -> tuple[str, TokenUsage | None] | None:
        """Return ``(content, usage)`` on cache hit, or ``None`` on miss/error."""
        if not self.enabled:
            return None
        path = self._entry_path(self.build_key(provider, model, prompt))
        if not path.is_file():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or "content" not in raw:
                return None
            content = str(raw["content"])
            usage_data = raw.get("usage")
            usage = TokenUsage(**usage_data) if isinstance(usage_data, dict) else None
            return content, usage
        except Exception as exc:
            logger.debug("Ignoring unreadable response cache entry %s: %s", path, exc)
            return None

    def set(
        self,
        provider: str,
        model: str,
        prompt: str,
        content: str,
        usage: TokenUsage | None = None,
        latency_ms: float | None = None,
    ) -> None:
        """Persist a response entry atomically to disk."""
        if not self.enabled:
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self._entry_path(self.build_key(provider, model, prompt))
        payload: dict[str, Any] = {
            "provider": provider or "",
            "model": model or "",
            "content": content,
            "usage": usage.model_dump() if usage is not None else None,
            "latency_ms": latency_ms,
        }
        serialized = json.dumps(payload, ensure_ascii=False)
        fd, tmp_name = tempfile.mkstemp(dir=self.cache_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(serialized)
            os.replace(tmp_name, path)
        except Exception:
            with contextlib.suppress(OSError):
                os.unlink(tmp_name)
            raise

    def clear(self) -> int:
        """Delete all cached response JSON files and return the count removed."""
        if not self.cache_dir.exists():
            return 0
        removed = 0
        for entry in self.cache_dir.glob("*.json"):
            with contextlib.suppress(OSError):
                entry.unlink()
                removed += 1
        return removed
