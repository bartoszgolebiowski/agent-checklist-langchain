from __future__ import annotations


class LLMCallError(RuntimeError):
    """Raised when the LLM client cannot produce or parse a valid response."""


class LLMConfigurationError(ValueError):
    """Raised when essential configuration such as the API key is missing."""
