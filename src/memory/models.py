from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from architecture.domain import GapRoute, SkillName, ToolName, WorkflowPhase
from architecture.schemas import (
    ActionableInsight,
    AgentResponse,
    ChecklistPackage,
    ResearchSignal,
    ResearchSource,
    TaskOverview,
)


class CoreMemory(BaseModel):
    """Static persona and behavioral settings."""

    persona: str = "You are a systems-thinking checklist architect."
    tone: str = "Direct, pragmatic, and encouraging."


class SemanticMemory(BaseModel):
    """Long-term preferences for how checklists should be framed."""

    organization_name: str = "Checklist Agent"
    domain_preferences: List[str] = Field(default_factory=list)


class ConversationTurn(BaseModel):
    """Single conversational exchange."""

    role: str
    content: str


class EpisodicMemory(BaseModel):
    """Records episodic interactions for grounding follow-ups."""

    turns: List[ConversationTurn] = Field(default_factory=list)


class WorkflowState(BaseModel):
    """Holds routing flags and bookkeeping for the coordinator."""

    phase: WorkflowPhase = WorkflowPhase.WAITING_FOR_TASK_INPUT
    needs_research: bool = False
    research_completed: bool = False
    last_skill: Optional[SkillName] = None
    last_tool: Optional[ToolName] = None
    quality_score: Optional[float] = None
    gap_route: Optional[GapRoute] = None
    iteration_counts: Dict[str, int] = Field(default_factory=dict)


class WorkingMemory(BaseModel):
    """Short-term data referenced throughout the workflow."""

    task_input: Optional[str] = None
    task_overview: Optional[TaskOverview] = None
    scope_notes: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    edge_cases: List[str] = Field(default_factory=list)
    research_questions: List[str] = Field(default_factory=list)
    research_sources: List[ResearchSource] = Field(default_factory=list)
    selected_sources: List[ResearchSource] = Field(default_factory=list)
    research_signals: List[ResearchSignal] = Field(default_factory=list)
    actionable_insights: List[ActionableInsight] = Field(default_factory=list)
    draft_package: Optional[ChecklistPackage] = None
    normalized_package: Optional[ChecklistPackage] = None
    final_package: Optional[ChecklistPackage] = None
    agent_summary: Optional[str] = None
    gap_reason: Optional[str] = None
    final_message: Optional[str] = None
    agent_response: Optional[AgentResponse] = None


class AgentState(BaseModel):
    """Aggregate root representing the full agent memory tree."""

    core: CoreMemory = Field(default_factory=CoreMemory)
    semantic: SemanticMemory = Field(default_factory=SemanticMemory)
    episodic: EpisodicMemory = Field(default_factory=EpisodicMemory)
    workflow: WorkflowState = Field(default_factory=WorkflowState)
    working: WorkingMemory = Field(default_factory=WorkingMemory)
