**State Machine Overview**

**Start State:** WAITING_FOR_TASK_INPUT — idle until user provides task input.

**Linear Flow:** PARSING_TASK -> SCOPING_AND_ASSUMPTIONS -> DECIDING_RESEARCH -> WEB_RESEARCH -> SOURCE_SELECTION -> EXTRACTING_SIGNALS -> INTEGRATING_FINDINGS -> OUTLINE_CHECKLIST_SKELETON -> DRAFTING_CHECKLIST -> DEEPENING_CHECKLIST -> NORMALIZING_CHECKLIST -> SELF_JUDGE -> GAP_ANALYSIS -> FINALIZING_CHECKLIST -> EMITTING_CHECKLIST

**Terminal Behavior:** After `EMITTING_CHECKLIST` the workflow completes and can return to `WAITING_FOR_TASK_INPUT` to accept a new task.

**Tool & Skill Mapping**

- `DECIDING_RESEARCH` may route to `WEB_RESEARCH` which triggers the external tool `TAVILY_SEARCH`.
- Most phases map deterministically to LLM-driven skills (see `src/architecture/domain.py` SkillName).

**Notable Transitions**

- `DECIDING_RESEARCH -> WEB_RESEARCH`: external tool invocation boundary.
- `SELF_JUDGE -> GAP_ANALYSIS`: branching point where the quality of the draft determines remediation.

**Recommendations**

- Make branching explicit: encode `GapRoute` outcomes (NEEDS_RESEARCH, NEEDS_DEPTH, READY) as explicit transitions in the DOT file so visual tools show remediation loops.
- Add timeouts and retry counts for `WEB_RESEARCH` tool calls to improve robustness.
- Consider adding states for error handling (e.g., `TOOL_ERROR`, `SKILL_ERROR`) to capture failures and allow safe retries.
- Provide a lightweight visual label for each node that includes the skill or tool name (useful when generating diagrams for stakeholders).

**Files added**

- File: [src/architecture/state_machine.dot](src/architecture/state_machine.dot)
- File: [src/architecture/state_machine.md](src/architecture/state_machine.md)
