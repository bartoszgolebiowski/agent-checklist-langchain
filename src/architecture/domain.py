from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class WorkflowPhase(str, Enum):
    """Enumerates every deterministic phase in the checklist workflow."""

    WAITING_FOR_TASK_INPUT = "waiting_for_task_input"
    PARSING_TASK = "parsing_task"
    SCOPING_AND_ASSUMPTIONS = "scoping_and_assumptions"
    DECIDING_RESEARCH = "deciding_research"
    WEB_RESEARCH = "web_research"
    SOURCE_SELECTION = "source_selection"
    EXTRACTING_SIGNALS = "extracting_signals"
    INTEGRATING_FINDINGS = "integrating_findings"
    OUTLINE_CHECKLIST_SKELETON = "outline_checklist_skeleton"
    DRAFTING_CHECKLIST = "drafting_checklist"
    DEEPENING_CHECKLIST = "deepening_checklist"
    NORMALIZING_CHECKLIST = "normalizing_checklist"
    SELF_JUDGE = "self_judge"
    GAP_ANALYSIS = "gap_analysis"
    FINALIZING_CHECKLIST = "finalizing_checklist"
    EMITTING_CHECKLIST = "emitting_checklist"


class DecisionType(str, Enum):
    """Specifies the type of action the coordinator selected."""

    LLM_SKILL = "llm_skill"
    TOOL = "tool"
    COMPLETE = "complete"
    NOOP = "noop"


class GapRoute(str, Enum):
    """Possible remediation paths after the self-judging step."""

    NEEDS_RESEARCH = "needs_research"
    NEEDS_DEPTH = "needs_depth"
    READY = "ready"


class SkillName(str, Enum):
    """Registered skill identifiers."""

    PARSE_TASK = "parse_task"
    SCOPE_AND_ASSUME = "scope_and_assume"
    DECIDE_RESEARCH = "decide_research"
    SOURCE_SELECTION = "source_selection"
    EXTRACT_SIGNALS = "extract_signals"
    INTEGRATE_FINDINGS = "integrate_findings"
    OUTLINE_SKELETON = "outline_skeleton"
    DRAFT_CHECKLIST = "draft_checklist"
    DEEPEN_CHECKLIST = "deepen_checklist"
    NORMALIZE_CHECKLIST = "normalize_checklist"
    SELF_JUDGE = "self_judge"
    GAP_ANALYSIS = "gap_analysis"
    FINALIZE_CHECKLIST = "finalize_checklist"
    EMIT_CHECKLIST = "emit_checklist"


class ToolName(str, Enum):
    """Registered external tool identifiers."""

    TAVILY_SEARCH = "tavily_search"


class Decision(BaseModel):
    """Return value from the coordinator describing the next action."""

    decision_type: DecisionType
    reason: str
    skill: Optional[SkillName] = None
    tool: Optional[ToolName] = None
    route_key: str

    @classmethod
    def for_skill(cls, skill: SkillName, reason: str) -> "Decision":
        return cls(
            decision_type=DecisionType.LLM_SKILL,
            reason=reason,
            skill=skill,
            route_key=skill.value,
        )

    @classmethod
    def complete(cls, reason: str) -> "Decision":
        return cls(
            decision_type=DecisionType.COMPLETE,
            reason=reason,
            route_key="__complete__",
        )

    @classmethod
    def noop(cls, reason: str) -> "Decision":
        return cls(
            decision_type=DecisionType.NOOP,
            reason=reason,
            route_key="__noop__",
        )

    @classmethod
    def for_tool(cls, tool: ToolName, reason: str) -> "Decision":
        return cls(
            decision_type=DecisionType.TOOL,
            reason=reason,
            tool=tool,
            route_key=tool.value,
        )
