from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Dict, Set

from typing_extensions import TypedDict

from langgraph.graph import END, StateGraph

from agent.context import Context
from architecture.domain import DecisionType, SkillName, ToolName
from engine.coordinator import Coordinator
from engine.executor import Executor
from llm.client import LLMClient
from memory.models import AgentState
from memory.state_manager import (
    apply_tavily_search_result,
    build_agent_response,
    create_initial_state,
    ingest_user_message,
    update_state_from_skill,
)
from prompting.renderer import PromptRenderer
from tools.models import SearchToolRequest, SearchToolResult
from tools.tavily_client import TavilySearchClient

TO_INTAKE = "__route_intake__"
TO_RESEARCH = "__route_research__"
TO_BUILD = "__route_build__"
TO_QUALITY = "__route_quality__"
TO_FINALIZE = "__route_finalize__"

INTAKE_SKILLS: Set[str] = {
    SkillName.PARSE_TASK.value,
    SkillName.SCOPE_AND_ASSUME.value,
    SkillName.DECIDE_RESEARCH.value,
}
RESEARCH_SKILLS: Set[str] = {
    SkillName.SOURCE_SELECTION.value,
    SkillName.EXTRACT_SIGNALS.value,
    SkillName.INTEGRATE_FINDINGS.value,
}
BUILD_SKILLS: Set[str] = {
    SkillName.OUTLINE_SKELETON.value,
    SkillName.DRAFT_CHECKLIST.value,
    SkillName.DEEPEN_CHECKLIST.value,
    SkillName.NORMALIZE_CHECKLIST.value,
}
QUALITY_SKILLS: Set[str] = {
    SkillName.SELF_JUDGE.value,
    SkillName.GAP_ANALYSIS.value,
}
FINALIZE_SKILLS: Set[str] = {
    SkillName.FINALIZE_CHECKLIST.value,
    SkillName.EMIT_CHECKLIST.value,
}


class GraphState(TypedDict, total=False):
    """Serialized state flowing through LangGraph."""

    agent_state: Dict[str, Any]
    agent_response: Dict[str, Any]
    decision: Dict[str, Any]
    user_message: str
    last_skill_output: Dict[str, Any]
    last_tool_output: Dict[str, Any]
    runtime_context: Dict[str, Any]


ToolRunner = Callable[[AgentState], SearchToolResult]
ToolHandler = Callable[[AgentState, SearchToolResult], AgentState]


def build_checklist_graph(context: Context | None = None):
    """Compiles the LangGraph that drives the checklist agent."""

    ctx = context or Context()
    renderer = PromptRenderer()
    llm_client = LLMClient.from_env()
    executor = Executor(llm_client, renderer)
    coordinator = Coordinator()
    tavily_client = TavilySearchClient(api_key=ctx.tavily_api_key or "")
    tavily_runner = _tavily_runner(tavily_client, ctx)

    graph = StateGraph(GraphState)

    graph.add_node("ingest_user_message", _ingest_node(ctx))
    graph.add_node("route_intake", _router_node(coordinator))
    graph.add_node("route_research", _router_node(coordinator))
    graph.add_node("route_build", _router_node(coordinator))
    graph.add_node("route_quality", _router_node(coordinator))
    graph.add_node("route_finalize", _router_node(coordinator))
    graph.add_node("emit_response", _emit_node())

    skill_nodes = {
        SkillName.PARSE_TASK: "parse_task",
        SkillName.SCOPE_AND_ASSUME: "scope_and_assume",
        SkillName.DECIDE_RESEARCH: "decide_research",
        SkillName.SOURCE_SELECTION: "source_selection",
        SkillName.EXTRACT_SIGNALS: "extract_signals",
        SkillName.INTEGRATE_FINDINGS: "integrate_findings",
        SkillName.OUTLINE_SKELETON: "outline_skeleton",
        SkillName.DRAFT_CHECKLIST: "draft_checklist",
        SkillName.DEEPEN_CHECKLIST: "deepen_checklist",
        SkillName.NORMALIZE_CHECKLIST: "normalize_checklist",
        SkillName.SELF_JUDGE: "self_judge",
        SkillName.GAP_ANALYSIS: "gap_analysis",
        SkillName.FINALIZE_CHECKLIST: "finalize_checklist",
        SkillName.EMIT_CHECKLIST: "emit_checklist",
    }

    tool_nodes = {
        ToolName.TAVILY_SEARCH: "tavily_search",
    }

    for skill, node_name in skill_nodes.items():
        graph.add_node(node_name, _skill_node(skill, executor))

    graph.add_node(
        tool_nodes[ToolName.TAVILY_SEARCH],
        _tool_node(
            ToolName.TAVILY_SEARCH,
            tavily_runner,
            apply_tavily_search_result,
        ),
    )

    graph.set_entry_point("ingest_user_message")
    graph.add_edge("ingest_user_message", "route_intake")

    graph.add_edge(skill_nodes[SkillName.PARSE_TASK], "route_intake")
    graph.add_edge(skill_nodes[SkillName.SCOPE_AND_ASSUME], "route_intake")
    graph.add_edge(skill_nodes[SkillName.DECIDE_RESEARCH], "route_research")

    graph.add_edge(tool_nodes[ToolName.TAVILY_SEARCH], "route_research")
    graph.add_edge(skill_nodes[SkillName.SOURCE_SELECTION], "route_research")
    graph.add_edge(skill_nodes[SkillName.EXTRACT_SIGNALS], "route_research")
    graph.add_edge(skill_nodes[SkillName.INTEGRATE_FINDINGS], "route_build")

    graph.add_edge(skill_nodes[SkillName.OUTLINE_SKELETON], "route_build")
    graph.add_edge(skill_nodes[SkillName.DRAFT_CHECKLIST], "route_build")
    graph.add_edge(skill_nodes[SkillName.DEEPEN_CHECKLIST], "route_build")
    graph.add_edge(skill_nodes[SkillName.NORMALIZE_CHECKLIST], "route_quality")

    graph.add_edge(skill_nodes[SkillName.SELF_JUDGE], "route_quality")
    graph.add_edge(skill_nodes[SkillName.GAP_ANALYSIS], "route_intake")
    graph.add_edge(skill_nodes[SkillName.FINALIZE_CHECKLIST], "route_finalize")
    graph.add_edge(skill_nodes[SkillName.EMIT_CHECKLIST], "emit_response")

    _attach_router(
        graph,
        "route_intake",
        INTAKE_SKILLS,
        {
            SkillName.PARSE_TASK.value: skill_nodes[SkillName.PARSE_TASK],
            SkillName.SCOPE_AND_ASSUME.value: skill_nodes[SkillName.SCOPE_AND_ASSUME],
            SkillName.DECIDE_RESEARCH.value: skill_nodes[SkillName.DECIDE_RESEARCH],
        },
        exclude_handoff=TO_INTAKE,
    )

    _attach_router(
        graph,
        "route_research",
        RESEARCH_SKILLS,
        {
            ToolName.TAVILY_SEARCH.value: tool_nodes[ToolName.TAVILY_SEARCH],
            SkillName.SOURCE_SELECTION.value: skill_nodes[SkillName.SOURCE_SELECTION],
            SkillName.EXTRACT_SIGNALS.value: skill_nodes[SkillName.EXTRACT_SIGNALS],
            SkillName.INTEGRATE_FINDINGS.value: skill_nodes[
                SkillName.INTEGRATE_FINDINGS
            ],
        },
        exclude_handoff=TO_RESEARCH,
    )

    _attach_router(
        graph,
        "route_build",
        BUILD_SKILLS,
        {
            SkillName.OUTLINE_SKELETON.value: skill_nodes[SkillName.OUTLINE_SKELETON],
            SkillName.DRAFT_CHECKLIST.value: skill_nodes[SkillName.DRAFT_CHECKLIST],
            SkillName.DEEPEN_CHECKLIST.value: skill_nodes[SkillName.DEEPEN_CHECKLIST],
            SkillName.NORMALIZE_CHECKLIST.value: skill_nodes[
                SkillName.NORMALIZE_CHECKLIST
            ],
        },
        exclude_handoff=TO_BUILD,
    )

    _attach_router(
        graph,
        "route_quality",
        QUALITY_SKILLS,
        {
            SkillName.SELF_JUDGE.value: skill_nodes[SkillName.SELF_JUDGE],
            SkillName.GAP_ANALYSIS.value: skill_nodes[SkillName.GAP_ANALYSIS],
        },
        exclude_handoff=TO_QUALITY,
    )

    _attach_router(
        graph,
        "route_finalize",
        FINALIZE_SKILLS,
        {
            SkillName.FINALIZE_CHECKLIST.value: skill_nodes[
                SkillName.FINALIZE_CHECKLIST
            ],
            SkillName.EMIT_CHECKLIST.value: skill_nodes[SkillName.EMIT_CHECKLIST],
        },
        exclude_handoff=TO_FINALIZE,
    )

    graph.add_edge("emit_response", END)
    return graph.compile()


def _attach_router(
    graph: StateGraph,
    node_name: str,
    local_skills: Set[str],
    local_routes: Dict[str, str],
    *,
    exclude_handoff: str,
) -> None:
    graph.add_conditional_edges(
        node_name,
        lambda state, bucket=local_skills: _route_from_decision(state, bucket),
        {
            **local_routes,
            **_handoff_routes(exclude=exclude_handoff),
            "__complete__": "emit_response",
            "__noop__": "emit_response",
        },
    )


def _handoff_routes(*, exclude: str) -> Dict[str, str]:
    routes = {
        TO_INTAKE: "route_intake",
        TO_RESEARCH: "route_research",
        TO_BUILD: "route_build",
        TO_QUALITY: "route_quality",
        TO_FINALIZE: "route_finalize",
    }
    routes.pop(exclude, None)
    return routes


def _ingest_node(context: Context):
    def _node(state: GraphState) -> GraphState:
        user_message = state.get("user_message")
        if not user_message:
            raise ValueError("user_message is required for each invocation")

        agent_state_dict = state.get("agent_state")
        if agent_state_dict:
            agent_state = AgentState.model_validate(agent_state_dict)
            agent_state = ingest_user_message(agent_state, user_message)
        else:
            agent_state = create_initial_state(user_message)

        new_state = deepcopy(state)
        new_state["agent_state"] = agent_state.model_dump()
        new_state["runtime_context"] = context.model_dump()
        return new_state

    return _node


def _router_node(coordinator: Coordinator):
    def _node(state: GraphState) -> GraphState:
        agent_state = _ensure_agent_state(state, "agent_state missing before routing")
        decision = coordinator.next_action(agent_state)
        new_state = deepcopy(state)
        new_state["agent_state"] = agent_state.model_dump()
        new_state["decision"] = decision.model_dump()
        return new_state

    return _node


def _skill_node(skill: SkillName, executor: Executor):
    def _node(state: GraphState) -> GraphState:
        agent_state = _ensure_agent_state(
            state, f"agent_state missing before running skill {skill.value}"
        )
        output = executor.run_skill(skill, agent_state)
        updated_state = update_state_from_skill(agent_state, skill, output)
        new_state = deepcopy(state)
        new_state["agent_state"] = updated_state.model_dump()
        new_state["last_skill_output"] = output.model_dump()
        return new_state

    return _node


def _tool_node(tool: ToolName, runner: ToolRunner, handler: ToolHandler):
    def _node(state: GraphState) -> GraphState:
        agent_state = _ensure_agent_state(
            state, f"agent_state missing before running tool {tool.value}"
        )
        result = runner(agent_state)
        updated_state = handler(agent_state, result)
        new_state = deepcopy(state)
        new_state["agent_state"] = updated_state.model_dump()
        new_state["last_tool_output"] = result.model_dump()
        return new_state

    return _node


def _emit_node():
    def _node(state: GraphState) -> GraphState:
        agent_state = _ensure_agent_state(state, "agent_state missing before emission")
        response = build_agent_response(agent_state)
        new_state = deepcopy(state)
        new_state["agent_state"] = agent_state.model_dump()
        new_state["agent_response"] = response.model_dump()
        return new_state

    return _node


def _route_from_decision(state: GraphState, local_skills: Set[str]) -> str:
    decision = _ensure_decision(state)
    if decision.get("decision_type") != DecisionType.LLM_SKILL.value:
        return decision.get("route_key", "__complete__")

    skill = decision.get("skill")
    if skill in local_skills:
        return skill
    return _categorize_skill(skill)


def _categorize_skill(skill: str | None) -> str:
    if skill in RESEARCH_SKILLS:
        return TO_RESEARCH
    if skill in BUILD_SKILLS:
        return TO_BUILD
    if skill in QUALITY_SKILLS:
        return TO_QUALITY
    if skill in FINALIZE_SKILLS:
        return TO_FINALIZE
    return TO_INTAKE


def _tavily_runner(client: TavilySearchClient, context: Context) -> ToolRunner:
    def _runner(agent_state: AgentState) -> SearchToolResult:
        request = _build_search_request(agent_state, context)
        task_id = agent_state.workflow.phase.value
        return client.search(request, task_id=task_id)

    return _runner


def _build_search_request(state: AgentState, context: Context) -> SearchToolRequest:
    questions = [q.strip() for q in state.working.research_questions if q.strip()]
    query = questions[0] if questions else ""
    follow_ups = questions[1:] if len(questions) > 1 else []

    if not query:
        if state.working.task_overview and state.working.task_overview.goal:
            query = state.working.task_overview.goal
        elif state.working.task_input:
            query = state.working.task_input
        else:
            query = "Checklist research task"

    return SearchToolRequest(
        query=query,
        follow_up_questions=follow_ups,
        max_results=context.tavily_max_results,
        search_depth=context.tavily_search_depth,
    )


def _ensure_agent_state(state: GraphState, error_message: str) -> AgentState:
    agent_state_dict = state.get("agent_state")
    if not agent_state_dict:
        raise ValueError(error_message)
    return AgentState.model_validate(agent_state_dict)


def _ensure_decision(state: GraphState) -> Dict[str, Any]:
    decision = state.get("decision")
    if not decision:
        raise ValueError("decision missing before routing")
    return decision


graph = build_checklist_graph(Context())
