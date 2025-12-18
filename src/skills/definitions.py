from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Type

from architecture.domain import SkillName
from prompting.renderer import PromptRenderer
from skills import models as skill_models


@dataclass(frozen=True, slots=True)
class SkillDefinition:
    """Declarative specification for a single skill."""

    name: SkillName
    template_path: str
    output_model: Type[skill_models.SkillOutput]

    def render(self, renderer: PromptRenderer, context: Mapping[str, Any]) -> str:
        return renderer.render(self.template_path, context)


def _definition(
    name: SkillName, template: str, model: Type[skill_models.SkillOutput]
) -> SkillDefinition:
    return SkillDefinition(name=name, template_path=template, output_model=model)


SKILL_REGISTRY: Dict[SkillName, SkillDefinition] = {
    SkillName.PARSE_TASK: _definition(
        SkillName.PARSE_TASK,
        "skills/parse_task.j2",
        skill_models.TaskParsingOutput,
    ),
    SkillName.SCOPE_AND_ASSUME: _definition(
        SkillName.SCOPE_AND_ASSUME,
        "skills/scope_and_assume.j2",
        skill_models.ScopingOutput,
    ),
    SkillName.DECIDE_RESEARCH: _definition(
        SkillName.DECIDE_RESEARCH,
        "skills/decide_research.j2",
        skill_models.ResearchDecisionOutput,
    ),
    SkillName.SOURCE_SELECTION: _definition(
        SkillName.SOURCE_SELECTION,
        "skills/source_selection.j2",
        skill_models.SourceSelectionOutput,
    ),
    SkillName.EXTRACT_SIGNALS: _definition(
        SkillName.EXTRACT_SIGNALS,
        "skills/extract_signals.j2",
        skill_models.SignalExtractionOutput,
    ),
    SkillName.INTEGRATE_FINDINGS: _definition(
        SkillName.INTEGRATE_FINDINGS,
        "skills/integrate_findings.j2",
        skill_models.IntegrationOutput,
    ),
    SkillName.OUTLINE_SKELETON: _definition(
        SkillName.OUTLINE_SKELETON,
        "skills/outline_skeleton.j2",
        skill_models.OutlineSkeletonOutput,
    ),
    SkillName.DRAFT_CHECKLIST: _definition(
        SkillName.DRAFT_CHECKLIST,
        "skills/draft_checklist.j2",
        skill_models.DraftChecklistOutput,
    ),
    SkillName.DEEPEN_CHECKLIST: _definition(
        SkillName.DEEPEN_CHECKLIST,
        "skills/deepen_checklist.j2",
        skill_models.DeepenChecklistOutput,
    ),
    SkillName.NORMALIZE_CHECKLIST: _definition(
        SkillName.NORMALIZE_CHECKLIST,
        "skills/normalize_checklist.j2",
        skill_models.NormalizeChecklistOutput,
    ),
    SkillName.SELF_JUDGE: _definition(
        SkillName.SELF_JUDGE,
        "skills/self_judge.j2",
        skill_models.SelfJudgeOutput,
    ),
    SkillName.GAP_ANALYSIS: _definition(
        SkillName.GAP_ANALYSIS,
        "skills/gap_analysis.j2",
        skill_models.GapAnalysisOutput,
    ),
    SkillName.FINALIZE_CHECKLIST: _definition(
        SkillName.FINALIZE_CHECKLIST,
        "skills/finalize_checklist.j2",
        skill_models.FinalizeChecklistOutput,
    ),
    SkillName.EMIT_CHECKLIST: _definition(
        SkillName.EMIT_CHECKLIST,
        "skills/emit_checklist.j2",
        skill_models.EmitChecklistOutput,
    ),
}


def get_skill_definition(skill: SkillName) -> SkillDefinition:
    try:
        return SKILL_REGISTRY[skill]
    except KeyError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Skill {skill.value} is not registered") from exc
