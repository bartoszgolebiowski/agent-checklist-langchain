from __future__ import annotations

from copy import deepcopy
from typing import Callable, Dict

from architecture.domain import GapRoute, SkillName, ToolName, WorkflowPhase
from architecture.schemas import AgentResponse, ChecklistPackage, ResearchSource
from memory.models import AgentState, ConversationTurn
from skills import models as skill_models
from tools.models import SearchToolResult

SkillHandler = Callable[[AgentState, skill_models.SkillOutput], AgentState]


def create_initial_state(user_message: str) -> AgentState:
    """Bootstraps a new agent state with the incoming task description."""

    state = AgentState()
    state.working.task_input = user_message
    state.workflow.phase = WorkflowPhase.PARSING_TASK
    state.episodic.turns.append(ConversationTurn(role="user", content=user_message))
    return state


def ingest_user_message(state: AgentState, user_message: str) -> AgentState:
    """Resets the workflow to parse a new user instruction."""

    new_state = deepcopy(state)
    new_state.working.task_input = user_message
    new_state.workflow.phase = WorkflowPhase.PARSING_TASK
    new_state.workflow.gap_route = None
    new_state.episodic.turns.append(ConversationTurn(role="user", content=user_message))
    new_state.working.agent_response = None
    new_state.working.agent_summary = None
    new_state.working.final_message = None
    return new_state


def update_state_from_skill(
    state: AgentState,
    skill: SkillName,
    output: skill_models.SkillOutput,
) -> AgentState:
    """Dispatches skill output to the appropriate handler."""

    handler = _SKILL_HANDLERS.get(skill)
    if handler is None:
        raise ValueError(f"No state handler registered for skill {skill.value}")
    return handler(state, output)


def apply_tavily_search_result(
    state: AgentState, result: SearchToolResult
) -> AgentState:
    """Updates memory using normalized Tavily search output."""

    new_state = deepcopy(state)
    new_state.working.research_sources = _sources_from_search_items(result)
    new_state.workflow.research_completed = True
    new_state.workflow.phase = WorkflowPhase.SOURCE_SELECTION
    _track_tool_completion(new_state, ToolName.TAVILY_SEARCH)
    return new_state


def build_agent_response(state: AgentState) -> AgentResponse:
    """Creates the final user-facing response payload."""

    if state.working.agent_response:
        return state.working.agent_response

    sections = []
    if state.working.final_package:
        sections = state.working.final_package.sections
    elif state.working.normalized_package:
        sections = state.working.normalized_package.sections

    message = state.working.final_message or "Checklist ready for review."
    return AgentResponse(
        phase=state.workflow.phase,
        message=message,
        sections=sections,
        metadata={"fallback": True},
    )


def _track_completion(state: AgentState, skill: SkillName) -> None:
    counts = state.workflow.iteration_counts
    counts[skill.value] = counts.get(skill.value, 0) + 1
    state.workflow.last_skill = skill


def _track_tool_completion(state: AgentState, tool: ToolName) -> None:
    counts = state.workflow.iteration_counts
    counts[tool.value] = counts.get(tool.value, 0) + 1
    state.workflow.last_tool = tool


def _record_assistant_turn(state: AgentState, content: str) -> None:
    state.episodic.turns.append(ConversationTurn(role="assistant", content=content))


def _handle_parse_task(
    state: AgentState, output: skill_models.TaskParsingOutput
) -> AgentState:
    new_state = deepcopy(state)
    new_state.working.task_overview = output.to_overview()
    new_state.working.scope_notes.clear()
    new_state.working.assumptions.clear()
    new_state.working.edge_cases.clear()
    new_state.workflow.phase = WorkflowPhase.SCOPING_AND_ASSUMPTIONS
    _track_completion(new_state, SkillName.PARSE_TASK)
    _record_assistant_turn(new_state, output.ai_response)
    return new_state


def _handle_scoping(
    state: AgentState, output: skill_models.ScopingOutput
) -> AgentState:
    new_state = deepcopy(state)
    new_state.working.scope_notes = output.scope_notes
    new_state.working.assumptions = output.assumptions
    new_state.working.edge_cases = output.edge_cases
    new_state.workflow.phase = WorkflowPhase.DECIDING_RESEARCH
    _track_completion(new_state, SkillName.SCOPE_AND_ASSUME)
    _record_assistant_turn(new_state, output.ai_response)
    return new_state


def _handle_decide_research(
    state: AgentState, output: skill_models.ResearchDecisionOutput
) -> AgentState:
    new_state = deepcopy(state)
    new_state.workflow.needs_research = output.needs_research
    new_state.workflow.phase = (
        WorkflowPhase.WEB_RESEARCH
        if output.needs_research
        else WorkflowPhase.OUTLINE_CHECKLIST_SKELETON
    )
    new_state.working.research_questions = output.research_questions
    new_state.workflow.research_completed = not output.needs_research
    _track_completion(new_state, SkillName.DECIDE_RESEARCH)
    _record_assistant_turn(new_state, output.ai_response)
    return new_state


def _handle_source_selection(
    state: AgentState, output: skill_models.SourceSelectionOutput
) -> AgentState:
    new_state = deepcopy(state)
    new_state.working.selected_sources = output.selected_sources
    new_state.workflow.phase = WorkflowPhase.EXTRACTING_SIGNALS
    _track_completion(new_state, SkillName.SOURCE_SELECTION)
    _record_assistant_turn(new_state, output.ai_response)
    return new_state


def _handle_extract_signals(
    state: AgentState, output: skill_models.SignalExtractionOutput
) -> AgentState:
    new_state = deepcopy(state)
    new_state.working.research_signals = output.signals
    new_state.workflow.phase = WorkflowPhase.INTEGRATING_FINDINGS
    _track_completion(new_state, SkillName.EXTRACT_SIGNALS)
    _record_assistant_turn(new_state, output.ai_response)
    return new_state


def _handle_integrate_findings(
    state: AgentState, output: skill_models.IntegrationOutput
) -> AgentState:
    new_state = deepcopy(state)
    new_state.working.actionable_insights = output.actionable_insights
    new_state.workflow.phase = WorkflowPhase.OUTLINE_CHECKLIST_SKELETON
    _track_completion(new_state, SkillName.INTEGRATE_FINDINGS)
    _record_assistant_turn(new_state, output.ai_response)
    return new_state


def _make_package(sections) -> ChecklistPackage:
    return ChecklistPackage(sections=sections)


def _handle_outline_skeleton(
    state: AgentState, output: skill_models.OutlineSkeletonOutput
) -> AgentState:
    new_state = deepcopy(state)
    new_state.working.draft_package = _make_package(output.sections)
    new_state.workflow.phase = WorkflowPhase.DRAFTING_CHECKLIST
    _track_completion(new_state, SkillName.OUTLINE_SKELETON)
    _record_assistant_turn(new_state, output.ai_response)
    return new_state


def _handle_draft_checklist(
    state: AgentState, output: skill_models.DraftChecklistOutput
) -> AgentState:
    new_state = deepcopy(state)
    new_state.working.draft_package = _make_package(output.sections)
    new_state.workflow.phase = WorkflowPhase.DEEPENING_CHECKLIST
    _track_completion(new_state, SkillName.DRAFT_CHECKLIST)
    _record_assistant_turn(new_state, output.ai_response)
    return new_state


def _handle_deepen_checklist(
    state: AgentState, output: skill_models.DeepenChecklistOutput
) -> AgentState:
    new_state = deepcopy(state)
    new_state.working.draft_package = _make_package(output.sections)
    new_state.workflow.phase = WorkflowPhase.NORMALIZING_CHECKLIST
    _track_completion(new_state, SkillName.DEEPEN_CHECKLIST)
    _record_assistant_turn(new_state, output.ai_response)
    return new_state


def _handle_normalize_checklist(
    state: AgentState, output: skill_models.NormalizeChecklistOutput
) -> AgentState:
    new_state = deepcopy(state)
    new_state.working.normalized_package = _make_package(output.sections)
    new_state.workflow.phase = WorkflowPhase.SELF_JUDGE
    _track_completion(new_state, SkillName.NORMALIZE_CHECKLIST)
    _record_assistant_turn(new_state, output.ai_response)
    return new_state


def _handle_self_judge(
    state: AgentState, output: skill_models.SelfJudgeOutput
) -> AgentState:
    new_state = deepcopy(state)
    new_state.workflow.quality_score = output.score
    new_state.workflow.phase = (
        WorkflowPhase.FINALIZING_CHECKLIST
        if output.threshold_met
        else WorkflowPhase.GAP_ANALYSIS
    )
    summary_lines = [
        f"Score: {output.score:.2f}",
        *[f"Strength: {item}" for item in output.strengths],
        *[f"Gap: {item}" for item in output.gaps],
    ]
    new_state.working.agent_summary = "\n".join(summary_lines)
    _track_completion(new_state, SkillName.SELF_JUDGE)
    _record_assistant_turn(new_state, output.ai_response)
    return new_state


def _handle_gap_analysis(
    state: AgentState, output: skill_models.GapAnalysisOutput
) -> AgentState:
    new_state = deepcopy(state)
    new_state.workflow.gap_route = output.route
    if output.route == GapRoute.NEEDS_RESEARCH:
        new_state.workflow.phase = WorkflowPhase.DECIDING_RESEARCH
        new_state.workflow.needs_research = True
    elif output.route == GapRoute.NEEDS_DEPTH:
        new_state.workflow.phase = WorkflowPhase.DEEPENING_CHECKLIST
    else:
        new_state.workflow.phase = WorkflowPhase.FINALIZING_CHECKLIST
    new_state.working.gap_reason = output.reason
    _track_completion(new_state, SkillName.GAP_ANALYSIS)
    _record_assistant_turn(new_state, output.ai_response)
    return new_state


def _handle_finalize_checklist(
    state: AgentState, output: skill_models.FinalizeChecklistOutput
) -> AgentState:
    new_state = deepcopy(state)
    new_state.working.final_package = _make_package(output.sections)
    new_state.working.agent_summary = "\n".join(output.highlights)
    new_state.workflow.phase = WorkflowPhase.EMITTING_CHECKLIST
    _track_completion(new_state, SkillName.FINALIZE_CHECKLIST)
    _record_assistant_turn(new_state, output.ai_response)
    return new_state


def _handle_emit_checklist(
    state: AgentState, output: skill_models.EmitChecklistOutput
) -> AgentState:
    new_state = deepcopy(state)
    new_state.working.final_message = output.final_message
    sections = []
    if new_state.working.final_package:
        sections = new_state.working.final_package.sections
    elif new_state.working.normalized_package:
        sections = new_state.working.normalized_package.sections
    response = AgentResponse(
        phase=WorkflowPhase.EMITTING_CHECKLIST,
        message=output.final_message,
        sections=sections,
        metadata={"call_to_action": output.call_to_action},
    )
    new_state.working.agent_response = response
    new_state.workflow.phase = WorkflowPhase.WAITING_FOR_TASK_INPUT
    _track_completion(new_state, SkillName.EMIT_CHECKLIST)
    _record_assistant_turn(new_state, output.ai_response)
    return new_state


def _sources_from_search_items(result: SearchToolResult) -> list[ResearchSource]:
    sources: list[ResearchSource] = []
    for idx, item in enumerate(result.items, start=1):
        summary = item.summary.strip() or " ".join(item.findings).strip()
        summary = summary or "See linked source for details."
        url = item.source_urls[0] if item.source_urls else ""
        title = item.title.strip() or f"Result {idx}"
        sources.append(
            ResearchSource(
                title=title,
                url=url,
                summary=summary,
                credibility="Tavily search result",
            )
        )
    return sources


_SKILL_HANDLERS: Dict[SkillName, SkillHandler] = {
    SkillName.PARSE_TASK: _handle_parse_task,
    SkillName.SCOPE_AND_ASSUME: _handle_scoping,
    SkillName.DECIDE_RESEARCH: _handle_decide_research,
    SkillName.SOURCE_SELECTION: _handle_source_selection,
    SkillName.EXTRACT_SIGNALS: _handle_extract_signals,
    SkillName.INTEGRATE_FINDINGS: _handle_integrate_findings,
    SkillName.OUTLINE_SKELETON: _handle_outline_skeleton,
    SkillName.DRAFT_CHECKLIST: _handle_draft_checklist,
    SkillName.DEEPEN_CHECKLIST: _handle_deepen_checklist,
    SkillName.NORMALIZE_CHECKLIST: _handle_normalize_checklist,
    SkillName.SELF_JUDGE: _handle_self_judge,
    SkillName.GAP_ANALYSIS: _handle_gap_analysis,
    SkillName.FINALIZE_CHECKLIST: _handle_finalize_checklist,
    SkillName.EMIT_CHECKLIST: _handle_emit_checklist,
}
