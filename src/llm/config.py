from __future__ import annotations

import os
from dataclasses import dataclass

from pydantic import SecretStr


DEFAULT_MODEL = "x-ai/grok-4-fast"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 1200


@dataclass(frozen=True, slots=True)
class LLMConfig:
    """Immutable configuration for the OpenRouter-powered LLM client."""

    api_key: SecretStr
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    temperature: float = DEFAULT_TEMPERATURE
    max_output_tokens: int = DEFAULT_MAX_TOKENS

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Construct configuration using standard OpenRouter environment vars."""

        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "Missing OPENROUTER_API_KEY (or fallback OPENAI_API_KEY) for LLM client."
            )

        model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
        base_url = os.getenv("OPENROUTER_BASE_URL", DEFAULT_BASE_URL)
        temperature = float(os.getenv("OPENROUTER_TEMPERATURE", DEFAULT_TEMPERATURE))
        max_output_tokens = int(
            os.getenv("OPENROUTER_MAX_OUTPUT_TOKENS", DEFAULT_MAX_TOKENS)
        )

        return cls(
            api_key=SecretStr(api_key),
            model=model,
            base_url=base_url,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
