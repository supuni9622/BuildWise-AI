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
| BuildWise CrewAI Flow | ✅ Built | `flows/consulting_flow.py::BuildWiseConsultingFlow` is the native `Flow[BuildWiseFlowState]` orchestrator. It connects intake, Discovery, Product Planning, deterministic specialist planning, Technical Planning, Lead Review, revisions, and the blueprint boundary with `@start`/`@listen`/`@router` methods |
| Discovery Crew | ✅ Built | `crews/discovery.py` + `tasks/discovery.py` |
| DiscoveryResult | ✅ Built | `domain/discovery.py` |
| Completeness Router | ✅ Built | `BuildWiseConsultingFlow.route_discovery()` delegates to `route_after_discovery(state)` and emits live clarification, continuation, or failure routes |
| Clarification loop (pause/frontend/answers/resume) | 🟡 Partial | The Flow enters `AWAITING_USER_INPUT`, accepts structured `ClarificationAnswer` values, and routes a persisted/reconstructed `RESUMING` state through Discovery to completion. `BuildWiseFlowStore` provides the native persistence adapter; the frontend/API resume endpoint remains missing |
| Early Market Router | ✅ Built | `run_product_planning()` calls `SpecialistPlanner.should_include_early_market_context(...)` before constructing the Product Planning Crew |
| Product Planning Crew | ✅ Built | `crews/product_planning.py`, incl. `assemble_product_planning_result` → `ProductPlanningResult` |
| Deterministic Specialist Planner | ✅ Built | `src/buildwise/planning/` implements the pure-Python planner; `BuildWiseConsultingFlow.plan_specialists()` now calls it, stores the `SpecialistExecutionPlan`, registers selected executions, and passes that exact plan to the Technical Planning Crew |
| Technical Planning Crew | ✅ Built | `crews/technical_planning.py`, incl. `assemble_technical_planning_result` → `TechnicalPlanningResult` |
| Cost Aggregator | 🟡 Partial | The Flow converts each Crew's `UsageMetrics` into a `UsageRecord`, accumulates prompt/completion/total tokens and agent executions in `UsageSummary`, and enforces `maximum_session_tokens`. Provider/model attribution, estimated cost, tool calls, retries, and execution duration are not yet populated |
| Lead Review Crew | ✅ Built | `crews/lead_review.py` + `tasks/lead_review.py` |
| approved → blueprint | 🟡 Partial | The live review router handles `APPROVED` and `APPROVED_WITH_LIMITATIONS`, verifies `approved_for_blueprint`, and invokes an injected `BlueprintBuilder`. The concrete deterministic builder/rendering implementation remains missing |
| revisions → rerun affected planning Crew | ✅ Built | The Flow maps product targets to Product Planning and technical targets to Technical Planning, cascades product revisions through replanning and technical regeneration, retains revision history, and enforces `maximum_specialist_revisions` |
| Output validation | 🟡 Partial | The Flow rejects missing/wrong structured Discovery and Lead Review outputs, aggregate assemblers validate Product/Technical Planning, and state setters enforce session ownership and specialist selection. The dedicated `validation/` package and a unified post-Crew validation service remain missing |
| Deterministic Blueprint Generator | 🔴 Missing | `reporting/__init__.py` is empty. `ProductBlueprint`/`BlueprintSection` models exist (`domain/blueprint.py`) with no assembler |
| Final Report / Frontend | 🔴 Missing | Depends on the blueprint generator above |
| Persistence (implicit, cross-cutting) | ✅ Built | `persistence/models.py` defines the five-table MVP schema; `repositories.py` handles consultation snapshots, versioned artifacts, clarification rounds, revisions, and usage; `flow_store.py::BuildWiseFlowStore` is the native CrewAI adapter. The full Flow persistence integration is tested |

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
helpers were dead code at the time (nothing outside `routing.py` called them)
and have been deleted; `route_after_specialist_planning`/
`route_after_specialists` now require only `SOLUTION_ARCHITECTURE`.

The planner is now called by `BuildWiseConsultingFlow.plan_specialists()` and
its exact output drives `create_technical_planning_crew(...)`.

### 2. ✅ Done — Main orchestrator — `src/buildwise/flows/consulting_flow.py`
Implemented per `prds/06_consulting_flow_prd.md`. The native CrewAI Flow owns
stage transitions, routing, structured clarification pause/resume, all four
Crew executions, planner execution, bounded revision routing, usage capture,
approval/rejection, and the blueprint-builder boundary. `BuildWiseFlowState`
now retains the preferred aggregate results, specialist plan, full Lead
Review, and revision history. Review routing consumes `LeadReview.decision`
directly; the obsolete duplicate-boolean contract has been removed. The Flow
constructor also accepts CrewAI's native `FlowPersistence` boundary.

### 3. ✅ Done — Minimal persistence — `src/buildwise/persistence/`
Implemented the five MVP tables: `consultations`, `artifacts`,
`clarification_rounds`, `revisions`, and `usage`. The SQLAlchemy repositories
upsert mutable session data, preserve immutable artifact versions, and avoid
duplicate revision records. `BuildWiseFlowStore` implements CrewAI's native
`FlowPersistence`, creates the schema, saves after Flow methods, and restores
state by CrewAI Flow UUID. No user, organization, permission, authentication,
API-key, or tenant-isolation tables were added.

### 4. 🟡 Partial — Output validation — `src/buildwise/validation/`
The Flow-side check described in every Crew PRD: reject a "successful"
`CrewOutput` when `.pydantic` is `None`, the wrong type, or fails ownership —
largely already covered by the same `run_domain_validator`/
`require_pydantic_output` machinery in `tasks/guardrails.py`, but the Flow
still needs one more pass after assembling `ProductPlanningResult`/
`TechnicalPlanningResult`/`LeadReview` before persisting them.

### 5. Deterministic Blueprint Generator — `src/buildwise/reporting/`
Consume the approved aggregates + `LeadReview`, produce a `ProductBlueprint`
(model already exists), render Markdown. No LLM call needed per the PRDs
unless deterministic assembly proves unreadable later.

The Flow-side `BlueprintBuilder` protocol and approval boundary now exist;
the concrete builder is still required.

### 6. Complete usage and runtime-budget accounting
Extend the new Flow-owned token aggregator with provider/model attribution,
estimated cost, tool calls, retries, duration, and enforcement for every
remaining `FlowRuntimeLimits` field.

### 7. Consultation API endpoints — `src/buildwise/api/v1/`
`POST` to start a consultation (kicks off the Flow), `POST` to submit
clarification answers (resumes it), `GET` to poll status/result. These call
into the completed Flow and the persistence layer in step 3.

---

## Smaller loose ends

- ~~`flows/routing.py`'s `SpecialistRoutingPlan` and
  `domain/specialist_planning.py`'s `SpecialistExecutionPlan` are two
  different models...~~ **Resolved.** There was only ever one model
  (`SpecialistExecutionPlan`); `routing.py` held a second, buggy
  implementation of the selection *rules* targeting that same model. It has
  been removed in favor of `src/buildwise/planning/` (see step 1 above).
- Tests now include 62 planner tests, 11 mocked Consulting Flow tests, and
  four persistence tests. Flow coverage includes the happy path, intake rejection,
  typed clarification, serialized-state resume through completion, all four
  review decisions, malformed revision decisions, revision-limit exhaustion,
  and session ownership. The full suite contains 77 passing tests with no
  live LLM calls.
- The planner's budget policy is intentionally coarse per the PRD (no exact
  token/dollar estimation): it only reads
  `FlowRuntimeLimits.maximum_agent_executions` and
  `.maximum_estimated_cost_usd`. The Flow now enforces
  `.maximum_session_tokens` from aggregated Crew usage; `.maximum_tool_calls`
  and `.maximum_execution_seconds` remain unenforced.
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
| FR2 | Generate dynamic questions | ✅ Built | Discovery produces `ClarificationQuestionSet` and the Flow exposes it as the typed pause result |
| FR3 | Pause and resume sessions | 🟡 Partial | The live Flow pauses in `AWAITING_USER_INPUT`, persists typed state through `BuildWiseFlowStore`, accepts structured answers, and resumes through Discovery to completion. Only the external API/frontend resume endpoint remains missing |
| FR4 | Select specialists dynamically | ✅ Built | The live Flow calls `SpecialistPlanner.create_execution_plan(...)`, stores its plan, and uses it to construct Technical Planning |
| FR5 | Generate product blueprint | 🔴 Missing | `ProductBlueprint`/`BlueprintSection` models exist (`domain/blueprint.py`); `reporting/__init__.py` is an empty stub — no assembler produces one |
| FR6 | Support markdown export | 🔴 Missing | `ProductBlueprint.generated_markdown` is a required field in the model, but nothing populates it since no generator exists |
| FR7 | Provide execution tracing | 🟡 Partial | HTTP request tracing and a live CrewAI Flow execution path exist, with stage-level structlog events. Explicit CrewAI trace configuration and per-session trace persistence remain missing |

## Non-Functional Requirements

| PRD requirement | Status | Evidence |
|---|---|---|
| Performance: < 2 minutes end-to-end | 🔴 Not verifiable | The orchestrator exists, but no live-LLM end-to-end performance benchmark has been run |
| Reliability: partial specialist failures shouldn't fail the whole workflow | 🟡 Partial | The live Flow tracks specialist lifecycle and routes required-specialist failure, but Crew-level exception normalization and optional-specialist degraded continuation are not yet complete |
| Security — Prompt Injection Protection | 🔴 Missing | No sanitization or prompt-injection defenses found anywhere in `tasks/` or `domain/intake.py`; input is only Pydantic-schema-validated, not adversarially screened |
| Security — Tool Restrictions | ✅ Built | `tools/registry.py` exposes a small, explicit `ToolKey` whitelist (`web_search`, `web_scraper`, `github_search`) with per-tool env-var gating; agents can only request tools by these keys |
| Security — Input Validation | 🟡 Partial | Strong Pydantic validation exists on all domain models (`domain/intake.py`, etc.), but there is no live endpoint yet accepting raw external input for that validation to guard |
| Cost — Session budget controls | 🟡 Partial | The Flow enforces session tokens and revision rounds and the planner applies agent/cost selection limits. Tool-call, duration, and actual estimated-cost enforcement remain incomplete |

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
| Flows | ✅ Built | `BuildWiseConsultingFlow` is the live typed orchestrator and is covered by mocked end-to-end tests |
| Crews | ✅ Built | Four real Crews: `crews/discovery.py`, `crews/product_planning.py`, `crews/technical_planning.py`, `crews/lead_review.py` |
| Human Feedback | 🟡 Partial | Structured clarification pause/resume and native state persistence are complete without manual JSON parsing. No API/frontend bridge or interactive input provider exists yet |
| Structured Outputs | ✅ Built | `TaskOutput.pydantic` enforced pervasively via `tasks/guardrails.py::require_pydantic_output` and friends |
| Tool Usage | ✅ Built | `tools/registry.py` wraps official CrewAI tools (`SerperDevTool`, `ScrapeWebsiteTool`, `GithubSearchTool`) |
| Parallel Execution | 🔴 Missing | The Flow currently executes its Crews sequentially; no Crew branches run concurrently |
| Tracing | 🟡 Partial | HTTP request tracing, a real CrewAI execution path, and stage-level Flow logs exist; explicit CrewAI trace wiring and persistence remain missing |
| Reflection Loops | ✅ Built | Task guardrail retries and the higher-level Lead Review → targeted Crew revision → Lead Review loop are both wired and bounded |
| Dynamic Routing | ✅ Built | Native `@router` methods now drive Discovery, review, revision, blueprint, and failure branches |

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
   agents. The live Flow follows the planner, so the registry metadata should
   be reconciled with the execution behavior.
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
| Flow-first orchestration (Flows own routing/state/pause-resume/specialist selection) | ✅ Built | `BuildWiseConsultingFlow` owns routing, aggregate state, clarification pause/resume, planner calls, Crew execution, revisions, usage capture, completion, and deterministic failure routes |
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
| PostgreSQL vs. SQLite as system of record | 🟡 Doc conflict, impl. reasonable | `crewai_runtime_architecture.md` §4.5/§3 treats PostgreSQL as the only system of record; `full_architecture_flow.md` §15 allows SQLite locally and Postgres when hosted. The portable SQLAlchemy MVP schema now supports both; `Settings.database_url` defaults to SQLite locally while `docker-compose.yml` wires Postgres |
| CrewAI tracing wired to Flow/Crew/agent/task/tool/LLM execution | 🟡 Partial | A real Flow/Crew execution path and stage-level structlog events now exist, but `Settings.crewai_tracing_enabled` is not explicitly passed into the Flow and no trace records are persisted per consulting session |

---

# LLM Model Selection Alignment — `docs/architecture/3. llm_model_selection.md` vs current implementation

That document is a provider/cost analysis that lands on **OpenAI as the V1
provider**, routed across four cost tiers (Fast / Balanced (Primary) /
Architecture / Reviewer), with Claude kept as a documented fallback/alt
config. This checks that recommendation against what's actually wired up.
Same legend: ✅ Built · 🟡 Partial · 🔴 Missing.

| Doc element | Status | Evidence |
|---|---|---|
| Provider decision (OpenAI primary for V1) | ✅ Built | `config/settings.py:29-32` defaults `primary_agent_model`/`architect_model`/`lead_reviewer_model`/`fast_model` all to `openai/...`; `.env.example` mirrors this under "Active BuildWise workflow models" |
| Four-tier `ModelTier` routing (Fast/Primary/Architect/Lead Reviewer) as a real mechanism, not just per-agent hardcoded strings | ✅ Built | `domain/enums.py::ModelTier` + `agents/factory.py::resolve_model_name` (`factory.py:251-273`) maps each `AgentContract.model_tier` to the matching `Settings` field, then builds a `crewai.LLM` from it (`factory.py:176`) |
| Exact recommended model IDs (§12/§15: `gpt-5.4-nano`, `gpt-5.4-mini`, `gpt-5.6-luna`, `gpt-5.6-terra`) | 🔴 Diverged | Actual defaults are different model IDs entirely: `fast_model`/`primary_agent_model` = `openai/gpt-5-mini`, `architect_model`/`lead_reviewer_model` = `openai/gpt-5.2` (`settings.py:29-32`) — the doc's specific routing table was never transcribed into code |
| Reviewer tier priced/modeled as the expensive, sparingly-used tier (§5, §9: the whole "Opus/Terra only for the reviewer" cost argument) | 🔴 Diverged | In the actual config, `lead_reviewer_model` and `architect_model` default to the **same** model (`gpt-5.2`) — there is currently no cost or capability differentiation between "Architecture" and "Reviewer" tiers, undermining the doc's central cost-tiering rationale |
| Fast-tier agents (§4/§13: Completeness Evaluator, Capability Classifier, Clarification Generator, Output Repair, lightweight semantic validation) | 🔴 Missing | `ModelTier.FAST` is fully wired in `factory.py`'s tier map, but `grep model_tier= src/buildwise/agents/*.py` shows **zero** `AgentContract`s use it — none of these lightweight-classifier agents exist yet; Discovery/clarification logic instead runs entirely on the Primary-tier Discovery Analyst |
| Balanced/Primary-tier agent roster (§4/§13: Discovery Analyst, Product Manager, Business Analyst, Market & GTM Strategist, **Security Architect**, **QA Architect**) | 🟡 Mismatch | Discovery Analyst, Product Manager, Business Analyst, Market & GTM Strategist are `ModelTier.PRIMARY` as the doc says — but Security Architect (`security_architect.py:75`) and QA & Evaluation Architect (`qa_evaluation_architect.py:173`) are actually `ModelTier.ARCHITECT` in code. `.env.example`'s own tier comments repeat the doc's (incorrect) roster, so the drift is between code and *two* docs, not just one |
| Specialist Planner uses an LLM at the Balanced tier (§4/§13 explicitly list "Specialist Planner" as a model-routed role) | 🔴 Contradicted | The actual `SpecialistPlanner` (`planning/planner.py`) is pure deterministic Python — "no CrewAI/LLM/DB" per its own PRD (`prds/05_specialist_planner.md`) — it never calls a model at all, so it has no tier to be routed to |
| Claude/Anthropic as documented alternate/evaluation config (§16, .env.example's `CLAUDE_*_MODEL`, `EVALUATION_MODEL`, `STRONG_EVALUATION_MODEL`) | 🔴 Missing | None of these fields exist on the `Settings` class (`config/settings.py`); since `model_config` sets `extra="ignore"`, setting them in `.env` is silently a no-op. No code path reads or constructs an Anthropic `LLM` anywhere |
| Model fallback policy (`.env.example`'s `FALLBACK_*_MODEL`, `MODEL_FALLBACK_*`) | 🔴 Missing | Same gap as above — documented in `.env.example` only, absent from `Settings`, and `factory.py::resolve_model_name` has no retry-with-fallback logic; a misconfigured or failing model raises `AgentProviderConfigurationError` with no fallback attempt |
| Multi-provider dependency readiness (doc's §14 "should remain provider agnostic") | ✅ Built | `pyproject.toml`: `crewai[openai,anthropic,litellm,tools]==1.15.5` — both OpenAI and Anthropic extras plus `litellm` are installed, so switching any tier to `anthropic/...` today is a config-only change, not a code change |
| Per-tier cost tracking (doc's entire §6-§9 cost comparison implies costs get measured) | 🟡 Partial | The Flow now constructs one `UsageRecord` per Crew and aggregates token counts and successful requests. It does not yet populate model/provider or estimated-cost fields, so tier-specific cost reporting remains incomplete |

## Key misalignments to resolve

1. **Reviewer tier has no cost/capability separation from Architecture tier** — the doc's core argument ("Opus/Terra only for the reviewer, Sonnet/Luna everywhere else, because the reviewer runs once and can afford to be pricier") is moot today since `lead_reviewer_model` and `architect_model` default to the identical `gpt-5.2`.
2. **Security Architect and QA Architect tier placement disagrees between code and docs** — both the doc under review and `.env.example`'s comments say Primary/Balanced tier; `agents/security_architect.py` and `agents/qa_evaluation_architect.py` actually declare `ModelTier.ARCHITECT`. Pick one and reconcile the other two.
3. **The doc's Fast tier has no agents to route** — until Completeness Evaluator / Capability Classifier / Output Repair agents exist (none do), `FAST_MODEL` is configured but dead weight.
4. **The doc assumes the Specialist Planner is a model call; it isn't** — it's deterministic Python by design (`prds/05_specialist_planner.md`). The doc should either be corrected or explicitly note the planner as a non-LLM exception.
5. **`.env.example` documents a whole cross-provider evaluation subsystem (`EVALUATION_*`, `CLAUDE_*_MODEL`, `MODEL_FALLBACK_*`) that has zero corresponding fields in `Settings` and zero implementing code** — right now these env vars do nothing if set, which is a silent-failure trap for anyone following `.env.example` expecting them to work.
