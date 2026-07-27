# BuildWise AI — Gap Analysis vs. Target Flow

Walks `BuildWise AI -final flow.drawio.png` node by node against the current
codebase. Legend: ✅ Built · 🟡 Partial (real logic exists but incomplete) ·
🔴 Missing (nothing built yet).

```
Actor → Frontend → FastAPI validation → BuildWise CrewAI Flow
  → Discovery Crew → DiscoveryResult → Completeness Router
      ├─ clarification required → pause / frontend / answers / resume ─┐
      └─ complete → Early Market Router                                │
  → Product Planning Crew (Market&GTM optional, PM, BA)                │
  → Deterministic Specialist Planner                                   │
  → Technical Planning Crew (Solution, AI/Security/QA optional)        │
  → Cost Aggregator                                                    │
  → Lead Review Crew                                                   │
      ├─ approved → blueprint → Output validation                      │
      │     → Deterministic Blueprint Generator → Final Report → Frontend
      └─ revisions → rerun affected planning Crew ───────────────────┘
```

---

## Node-by-node status

| Diagram node | Status | Notes |
|---|---|---|
| Actor / Frontend | N/A | No frontend in this repository; out of scope here |
| FastAPI validation | 🟡 Partial | App + `/health`, `/ready`, `/api/v1` exist (`api/router.py`). **No consultation endpoints** — no `POST` to submit a product idea, no clarification-answer endpoint, no session/result retrieval |
| BuildWise CrewAI Flow | 🔴 Missing | `flows/consulting_flow.py` does not exist. Building blocks do: `BuildWiseFlowState` (state.py), routing functions (routing.py) |
| Discovery Crew | ✅ Built | `crews/discovery.py` + `tasks/discovery.py` |
| DiscoveryResult | ✅ Built | `domain/discovery.py` |
| Completeness Router | 🟡 Partial | `route_after_discovery(state)` implements the decision logic, but isn't wired to a live `@router`-decorated Flow method yet |
| Clarification loop (pause/frontend/answers/resume) | 🔴 Missing | `BuildWiseFlowState.request_clarification()` / `.receive_clarification_answers()` encode the *state transitions*; nothing pauses a real Flow, no endpoint accepts answers, no resume wiring |
| Early Market Router | 🟡 Partial | `SpecialistPlanner.should_include_early_market_context(discovery, ...)` (`planning/planner.py`, delegating to `planning/policies.py`) implements the deterministic `include_market_and_gtm: bool` decision from structured Discovery signals (specialist signals, market/business risk, weakly-defined-market unknowns) plus explicit request/exclusion. Not yet called by anything live — no Flow exists to call it before constructing the Product Planning Crew |
| Product Planning Crew | ✅ Built | `crews/product_planning.py`, incl. `assemble_product_planning_result` → `ProductPlanningResult` |
| Deterministic Specialist Planner | ✅ Built | `src/buildwise/planning/` (`policies.py`, `execution_graph.py`, `planner.py`) implements `SpecialistPlanner.create_execution_plan(...) -> SpecialistExecutionPlan` per `prds/05_specialist_planner.md`: pure Python, no CrewAI/LLM/DB, full unit + integration coverage (62 tests, `tests/unit/planning/`, `tests/integration/planning/`). Consumed successfully by `create_technical_planning_crew` in tests. **Not yet wired into a live Flow** — same root cause as "BuildWise CrewAI Flow" below, since `flows/consulting_flow.py` doesn't exist yet |
| Technical Planning Crew | ✅ Built | `crews/technical_planning.py`, incl. `assemble_technical_planning_result` → `TechnicalPlanningResult` |
| Cost Aggregator | 🔴 Missing | `UsageRecord`/`UsageSummary` models exist (`domain/usage.py`); nothing sums CrewAI per-Crew usage metrics into a session total |
| Lead Review Crew | ✅ Built | `crews/lead_review.py` + `tasks/lead_review.py` |
| approved → blueprint | 🟡 Partial | `route_after_review(revision_required, approved)` exists but takes plain booleans, not the real `LeadReview.decision` enum end-to-end through a live Flow |
| revisions → rerun affected planning Crew | 🔴 Missing | No logic maps a `RevisionTarget` (`product_definition`, `requirements`, `market_and_gtm`, `solution_architecture`, `ai_architecture`, `security_architecture`, `qa_and_evaluation`) to *which* Crew to rerun, nor enforces `maximum_specialist_revisions` |
| Output validation | 🔴 Missing | `validation/__init__.py` is an empty stub package |
| Deterministic Blueprint Generator | 🔴 Missing | `reporting/__init__.py` is empty. `ProductBlueprint`/`BlueprintSection` models exist (`domain/blueprint.py`) with no assembler |
| Final Report / Frontend | 🔴 Missing | Depends on the blueprint generator above |
| Persistence (implicit, cross-cutting) | 🟡 Partial | `persistence/database.py` is a bare engine + connectivity check — **no ORM models, no tables, no repositories** for sessions, artifacts, or revision history |

---

## What's actually needed next, in build order

### 1. ✅ Done — Deterministic Specialist Planner — `src/buildwise/planning/`
Built per `prds/05_specialist_planner.md`: `SpecialistPlanner.create_execution_plan(discovery, product_planning, limits, explicitly_requested, explicitly_excluded) -> SpecialistExecutionPlan`
in `planner.py`, backed by pure selection rules in `policies.py` (Solution
always required; AI/Security/QA selected from structured capability,
requirement, and risk signals; a coarse budget policy that trims optional
specialists in a fixed priority order and never silently drops a
safety-critical one) and a small fixed dependency-graph builder/validator in
`execution_graph.py`. `SpecialistPlanner.should_include_early_market_context(discovery, ...)`
covers the smaller **Early Market Router** decision in the same module, as
the PRD requires.

While implementing this, `flows/routing.py::build_specialist_execution_plan`
(the "different, older model" this section used to point at — it turned out
to target the *same* `SpecialistExecutionPlan`, not a separate
`SpecialistRoutingPlan`) was found to unconditionally force-include Market &
GTM into the *technical* plan, contradicting the PRD's explicit rule that
Market & GTM belongs only to the Product Planning Crew and must never be
reselected during technical planning. That function and its
`_evaluate_ai_architect`/`_evaluate_security_architect`/`_evaluate_qa_architect`
helpers were dead code (nothing outside `routing.py` called them, since no
Flow exists yet) and have been deleted; `route_after_specialist_planning`/
`route_after_specialists` now require only `SOLUTION_ARCHITECTURE`.

**Residual gap:** nothing calls `SpecialistPlanner` yet — that wiring is
explicitly scoped to step 3 below (`flows/consulting_flow.py`), matching the
PRD's own implementation order (its step 8, "wire planner into
consulting_flow.py later").

### 2. Persistence schema — `src/buildwise/persistence/`
SQLAlchemy ORM models (or a document-style JSON-column approach) for
`ConsultingSession`, the serialized `BuildWiseFlowState`, and revision
history, plus repository functions. Every PRD assumes the Flow "persists
validated artifacts" — there's currently nowhere to put them.

### 3. `flows/consulting_flow.py` — the actual orchestrator
Build a `Flow[BuildWiseFlowState]` subclass wiring `@start`/`@listen`/
`@router` methods to the existing `routing.py` functions and the four Crew
factories. Installed CrewAI (1.15.5) already provides native mechanisms for
the hardest parts — use them instead of custom equivalents:
  - **Routing**: `@router(previous_method)` returning route-name strings,
    plus `and_()`/`or_()` for multi-predecessor listens — matches the
    `FlowRoute` StrEnum already defined in `routing.py`.
  - **Human-in-the-loop clarification**: `@human_feedback(...)` and
    `Flow.ask(...)` with a pluggable `InputProvider`/`HumanFeedbackProvider`
    (including a non-blocking `HumanFeedbackPending` mode for
    webhook/async-resume patterns) — this is the "pause / frontend / answers
    / resume" loop in the diagram; no custom pause mechanism should be built.
  - **State persistence across pause/resume**: `@persist(FlowPersistence)` —
    CrewAI ships `SQLiteFlowPersistence`; a Postgres-backed implementation of
    the `FlowPersistence` ABC would plug in directly once step 2 exists.
  - **Concurrency**: Crew-level, decided by the Flow (e.g. Market & GTM
    running alongside Technical Planning) — not inside any single Crew.

### 4. Revision routing
A small deterministic mapping from `RevisionTarget` to "rerun Product
Planning Crew" vs "rerun Technical Planning Crew" (with the dependency-aware
subset described in `crews_refactor_plan.md` §11: reviving Solution
Architecture must cascade to AI/Security/QA if they depend on it; reviving
just QA must not). Bounded by `BuildWiseFlowState.limits.maximum_specialist_revisions`
(already modeled, not yet enforced anywhere live).

### 5. Cost Aggregator
Deterministic, Flow-owned: collect CrewAI's per-Crew `UsageMetrics` after
each `kickoff()` into `UsageSummary` (already modeled in `domain/usage.py`).
No new cost-calculation logic needed — just aggregation.

### 6. Output validation — `src/buildwise/validation/`
The Flow-side check described in every Crew PRD: reject a "successful"
`CrewOutput` when `.pydantic` is `None`, the wrong type, or fails ownership —
largely already covered by the same `run_domain_validator`/
`require_pydantic_output` machinery in `tasks/guardrails.py`, but the Flow
still needs one more pass after assembling `ProductPlanningResult`/
`TechnicalPlanningResult`/`LeadReview` before persisting them.

### 7. Deterministic Blueprint Generator — `src/buildwise/reporting/`
Consume the approved aggregates + `LeadReview`, produce a `ProductBlueprint`
(model already exists), render Markdown. No LLM call needed per the PRDs
unless deterministic assembly proves unreadable later.

### 8. Consultation API endpoints — `src/buildwise/api/v1/`
`POST` to start a consultation (kicks off the Flow), `POST` to submit
clarification answers (resumes it), `GET` to poll status/result. These call
into the Flow built in step 3 and the persistence layer built in step 2.

---

## Smaller loose ends

- ~~`flows/routing.py`'s `SpecialistRoutingPlan` and
  `domain/specialist_planning.py`'s `SpecialistExecutionPlan` are two
  different models...~~ **Resolved.** There was only ever one model
  (`SpecialistExecutionPlan`); `routing.py` held a second, buggy
  implementation of the selection *rules* targeting that same model. It has
  been removed in favor of `src/buildwise/planning/` (see step 1 above).
- Tests now exist for the planning module (`tests/unit/planning/`,
  `tests/integration/planning/`, 62 tests, no live LLM calls) plus shared
  fixture builders in `tests/fixtures/planning.py` for the heavily
  cross-validated `DiscoveryResult`/`ProductPlanningResult` graph. Everywhere
  else (`tests/unit/`, `tests/integration/` outside `planning/`) is still
  empty scaffolding — every other PRD's testing section still describes what
  to cover once the Flow lands.
- The planner's budget policy is intentionally coarse per the PRD (no exact
  token/dollar estimation): it only reads
  `FlowRuntimeLimits.maximum_agent_executions` and
  `.maximum_estimated_cost_usd`. `.maximum_session_tokens`,
  `.maximum_tool_calls`, and `.maximum_execution_seconds` are modeled but
  unused by the planner (by design — they're runtime guards for actual Crew
  execution, not pre-execution selection policy) and remain unenforced
  anywhere live, same as noted under Cost — Session budget controls below.
- `reporting/` and `validation/` currently contain only a one-line docstring
  each (`"""Blueprint assembly and rendering."""` /
  `"""Deterministic and model-assisted validation."""`) — no code yet; first
  real content in either will define their shape.

---

# PRD Alignment — `prd.md` vs. current implementation

The section above tracks the target *flow diagram*. This section tracks the
PRD document itself (`prd.md`) line by line: Functional/Non-Functional
Requirements, the Agents roster, the CrewAI feature checklist, and the Final
Output shape. Same legend: ✅ Built · 🟡 Partial · 🔴 Missing.

## Functional Requirements

| PRD ID | Requirement | Status | Evidence |
|---|---|---|---|
| FR1 | Accept vague ideas | 🟡 Partial | `domain/intake.py` models (`ProductIdeaRequest`, `ValidatedProductIdea`) and the Discovery Crew (`crews/discovery.py`) can process one, but there is no live endpoint to submit one — `api/v1/router.py` only exposes the API root |
| FR2 | Generate dynamic questions | 🟡 Partial | `DiscoveryResult`/`ClarificationQuestionSet` (`domain/discovery.py`) and Discovery Crew tasks (`tasks/discovery.py`) generate these at the Crew level, but nothing wires this into a running, resumable session |
| FR3 | Pause and resume sessions | 🔴 Missing | `BuildWiseFlowState.request_clarification()` / `.receive_clarification_answers()` model the *state transitions* only; no live `Flow`, no `@human_feedback`, no persistence, no endpoint actually pauses/resumes anything (matches the flow-diagram gap above) |
| FR4 | Select specialists dynamically | 🟡 Partial | The deterministic planner (`src/buildwise/planning/`) is fully built, tested, and its `SpecialistExecutionPlan` output is consumed by `create_technical_planning_crew` — the selection *policy* is done. Still 🟡 for the requirement as a whole because no live Flow calls it yet; a real consultation cannot dynamically select specialists end-to-end until `flows/consulting_flow.py` exists |
| FR5 | Generate product blueprint | 🔴 Missing | `ProductBlueprint`/`BlueprintSection` models exist (`domain/blueprint.py`); `reporting/__init__.py` is an empty stub — no assembler produces one |
| FR6 | Support markdown export | 🔴 Missing | `ProductBlueprint.generated_markdown` is a required field in the model, but nothing populates it since no generator exists |
| FR7 | Provide execution tracing | 🟡 Partial | HTTP-level request tracing exists (`observability/context.py`, `observability/middleware.py`, `X-Request-ID`); no CrewAI-native Crew/Flow tracing or per-session trace persisted, since no live Flow runs Crews yet |

## Non-Functional Requirements

| PRD requirement | Status | Evidence |
|---|---|---|
| Performance: < 2 minutes end-to-end | 🔴 Not verifiable | No live orchestrator exists to run end-to-end and measure against |
| Reliability: partial specialist failures shouldn't fail the whole workflow | 🟡 Partial | `SpecialistExecutionState` models per-specialist `failed`/retry semantics (`flows/state.py`) cleanly, but nothing yet catches a real Crew failure and keeps the Flow going, because the Flow doesn't run |
| Security — Prompt Injection Protection | 🔴 Missing | No sanitization or prompt-injection defenses found anywhere in `tasks/` or `domain/intake.py`; input is only Pydantic-schema-validated, not adversarially screened |
| Security — Tool Restrictions | ✅ Built | `tools/registry.py` exposes a small, explicit `ToolKey` whitelist (`web_search`, `web_scraper`, `github_search`) with per-tool env-var gating; agents can only request tools by these keys |
| Security — Input Validation | 🟡 Partial | Strong Pydantic validation exists on all domain models (`domain/intake.py`, etc.), but there is no live endpoint yet accepting raw external input for that validation to guard |
| Cost — Session budget controls | 🟡 Partial | `FlowRuntimeLimits` (`flows/state.py`) models `maximum_session_tokens`, `maximum_estimated_cost_usd`, `maximum_agent_executions`, `maximum_tool_calls`, `maximum_specialist_revisions` — none of it is enforced anywhere live, since there is no running Flow and no Cost Aggregator |

## Agents

| PRD role | Type | Status | Evidence |
|---|---|---|---|
| Discovery Analyst | Core | ✅ Built | `agents/product_discovery_analyst.py`, `invocation_mode=REQUIRED` |
| Product Manager | Core | ✅ Built | `agents/product_manager.py`, `invocation_mode=REQUIRED` |
| Business Analyst | Core | ✅ Built | `agents/business_analyst.py`, `invocation_mode=REQUIRED` |
| Solution Architect | Core (per PRD) | 🟡 Misaligned | Contract exists (`agents/solution_architect.py`) but is registered with `invocation_mode=CONDITIONAL`, not `REQUIRED` — the registry's `_validate_required_agent_set()` does **not** include it in the core set. PRD lists it as Core; code treats it as Conditional |
| Lead Reviewer | Core | ✅ Built | `agents/lead_reviewer.py`, `invocation_mode=REQUIRED` |
| Market Analyst | Conditional | ✅ Built (renamed) | `agents/market_and_gtm_strategist.py` — same role, different key (`market_and_gtm_strategist`) |
| AI Architect | Conditional | ✅ Built | `agents/ai_architect.py` |
| Security Architect | Conditional | ✅ Built | `agents/security_architect.py` |
| QA Architect | Conditional | ✅ Built (renamed) | `agents/qa_evaluation_architect.py` — same role, different key |
| Engineering Lead | Conditional | 🔴 Missing | No agent contract, no `AgentType` enum value, no task/crew references this role anywhere in the codebase |

## CrewAI Features Utilized

| PRD claims | Status | Evidence |
|---|---|---|
| Flows | 🔴 Missing | Only `flows/smoke.py` (a trivial test `Flow`) exists; the real orchestrator (`flows/consulting_flow.py`) is not built |
| Crews | ✅ Built | Four real Crews: `crews/discovery.py`, `crews/product_planning.py`, `crews/technical_planning.py`, `crews/lead_review.py` |
| Human Feedback | 🔴 Missing | No use of CrewAI's `@human_feedback` / `Flow.ask()` anywhere; only state-shape modeling in `flows/state.py` |
| Structured Outputs | ✅ Built | `TaskOutput.pydantic` enforced pervasively via `tasks/guardrails.py::require_pydantic_output` and friends |
| Tool Usage | ✅ Built | `tools/registry.py` wraps official CrewAI tools (`SerperDevTool`, `ScrapeWebsiteTool`, `GithubSearchTool`) |
| Parallel Execution | 🔴 Missing | No orchestration exists yet to run any Crews concurrently (e.g., Market & GTM alongside Technical Planning) |
| Tracing | 🟡 Partial | HTTP-request tracing only (`observability/middleware.py`); no CrewAI-native Crew/Flow trace capture |
| Reflection Loops | 🟡 Partial | Task-level retry loops exist via CrewAI's `guardrail_max_retries` pattern (`tasks/guardrails.py`); the higher-level "Lead Review requests revision → rerun specialist Crew" loop from the PRD is not wired since the Flow doesn't exist |
| Dynamic Routing | 🟡 Partial | `flows/routing.py` defines the routing *decision functions* (`route_after_discovery`, `route_after_review`, etc.) but none are wired to a live `@router`-decorated Flow method |

## Final Output — Product Blueprint sections

PRD specifies 12 sections; the actual `BlueprintSectionType` enum
(`domain/enums.py`) defines 16. No assembler exists yet to populate any of
them (see FR5/FR6 above) — this table compares model *shape* only.

| PRD section | Status | Codebase equivalent |
|---|---|---|
| 1. Problem Statement | 🟡 Renamed/unclear | No `problem_statement` enum value; closest is `PRODUCT_VISION` or `EXECUTIVE_SUMMARY` |
| 2. Users | ✅ Built | `USERS_AND_PERSONAS` |
| 3. Market Insights | ✅ Built (renamed) | `MARKET_AND_GTM` |
| 4. Requirements | ✅ Built | `REQUIREMENTS` |
| 5. Architecture | ✅ Built | `SOLUTION_ARCHITECTURE` |
| 6. AI Design | ✅ Built | `AI_ARCHITECTURE` |
| 7. Security | ✅ Built | `SECURITY_ARCHITECTURE` |
| 8. Evaluation | ✅ Built | `QA_AND_EVALUATION` |
| 9. Risks | ✅ Built (merged) | `RISKS_AND_ASSUMPTIONS` (combined with Assumptions) |
| 10. Delivery Roadmap | ✅ Built | `ROADMAP` |
| 11. Open Questions | 🔴 Missing | No matching enum value or model field; `ProductBlueprint.limitations` is not the same concept |
| 12. Final Recommendation | 🟡 Different shape | `ProductBlueprint.recommendations: list[str]` exists as a top-level field, not as a `BlueprintSectionType` section |
| *(not in PRD)* | Extra | Codebase also defines `FEATURES_AND_SCOPE`, `USER_JOURNEYS`, `COSTS`, `IMPLEMENTATION_GUIDANCE`, `LIMITATIONS` — finer-grained than the PRD's 12 sections |

## Key misalignments to resolve

1. **Solution Architect core/conditional mismatch** — PRD lists it as a Core
   (always-run) agent; the registry enforces it as Conditional. The
   deterministic Specialist Planner (item 1 in the build order above) has
   already made its own call — it always selects
   `SpecialistType.SOLUTION_ARCHITECTURE` as `required=True` and rejects any
   attempt to exclude it — but `agents/registry.py`'s
   `_validate_required_agent_set()` still doesn't include it among the core
   agents. These two now disagree; reconcile the registry to match the
   planner (or vice versa) before wiring either into a live Flow.
2. **"Engineering Lead" agent is entirely unbuilt** — no contract, enum
   value, task, or Crew reference exists. Needs a PRD-vs-scope decision: build
   it, or update `prd.md` to drop it.
3. **Prompt Injection Protection is unimplemented** — the PRD calls it out
   explicitly under Security, and nothing in `tasks/` or `domain/intake.py`
   addresses it beyond standard Pydantic schema validation.
4. **"Open Questions" has no home** in the current blueprint model — every
   other PRD section maps onto an existing `BlueprintSectionType` (sometimes
   renamed/merged); this one doesn't.

---

# Architecture Contract Alignment — `docs/architecture/*.md` vs current implementation

This section checks the codebase against the two runtime-architecture
contracts: `docs/architecture/crewai_runtime_architecture.md` (status:
Accepted, v1.0) and `docs/architecture/full_architecture_flow.md`. Same
legend: ✅ Built · 🟡 Partial · 🔴 Missing.

These two documents are themselves not fully consistent with each other, or
with `prds/05_specialist_planner.md` (the PRD actually implemented for the
Specialist Planner). Those cross-document conflicts are called out
explicitly below rather than silently resolved in the implementation's
favor — a decision is needed on which document is authoritative before any
further alignment work.

## Orchestration layering

| Contract element | Status | Notes |
|---|---|---|
| Flow-first orchestration (Flows own routing/state/pause-resume/specialist selection) | 🔴 Missing | Principle is sound and the building blocks exist (`flows/state.py`, `flows/routing.py`), but no `Flow` subclass runs any of it — same root cause tracked throughout this document |
| Application Service Layer (`full_architecture_flow.md` §3: Session Service, Flow Execution Service, Human Feedback Service, Blueprint Service, Usage and Cost Service, Validation Service, Guardrail Service, Tool Execution Service) | 🔴 Missing | No `application/` package exists at all (not even empty) — `crewai_runtime_architecture.md` §24.1 talks about an *existing* `application/` package to inspect/migrate, but the current repo has none. Either that section is stale or the package was already removed |
| JSON-first Crew standard (`crewai_runtime_architecture.md` §22, §25: `crews/<name>/crew.jsonc` + `agents/<name>.jsonc`, loaded by a shared Python loader) | 🔴 Missing / diverged | The actual implementation is 100% Python: `crews/*.py` factory functions (`create_discovery_crew`, `create_product_planning_crew`, etc.), `tasks/*.py`, and `agents/*.py` contract modules (`agents/base.py::AgentContract`, `agents/registry.py`, `agents/factory.py`). No `.jsonc` file exists anywhere in `src/`. This is a foundational, repo-wide structural choice that contradicts the contract's canonical folder tree — needs an explicit decision to update the contract or migrate the code |
| Final folder structure (`crewai_runtime_architecture.md` §22) | 🟡 Diverged | Beyond the JSON-first Crew point above: `infrastructure/` exists as a directory but is completely empty (no `__init__.py`, no `llm.py`/`clock.py`); `knowledge/` is empty (no `README.md`, no `product/`/`architecture/`/etc. subdirs); `observability/` has `context.py` + `middleware.py`, not the target's `events.py`/`tracing.py`/`usage.py`; `tools/` has no `policies.py` or `research/`; `flows/` has no `persistence.py` or `guardrails.py` (guardrails currently live in `tasks/guardrails.py` instead); domain module names differ from the target list (`market_and_gtm.py` vs. target `market.py`, `qa.py` vs. target `qa_evaluation.py`) and the domain package has grown several modules the contract's tree doesn't mention (`product_planning.py`, `technical_planning.py`, `specialist_planning.py`, `agent.py`, `api.py`) — a natural result of the Crew-refactor work happening after this contract was written |
| Crews are focused single-outcome units | ✅ Built | The four real Crews (`discovery`, `product_planning`, `technical_planning`, `lead_review`) each match this principle in spirit even though they aren't JSON-defined |
| Sequential process by default, no hierarchical Crews | ✅ Built | All four Crew factories pass `process=Process.sequential`; nothing uses hierarchical execution |

## Specialist roster & selection-timing conflicts

| Conflict | `crewai_runtime_architecture.md` | `full_architecture_flow.md` | `prds/05_specialist_planner.md` (implemented) | Status |
|---|---|---|---|---|
| Market & GTM Strategist selection | §6.6: **"Always included"** alongside Solution Architect and Lead Reviewer, decided in the same specialist-planning stage as AI/Security/QA | Conditional (`MARKET_DECISION` node), decided in the *same* single "Specialist Planning" stage as AI/Security/QA/Engineering Lead — no separate early stage | Conditional, decided by a **separate, earlier** `should_include_early_market_context()` policy *before* the Product Planning Crew is built, and explicitly **forbidden** from ever appearing in the later Technical Planning `SpecialistExecutionPlan` | 🔴 Three-way conflict | The implementation (`src/buildwise/planning/`) follows the third model. It also fixed a bug where `flows/routing.py`'s old code literally implemented the first model (force-including Market & GTM as `required=True` in the *technical* plan) — see build-order item 1 above. All three documents need to agree on one timing model |
| "Engineering Lead" specialist | §8 Agent Responsibility Matrix does **not** list Engineering Lead at all | Lists it as a full conditional specialist with its own routing rule (`ENGINEERING_DECISION`) and deliverables (delivery plan, dependencies, complexity, maintainability, tech debt, team skills) | `SpecialistType` enum has exactly 5 members (Market & GTM, Solution, AI, Security, QA) — **no Engineering Lead**, matching `prd.md`'s gap noted above but contradicting `full_architecture_flow.md` | 🔴 Conflict | Same underlying gap as "Key misalignments" item 2 above, now sourced from a second document. No `AgentType`/`SpecialistType` enum value, contract, task, or Crew exists for it anywhere |
| Solution Architect invocation mode | Implicitly "always runs" (`full_architecture_flow.md` diagram: "Always Runs") | Same | Planner always selects it with `required=True` and rejects exclusion | ✅ Agreement | All three agree Solution Architect is mandatory; only `agents/registry.py`'s `invocation_mode=CONDITIONAL` disagrees (see "Key misalignments" item 1) |

## Security & guardrail depth

| Contract requirement | Status | Notes |
|---|---|---|
| Semantic input validation / prompt-injection detection / secret detection as explicit pre-acceptance pipeline stages (`full_architecture_flow.md` §7–9: "Prompt Injection Check", "Secret Detection", 12-item AI-security threat list including indirect injection via web results, hidden instruction attacks, cross-session leakage) | 🔴 Missing | Confirmed no implementation anywhere in `tasks/`, `domain/intake.py`, or `api/`; only Pydantic schema validation exists. This is the same gap as "Key misalignments" item 3, now specified in much more detail by both new documents — including the principle "all user input, external content, and tool output must be treated as untrusted data", which nothing currently enforces |
| Tool definitions require purpose, allowed users/operations, input constraints, output schema, timeout, retry policy, rate limit, side-effect classification, sensitive-data policy, logging policy, failure behavior (`crewai_runtime_architecture.md` §10) | 🟡 Partial | `tools/registry.py::ToolRegistry` implements the default-deny key allowlist and per-tool env-var gating (§10.1) cleanly, but none of the other governance fields exist as structured policy — there's no `tools/policies.py`, no timeout/retry/rate-limit config per tool, no tool-output sanitization or untrusted-content handling |
| Tool output must pass a security/injection guardrail before being used by a specialist (`full_architecture_flow.md` diagram: `TOOL_OUTPUT_GUARDRAIL`) | 🔴 Missing | No such guardrail exists; tool results returned by `ToolRegistry.resolve_many()` flow directly into the agent with no intermediate check |
| Deterministic + LLM guardrail split (`crewai_runtime_architecture.md` §17) | 🟡 Partial | Deterministic guardrails exist and are used extensively (`tasks/guardrails.py::require_pydantic_output` and friends); no LLM-based subjective guardrails (clarity, coherence, vague-recommendation detection) exist yet, and the doc's specific "one repair attempt then mark partial" pattern isn't implemented — current guardrails retry then fail the task rather than continuing with a partial/degraded result |

## Operational infrastructure

| Contract requirement | Status | Notes |
|---|---|---|
| Docker (multi-stage build, non-root user, health check, production ASGI server, `.dockerignore`, pinned deps) | ✅ Built | `Dockerfile` matches the spec closely: multi-stage `python:3.12-slim` build, non-root `buildwise` user, `HEALTHCHECK` hitting `/health`, `uv`-pinned deps. `docker-compose.yml` wires a Postgres service too. Not previously credited anywhere in this document |
| CI (GitHub Actions: Ruff, mypy, pytest, coverage, startup smoke test) | 🔴 Missing | No `.github/workflows/` directory exists at all — zero automated CI, despite both architecture docs treating it as a required MVP control (`crewai_runtime_architecture.md` §2.8, `full_architecture_flow.md` §16–17) |
| Docker/security CI workflow (image build, container smoke test, dependency audit, secret scanning, image scanning) | 🔴 Missing | Same as above — the Docker image itself is ready to be built by CI, but nothing builds or scans it automatically |
| `GET /metrics/summary` endpoint (`full_architecture_flow.md` §6) | 🔴 Missing | Only `/health` and `/ready` exist in `api/router.py`; no metrics-summary endpoint |
| PostgreSQL vs. SQLite as system of record | 🟡 Doc conflict, impl. reasonable | `crewai_runtime_architecture.md` §4.5/§3 treats PostgreSQL as the only system of record; `full_architecture_flow.md` §15 explicitly allows SQLite for local dev with Postgres for hosted deployment. Current `Settings.database_url` defaults to SQLite locally while `docker-compose.yml` wires Postgres for the containerized path — matches the *second* document, conflicts with the first's stricter wording. No ORM models exist yet either way (tracked above under Persistence) |
| CrewAI tracing wired to Flow/Crew/agent/task/tool/LLM execution | 🔴 Missing | `Settings.crewai_tracing_enabled` exists as a config flag, but nothing consumes it — there's no live Flow or Crew execution path yet for tracing to attach to (same root cause as the Flow gap above) |
