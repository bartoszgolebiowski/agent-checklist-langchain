from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from architecture.domain import GapRoute
from architecture.schemas import (
    ActionableInsight,
    ChecklistSection,
    ResearchSignal,
    ResearchSource,
    TaskOverview,
)


class SkillOutput(BaseModel):
    """Base class shared across all skill outputs."""

    ai_response: str = Field(
        ..., description="Natural-language narration for this workflow step."
    )


class TaskParsingOutput(SkillOutput):
    """Structured representation of the initial task."""

    goal: str = Field(..., description="Restated primary objective for the task.")
    constraints: List[str] = Field(
        default_factory=list,
        description="Explicit constraints mentioned by the user.",
    )
    audience: List[str] = Field(
        default_factory=list,
        description="Intended recipients or stakeholders for the checklist.",
    )
    success_criteria: List[str] = Field(
        default_factory=list,
        description="Observable signals that confirm the goal is satisfied.",
    )

    def to_overview(self) -> TaskOverview:
        return TaskOverview(
            goal=self.goal,
            constraints=self.constraints,
            audience=self.audience,
            success_criteria=self.success_criteria,
        )


class ScopingOutput(SkillOutput):
    """Captures assumptions, scope notes, and edge cases."""

    scope_notes: List[str] = Field(
        default_factory=list,
        description="Clarifications that bound the checklist's scope.",
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Assumptions that must hold true for the plan to work.",
    )
    edge_cases: List[str] = Field(
        default_factory=list,
        description="Notable scenarios or failure modes to consider.",
    )


class ResearchDecisionOutput(SkillOutput):
    """Determines whether external research is required."""

    needs_research: bool = Field(
        ..., description="Flag indicating if outside research is warranted."
    )
    justification: str = Field(
        ..., description="Rationale behind the research recommendation."
    )
    research_questions: List[str] = Field(
        default_factory=list,
        description="Concrete questions the research phase should answer.",
    )


class SourceSelectionOutput(SkillOutput):
    """Narrows research down to the most credible sources."""

    selected_sources: List[ResearchSource] = Field(
        default_factory=list,
        description="Curated list of sources worth citing downstream.",
    )


class SignalExtractionOutput(SkillOutput):
    """Extracts signals and edge cases from selected sources."""

    signals: List[ResearchSignal] = Field(
        default_factory=list,
        description="Atomic insights pulled from each selected source.",
    )


class IntegrationOutput(SkillOutput):
    """Connects research signals to actionable recommendations."""

    actionable_insights: List[ActionableInsight] = Field(
        default_factory=list,
        description="Implications that convert raw signals into guidance.",
    )


class OutlineSkeletonOutput(SkillOutput):
    """Defines the top-level checklist sections."""

    sections: List[ChecklistSection] = Field(
        default_factory=list,
        description="Initial section scaffolding for the checklist.",
    )


class DraftChecklistOutput(SkillOutput):
    """Generates the first draft of the checklist items."""

    sections: List[ChecklistSection] = Field(
        default_factory=list,
        description="Draft checklist sections populated with items.",
    )


class DeepenChecklistOutput(SkillOutput):
    """Adds sub-steps, prerequisites, and acceptance checks."""

    sections: List[ChecklistSection] = Field(
        default_factory=list,
        description="Checklist enriched with depth details per item.",
    )


class NormalizeChecklistOutput(SkillOutput):
    """Ensures consistent phrasing and removes duplicates."""

    sections: List[ChecklistSection] = Field(
        default_factory=list,
        description="Normalized sections ready for quality review.",
    )


class SelfJudgeOutput(SkillOutput):
    """Scores the checklist against a rubric."""

    score: float = Field(..., description="Rubric score between 0 and 1.")
    threshold_met: bool = Field(
        ..., description="Indicates whether the score passes the bar."
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="Highlights that demonstrate checklist quality.",
    )
    gaps: List[str] = Field(
        default_factory=list,
        description="Deficiencies that still need to be addressed.",
    )


class GapAnalysisOutput(SkillOutput):
    """Determines why the checklist missed the quality bar."""

    route: GapRoute = Field(
        ..., description="Where the workflow should go next (research/depth/ready)."
    )
    reason: str = Field(
        ..., description="Short explanation for the selected remediation path."
    )
    next_focus: str = Field(
        ..., description="Specific aspect to prioritize in the next step."
    )


class FinalizeChecklistOutput(SkillOutput):
    """Produces the final checklist package."""

    sections: List[ChecklistSection] = Field(
        default_factory=list,
        description="Fully polished checklist sections ready for delivery.",
    )
    highlights: List[str] = Field(
        default_factory=list,
        description="Key wins or differentiators worth calling out.",
    )
    handoff_notes: List[str] = Field(
        default_factory=list,
        description="Operational notes for whoever executes the checklist.",
    )


class EmitChecklistOutput(SkillOutput):
    """Crafts the user-facing response for the final checklist."""

    final_message: str = Field(
        ..., description="User-facing narration summarizing the checklist."
    )
    call_to_action: str = Field(
        ..., description="Concrete next step the user should take."
    )
