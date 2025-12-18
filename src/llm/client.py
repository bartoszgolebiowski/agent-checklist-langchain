from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from llm.config import LLMConfig
from llm.exceptions import LLMCallError, LLMConfigurationError

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True, slots=True)
class LLMClient:
    """Thin wrapper around OpenRouter's OpenAI-compatible Responses API."""

    config: LLMConfig
    _client: Optional[OpenAI] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        api_key = self.config.api_key.get_secret_value()
        if not api_key:
            raise LLMConfigurationError("LLMConfig.api_key must be provided")
        client = OpenAI(api_key=api_key, base_url=self.config.base_url)
        object.__setattr__(self, "_client", client)

    @classmethod
    def from_env(cls) -> "LLMClient":
        """Convenience constructor using environment-derived config."""

        return cls(config=LLMConfig.from_env())

    def invoke(self, prompt: str, output_model: Type[T]) -> T:
        """Execute the prompt and coerce the response into the output model."""

        if self._client is None:  # pragma: no cover - defensive
            raise LLMConfigurationError("LLM client is not initialized")
        try:
            response = self._client.responses.parse(
                model=self.config.model,
                input=prompt,
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_output_tokens,
                text_format=output_model,
            )
        except Exception as exc:  # pragma: no cover - network errors
            raise LLMCallError("Failed to execute LLM call") from exc

        payload = response.output_parsed
        if payload is None:
            raise LLMCallError("LLM response payload was empty")
        try:
            return output_model.model_validate(payload)
        except ValidationError as exc:
            raise LLMCallError("LLM response failed schema validation") from exc
