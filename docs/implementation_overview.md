# BuildWise AI — Implementation Overview

What has been built, and how each layer connects to the next. Companion to
`file_structure.md` (what exists, file by file) and `gap_analysis.md` (what's
left, against the target flow diagram).

---

## 1. The layered architecture, end to end

```
Domain Models  (Pydantic, framework-independent)
      │
      ▼
Agent Contracts ──▶ Agent Registry ──▶ Agent Factory ──▶ native crewai.Agent
      │                                     ▲
      │                              resolves: LLM (ModelTier), tools (ToolRegistry),
      │                              skills (SKILL.md packages)
      ▼
Task Factories (native crewai.Task, one per specialist capability)
      │
      ▼
Crew Factories (native crewai.Crew — 4 business-facing Crews)
      │
      ▼
[NOT YET BUILT] CrewAI Flow — orchestrates the 4 Crews, owns state/routing/pause/persistence
      │
      ▼
[PARTIALLY BUILT] FastAPI — currently only health/ready/root; no consultation endpoints
```

Every layer only depends on the one below it. `domain/` never imports
`crewai`. `tasks/` never constructs an `Agent` or a `Crew`. `crews/` never
calls `.kickoff()`. This separation is deliberate and is enforced throughout
every PRD in `prds/`.

---

## 2. Domain layer — the shared vocabulary

`src/buildwise/domain/` holds every structured artifact the system produces,
as plain Pydantic v2 models inheriting from `BuildWiseModel`
(`extra="forbid"`, `validate_assignment=True`). Nothing here knows CrewAI
exists.

Each pipeline stage has a canonical root model:

| Stage | Root model | File |
|---|---|---|
| Discovery | `DiscoveryResult` | `discovery.py` |
| Product definition | `ProductDefinition` | `product.py` |
| Requirements | `RequirementsSpecification` | `requirements.py` |
| Market & GTM | `MarketAndGTMStrategy` | `market_and_gtm.py` |
| Solution architecture | `SolutionArchitecture` | `architecture.py` |
| AI architecture | `AIArchitecture` | `ai_architecture.py` |
| Security architecture | `SecurityArchitecture` | `security.py` |
| QA & evaluation | `QAEvaluationPlan` | `qa.py` |
| Lead review | `LeadReview` | `review.py` |
| Specialist selection | `SpecialistExecutionPlan` | `specialist_planning.py` |
| Product Planning aggregate | `ProductPlanningResult` | `product_planning.py` |
| Technical Planning aggregate | `TechnicalPlanningResult` | `technical_planning.py` |
| Final deliverable (models only) | `ProductBlueprint` | `blueprint.py` |

Most root models carry heavy `model_validator` logic: cross-reference
integrity (every `related_feature_ids` entry must exist in the artifact's own
`features` list), decision/rationale consistency (`decision="approved"` ⇒ no
open questions), and session ownership. Several also expose a **classmethod
ownership validator** for cross-*artifact* checks that a single model can't
self-verify — e.g. `ProductDefinition.validate_discovery_ownership(...)`,
`RequirementsSpecification.validate_product_ownership(...)`,
`SolutionArchitecture.validate_requirements_ownership(...)`,
`AIArchitecture.validate_architecture_ownership(...)`,
`MarketAndGTMStrategy.validate_product_ownership(...)`. These classmethods
are reused (not reimplemented) by the Tasks layer's guardrails.

The two **aggregate** models — `ProductPlanningResult` and
`TechnicalPlanningResult` — don't duplicate any fields; they hold references
to the real artifacts produced by their Crew's tasks, plus their own
session-ownership validation. `TechnicalPlanningResult` additionally exposes
`validate_specialist_selection(ai_selected=, security_selected=,
qa_selected=)`, a decoupled cross-check against a `SpecialistExecutionPlan`
performed *after* assembly.

`domain/__init__.py` wildcard-imports every submodule so `from
buildwise.domain import X` works package-wide; code inside `tasks/`/`crews/`
always imports from the specific submodule instead.

---

## 3. Agents layer — contracts → native CrewAI agents

`agents/base.py` defines `AgentContract`: role, goal, backstory,
responsibilities/exclusions, `ModelTier`, `AgentCapabilityPolicy` (which tool
keys / skill paths / knowledge paths / MCP keys / app keys it may use),
`AgentRuntimeSettings` (max_iter, reasoning, cache…), `AgentFailureBehavior`,
and `handoff_targets`. Nine such contracts exist (one per
`AgentType` enum value), registered in `agents/registry.py`'s
`AgentContractRegistry`, which validates registry-wide invariants (every
`AgentType` has a contract, handoff targets resolve to real agents, the four
always-required agents — Discovery Analyst, Product Manager, Business
Analyst, Lead Reviewer — are marked `REQUIRED`).

`agents/factory.py`'s `AgentFactory.create(AgentType.X)` is the only place a
native `crewai.Agent` gets constructed:

- **Model** — `ModelTier` → configured model name (`Settings.fast_model` /
  `primary_agent_model` / `architect_model` / `lead_reviewer_model`) → native
  `crewai.LLM`.
- **Tools** — `capabilities.tool_keys` → `tools/registry.py`'s
  `ToolRegistry.resolve_many(...)`, which lazily builds official CrewAI tools
  (`SerperDevTool`, `ScrapeWebsiteTool`, `GithubSearchTool`), raising
  immediately if a required credential (e.g. `SERPER_API_KEY`) is missing.
- **Skills** — `capabilities.skill_paths` (e.g. `"skills/product_manager"`)
  resolved relative to the `buildwise` package root (`src/buildwise/`, fixed
  during this work — it previously pointed at the repo root and broke every
  agent construction) and validated to actually contain `SKILL.md`.

Construction fails immediately and loudly on any missing credential, skill,
or provider config — there is no partial/degraded agent.

---

## 4. Tasks layer — native `crewai.Task` factories

Nine `create_<x>_task(...)` functions in `tasks/`, each returning a plain
`crewai.Task` with `output_pydantic=<RootModel>`. Two shared modules back all
nine:

- **`tasks/guardrails.py`** — deterministic, LLM-free validators matching
  CrewAI's native guardrail contract (`(TaskOutput) -> tuple[bool, Any]`,
  composed via `compose_guardrails(...)` into the `guardrails=[...]` list
  CrewAI already retries against, bounded by `guardrail_max_retries`):
  - `require_pydantic_output(Model)` — the output exists and is the right type
  - `require_non_empty_collections(Model, *fields)` — only used where the
    domain model itself has no `min_length` (e.g. `SecurityArchitecture`,
    `QAEvaluationPlan`, both plain `BaseModel`s with no cross-field
    validators of their own)
  - `run_domain_validator(fn)` — wraps one of the domain layer's own
    classmethod ownership validators, catching `ValueError`/`TypeError` and
    turning it into actionable guardrail feedback instead of duplicating the
    check
  - `require_review_consistency` — the Lead Review decision/
    `approved_for_blueprint`/revision-request consistency table
- **`tasks/revisions.py`** — `format_revision_instructions(RevisionRequest)`,
  appended to a task's description when the Flow reruns a Crew for a
  targeted fix rather than first-generation.

**Dual input mode.** Every task whose upstream artifact might come from
*inside the same Crew* (constructed together, before any kickoff) or from *a
different, already-completed Crew* accepts either:

```python
create_product_definition_task(agent=..., discovery_task=prior_task)        # same-Crew: native context=[...]
create_product_definition_task(agent=..., discovery_result=prior_value)     # cross-Crew: literal value + ownership guardrail
```

`market_and_gtm`, `ai_architecture`, `security_architecture`, and
`qa_evaluation` all needed this extended to *two or three* upstream
dependencies (see §5) to support the four-Crew topology — this was the one
real Tasks-layer change made during the Crew refactor, and it's additive:
existing cross-Crew callers are unaffected.

Ownership guardrails only apply in cross-Crew mode — in same-Crew mode the
real object doesn't exist yet at construction time (only the `Task`
reference does), so there's nothing to validate against until the Crew
actually runs.

---

## 5. Crews layer — 4 business Crews, no registry

`prds/crews_refactor_plan.md` replaced an earlier one-Crew-per-Agent layout
with four collaborative, business-meaningful Crews. `crews/__init__.py`
exports exactly these four factories (the Flow imports them explicitly —
BuildWise has one fixed business process, not a plugin system, so there's no
`CrewRegistry`):

**`create_discovery_crew`** — 1 agent (Product Discovery Analyst), 1 task.
Optional `clarification_context` for re-running after a clarification round.

**`create_product_planning_crew`** — Product Manager → Business Analyst →
optional Market & GTM Strategist, in that order, wired with native
`context=[...]`. Market & GTM *must* run last: `MarketAndGTMStrategy`
validates real `product_definition_id` and persona/feature references, which
can't exist before `ProductDefinition` and `RequirementsSpecification` do
(this ordering was a deliberate resolution of a conflict between the refactor
plan's diagram and the domain model's own ownership constraints). Bounded
`revision_requests: list[RevisionRequest]` are routed to only the task each
one targets. `assemble_product_planning_result(crew_output, session_id=)`
turns the executed `CrewOutput` into a `ProductPlanningResult` by matching
each task's `.pydantic` output *by type*.

**`create_technical_planning_crew`** — dynamically composes only the
specialists present in a `SpecialistExecutionPlan.recommendations`: Solution
Architect always first, then AI/Security/QA Architects conditionally, each
wired with `context=[...]` against exactly its real dependencies (Security
gets `[solution_task, ai_task]` when AI was selected, `[solution_task]`
otherwise; QA gets whichever of solution/AI/security actually ran). Rejects
construction if AI/Security/QA are selected without Solution Architecture
(they all depend on it inside the same Crew), and if the plan lists a
specialist twice. `assemble_technical_planning_result(...)` mirrors the
Product Planning assembler.

**`create_lead_review_crew`** — 1 agent (Lead Reviewer), 1 task, consuming
every required artifact plus whichever optional specialist artifacts were
selected (`None` when not — never treated as a failure) and prior
`revision_history` so it doesn't re-flag already-addressed issues.

All four use `Process.sequential`, `memory=False`, `cache=True`,
`verbose=settings.crewai_verbose` — no hierarchical process, no Crew memory
(Flow state is the canonical context store), matching the refactor plan's
explicit defaults.

---

## 6. Flow-layer building blocks (not yet an actual Flow)

`flows/state.py`'s `BuildWiseFlowState` is a complete session state machine:
`SessionStatus`/`SessionStage` with a validated `transition_to(...)`,
specialist execution tracking (`register_specialist`, `mark_specialist_running/
completed/failed`), clarification handling
(`request_clarification`/`receive_clarification_answers`), and terminal-state
validation (`mark_completed`/`mark_failed`). It's a plain Pydantic model, not
yet attached to any `crewai.Flow` subclass.

`flows/routing.py` holds pure, deterministic decision functions —
`route_after_discovery`, `route_after_clarification`,
`route_after_product_definition`, `route_after_requirements`,
`route_after_specialists`, `route_after_review`,
`route_after_blueprint_assembly` — each returning a `FlowRoute` StrEnum value,
plus `build_specialist_routing_plan(state)` / `apply_specialist_routing_plan(...)`,
today's version of "deterministic specialist planning" (it predates and
differs slightly from the newer `SpecialistExecutionPlan` model — see
`gap_analysis.md`).

`flows/smoke.py` is a trivial `Flow[SmokeFlowState]` proving `@start`/
`@listen` wiring works; it has no relationship to the real consulting flow.

**None of this is wired into an actual `crewai.Flow` subclass yet** — see
`gap_analysis.md` for what `consulting_flow.py` still needs.

---

## 7. Everything else

- **`api/`** — FastAPI routers for `/health`, `/ready`, `/api/v1` root only.
  `main.py` wires `RequestContextMiddleware`, structlog, and exception
  handlers (`domain/errors.py`). No consultation endpoints exist yet.
- **`config/settings.py`** — `pydantic-settings` `Settings`, env-driven
  (model names per tier, retry/iteration limits, cost/token budgets,
  `database_url`).
- **`persistence/database.py`** — a bare SQLAlchemy engine +
  `check_database_connection()`. No ORM models, tables, or repositories for
  sessions/artifacts/revision history exist yet.
- **`reporting/`, `validation/`** — empty stub packages for the future
  deterministic blueprint assembler and output validator.
- **`tests/`** — directory scaffolding only (`fixtures/`, `unit/`,
  `integration/`), no tests written.

See `gap_analysis.md` for the prioritized list of what's still needed to
reach the target flow in `BuildWise AI -final flow.drawio.png`.
