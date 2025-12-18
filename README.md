# AI Checklist Agent

[![CI](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml)
[![Integration Tests](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml)

This repository contains a deterministic LangGraph implementation of an AI Checklist Agent. The agent converts natural-language goals into actionable checklists, refines them through a short dialogue, persists the plan, tracks conversational progress, and produces a completion summary without relying on an external LLM.

<div align="center">
  <img src="./static/studio_ui.png" alt="Graph view in LangGraph studio UI" width="75%" />
</div>

The core logic lives in `src/agent/checklist_agent.py` and is orchestrated through `src/agent/graph.py`. Every invocation accepts a `user_message` plus any saved state, advances the workflow to the next phase, and responds with an `agent_response` containing the text to show the user.

## Getting Started

1. Install dependencies, along with the [LangGraph CLI](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/), which will be used to run the server.

```bash
cd path/to/your/app
pip install -e . "langgraph-cli[inmem]"
```

2. (Optional) Customize the code and project as needed. Create a `.env` file if you need to use secrets.

```bash
cp .env.example .env
```

3. Start the LangGraph Server.

```bash
langgraph dev
```

Each request must include a `user_message`. To continue the conversation, pass the prior state (the JSON result from the previous invocation), set `user_message` to the next user utterance, and invoke the graph again (e.g., via `graph.ainvoke` in Python or through LangGraph Studio). The agent responds through the `agent_response` field.

The agent persists finalized checklists and tracking updates under `checklists/` (ignored by git). Set the runtime context `storage_dir` to control where files land.

## Checklist Workflow

1. **Initialization** – converts the initial description into an actionable checklist and surfaces up to three targeted clarification questions.
2. **Refinement** – ingests answers or additional edits, updating the checklist until the user approves.
3. **Persistence** – saves the approved checklist (tasks, timestamps, clarifications, and conversation log) to JSON.
4. **Tracking** – listens for natural-language updates such as “completed item 2” or “add a stakeholder review,” updating the stored checklist each time.
5. **Summary** – once every item is complete, the agent automatically generates a completion recap using the checklist state and progress log.

## Deterministic LangGraph Architecture

The implementation inside `src/agent/graph.py` mirrors the state diagram shared in the issue. Each phase in the diagram (ParsingTask → ScopingAndAssumptions → … → EmittingChecklist) maps to a dedicated LangGraph node that triggers a declarative LLM skill.

- **Coordinator** (`src/engine/coordinator.py`) inspects `AgentState.workflow.phase` and returns a `Decision` pointing to the appropriate skill.
- **Executor** (`src/engine/executor.py`) renders the Jinja template for that skill, calls the structured-output LLM client, and hands the response to the memory layer.
- **Memory** (`src/memory/state_manager.py`) deep-copies `AgentState`, stores the structured output, advances the workflow flag, and records the conversational turn.
- **Skills + Templates** (`src/skills` and `src/prompting`) keep prompts/data schemas declarative, ensuring the LLM never controls the routing logic.

The LangGraph keeps looping through `decide_next -> skill_node` until the Coordinator returns `DecisionType.COMPLETE`, after which it emits a final `AgentResponse`. Because every node is phase-specific, LangGraph Studio shows a readable trail of how the checklist evolved.

### Programmatic usage

```python
from agent.checklist_agent import ChecklistAgent

agent = ChecklistAgent()
result = agent.invoke("Plan a zero-downtime database migration for a fintech API")

print(result["agent_response"]["message"])
```

Persist the returned `agent_state` between invocations if you want to resume the same workflow with follow-up user input.

## How to customize

1. **Define runtime context**: Modify the `Context` class in the `graph.py` file to expose the arguments you want to configure per assistant. The template ships with a `storage_dir` field so you can control where finalized checklists and tracking logs are written for each run. For more information on runtime context in LangGraph, [see here](https://langchain-ai.github.io/langgraph/agents/context/?h=context#static-runtime-context).

2. **Extend the graph**: The core logic of the application is defined in [graph.py](./src/agent/graph.py). You can modify this file to add new nodes, edges, or change the flow of information.

## Development

While iterating on your graph in LangGraph Studio, you can edit past state and rerun your app from previous states to debug specific nodes. Local changes will be automatically applied via hot reload.

Follow-up requests extend the same thread. You can create an entirely new thread, clearing previous history, using the `+` button in the top right.

For more advanced features and examples, refer to the [LangGraph documentation](https://langchain-ai.github.io/langgraph/). These resources can help you adapt this template for your specific use case and build more sophisticated conversational agents.

LangGraph Studio also integrates with [LangSmith](https://smith.langchain.com/) for more in-depth tracing and collaboration with teammates, allowing you to analyze and optimize your chatbot's performance.
