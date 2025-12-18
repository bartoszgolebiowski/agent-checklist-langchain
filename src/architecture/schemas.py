from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from .domain import WorkflowPhase


class TaskOverview(BaseModel):
    """Structured summary of the initial task request."""

    goal: str = Field(..., description="Restated main objective for the task.")
    constraints: List[str] = Field(
        default_factory=list,
        description="Explicit constraints that the checklist must respect.",
    )
    audience: List[str] = Field(
        default_factory=list,
        description="Stakeholders or recipients the checklist targets.",
    )
    success_criteria: List[str] = Field(
        default_factory=list,
        description="Observable signals demonstrating the goal is complete.",
    )


class ResearchSource(BaseModel):
    """Represents a potential source surfaced during research."""

    title: str = Field(..., description="Name or headline of the source.")
    url: str = Field(..., description="Canonical link to the source content.")
    summary: str = Field(..., description="Concise description of the source.")
    credibility: str = Field(..., description="Free-form signal describing trust.")


class ResearchSignal(BaseModel):
    """Atomic insight extracted from a source."""

    source_title: str = Field(..., description="Title of the origin source.")
    signal: str = Field(..., description="Key fact or observation extracted.")
    implication: str = Field(..., description="Why the signal matters operationally.")


class ActionableInsight(BaseModel):
    """Connects research signals to actionable checklist recommendations."""

    area: str = Field(..., description="Checklist area or theme impacted.")
    recommendation: str = Field(..., description="Concrete action to incorporate.")
    risk_mitigated: str = Field(..., description="Risk reduced by the action.")


class ChecklistItem(BaseModel):
    """Single actionable checklist entry with clear verification criteria."""

    identifier: str = Field(..., description="Stable item identifier (e.g., 1.2).")
    title: str = Field(..., description="Short, action-oriented item label.")
    description: str = Field(..., description="Narrative explaining the item.")
    sub_steps: List[str] = Field(
        default_factory=list,
        description="Optional detailed steps nested under the item.",
    )
    acceptance_criteria: List[str] = Field(
        default_factory=list,
        description="Checks that confirm the item is done correctly.",
    )
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Conditions that must be met before executing the item.",
    )


class ChecklistSection(BaseModel):
    """Logical grouping of checklist items."""

    name: str = Field(..., description="Section label (e.g., Planning).")
    objective: str = Field(..., description="Outcome this section accomplishes.")
    items: List[ChecklistItem] = Field(
        default_factory=list,
        description="Checklist items that belong to the section.",
    )


class ChecklistPackage(BaseModel):
    """Holds the current revision of the checklist along with commentary."""

    sections: List[ChecklistSection] = Field(
        default_factory=list,
        description="Ordered sections comprising the checklist.",
    )
    notes: List[str] = Field(
        default_factory=list,
        description="Supplemental commentary, caveats, or reminders.",
    )


class AgentResponse(BaseModel):
    """User-facing response from the agent."""

    phase: WorkflowPhase = Field(
        ..., description="Workflow phase when the response was produced."
    )
    message: str = Field(..., description="Primary assistant message to the user.")
    sections: List[ChecklistSection] = Field(
        default_factory=list,
        description="Checklist snapshot to surface alongside the message.",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Arbitrary structured metadata (e.g., CTAs, flags).",
    )
