from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from jinja2 import Environment, FileSystemLoader, StrictUndefined


class PromptRenderer:
    """Renders Jinja templates into LLM-ready prompts."""

    def __init__(self, templates_path: Path | None = None) -> None:
        base_path = templates_path or Path(__file__).resolve().parent / "jinja"
        loader = FileSystemLoader(str(base_path))
        self._env = Environment(
            loader=loader,
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )

    def render(self, template_name: str, context: Mapping[str, Any]) -> str:
        template = self._env.get_template(template_name)
        return template.render(**context)
