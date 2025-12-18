from __future__ import annotations

from architecture.domain import Decision, SkillName, ToolName, WorkflowPhase
from memory.models import AgentState


class Coordinator:
    """Deterministic state machine that selects the next skill to run."""

    def next_action(self, state: AgentState) -> Decision:
        phase = state.workflow.phase
        if phase == WorkflowPhase.WAITING_FOR_TASK_INPUT:
            if state.working.task_input:
                return Decision.for_skill(
                    SkillName.PARSE_TASK, "Parse the freshly provided task input."
                )
            return Decision.noop("No task input provided yet.")
        if phase == WorkflowPhase.PARSING_TASK:
            return Decision.for_skill(
                SkillName.PARSE_TASK, "Structure the incoming task description."
            )
        if phase == WorkflowPhase.SCOPING_AND_ASSUMPTIONS:
            return Decision.for_skill(
                SkillName.SCOPE_AND_ASSUME, "Capture assumptions and explicit scope."
            )
        if phase == WorkflowPhase.DECIDING_RESEARCH:
            return Decision.for_skill(
                SkillName.DECIDE_RESEARCH,
                "Decide whether external research is required.",
            )
        if phase == WorkflowPhase.WEB_RESEARCH:
            return Decision.for_tool(
                ToolName.TAVILY_SEARCH, "Run Tavily search to gather sources."
            )
        if phase == WorkflowPhase.SOURCE_SELECTION:
            return Decision.for_skill(
                SkillName.SOURCE_SELECTION, "Select the most credible sources."
            )
        if phase == WorkflowPhase.EXTRACTING_SIGNALS:
            return Decision.for_skill(
                SkillName.EXTRACT_SIGNALS, "Extract actionable signals from sources."
            )
        if phase == WorkflowPhase.INTEGRATING_FINDINGS:
            return Decision.for_skill(
                SkillName.INTEGRATE_FINDINGS,
                "Convert signals into checklist implications.",
            )
        if phase == WorkflowPhase.OUTLINE_CHECKLIST_SKELETON:
            return Decision.for_skill(
                SkillName.OUTLINE_SKELETON, "Build the checklist skeleton."
            )
        if phase == WorkflowPhase.DRAFTING_CHECKLIST:
            return Decision.for_skill(
                SkillName.DRAFT_CHECKLIST, "Draft checklist items per section."
            )
        if phase == WorkflowPhase.DEEPENING_CHECKLIST:
            return Decision.for_skill(
                SkillName.DEEPEN_CHECKLIST, "Deepen each checklist item with sub-steps."
            )
        if phase == WorkflowPhase.NORMALIZING_CHECKLIST:
            return Decision.for_skill(
                SkillName.NORMALIZE_CHECKLIST,
                "Normalize the checklist for consistency.",
            )
        if phase == WorkflowPhase.SELF_JUDGE:
            return Decision.for_skill(
                SkillName.SELF_JUDGE, "Score the checklist against the rubric."
            )
        if phase == WorkflowPhase.GAP_ANALYSIS:
            return Decision.for_skill(
                SkillName.GAP_ANALYSIS, "Route remediation based on the quality gap."
            )
        if phase == WorkflowPhase.FINALIZING_CHECKLIST:
            return Decision.for_skill(
                SkillName.FINALIZE_CHECKLIST, "Lock the final checklist package."
            )
        if phase == WorkflowPhase.EMITTING_CHECKLIST:
            return Decision.for_skill(
                SkillName.EMIT_CHECKLIST, "Explain the finalized checklist to the user."
            )
        return Decision.complete("Workflow finished.")
