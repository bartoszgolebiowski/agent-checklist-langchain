from __future__ import annotations

from typing import Any, Dict, Optional

from agent.context import Context
from agent.graph import build_checklist_graph


class ChecklistAgent:
    """High-level facade for invoking the LangGraph agent."""

    def __init__(self, context: Optional[Context] = None) -> None:
        self._context = context or Context()
        self._graph = build_checklist_graph(self._context)

    def invoke(
        self, user_message: str, state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = dict(state or {})
        payload["user_message"] = user_message
        return self._graph.invoke(payload)
