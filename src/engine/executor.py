from __future__ import annotations

from typing import Any, Dict

from architecture.domain import SkillName
from llm.client import LLMClient
from memory.models import AgentState
from prompting.renderer import PromptRenderer
from skills.definitions import SkillDefinition, get_skill_definition
from skills.models import SkillOutput


class Executor:
    """Executes declarative skills using the configured LLM client."""

    def __init__(self, client: LLMClient, renderer: PromptRenderer) -> None:
        self._client = client
        self._renderer = renderer

    def run_skill(self, skill: SkillName, state: AgentState) -> SkillOutput:
        definition = get_skill_definition(skill)
        context = self._build_context(state=state, skill=skill)
        prompt = definition.render(self._renderer, context)
        return self._client.invoke(prompt, definition.output_model)

    def _build_context(self, *, state: AgentState, skill: SkillName) -> Dict[str, Any]:
        return {
            "state": state.model_dump(),
            "skill": skill.value,
            "phase": state.workflow.phase.value,
        }
