# BuildWise AI — Gap Analysis vs. Target Flow

Walks `BuildWise AI -final flow.drawio.png` node by node against the current
codebase. Legend: ✅ Built · 🟡 Partial (real logic exists but incomplete) ·
🔴 Missing (nothing built yet).

Assessment baseline: 2026-07-27, including the Consulting Flow, five-table
PostgreSQL persistence layer, consultation clarification/resume API, and final
cross-stage output validator, deterministic blueprint generator, and the
no-auth `web/` frontend module.

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
| Actor / Frontend | ✅ Built | `web/` is a frontend module in the same repository. It provides product intake, configurable API connection, resumable consultation state, clarification forms, live stage progress, the final 17-section blueprint viewer, and Markdown download without authentication |
| FastAPI validation | ✅ Built | The API validates vague-idea intake and typed clarification answers and exposes `POST /api/v1/consultations`, `POST /api/v1/consultations/{id}/clarifications`, `GET /api/v1/consultations/{id}`, and `GET /api/v1/consultations/{id}/result` |
| BuildWise CrewAI Flow | ✅ Built | `flows/consulting_flow.py::BuildWiseConsultingFlow` is the native `Flow[BuildWiseFlowState]` orchestrator. It connects intake, Discovery, Product Planning, deterministic specialist planning, Technical Planning, Lead Review, revisions, and the blueprint boundary with `@start`/`@listen`/`@router` methods |
| Discovery Crew | ✅ Built | `crews/discovery.py` + `tasks/discovery.py` |
| DiscoveryResult | ✅ Built | `domain/discovery.py` |
| Completeness Router | ✅ Built | `BuildWiseConsultingFlow.route_discovery()` delegates to `route_after_discovery(state)` and emits live clarification, continuation, or failure routes |
| Clarification loop (pause/answers/resume) | ✅ Built | The API returns active questions, loads persisted Flow state, validates the active round and question set, checkpoints accepted answers before execution, resumes Discovery, and continues to the next pause or terminal state. `web/app/page.tsx` renders free-text, numeric, boolean, single-choice, and multiple-choice clarification inputs and resumes the consultation |
| Early Market Router | ✅ Built | `run_product_planning()` calls `SpecialistPlanner.should_include_early_market_context(...)` before constructing the Product Planning Crew |
| Product Planning Crew | ✅ Built | `crews/product_planning.py`, incl. `assemble_product_planning_result` → `ProductPlanningResult` |
| Deterministic Specialist Planner | ✅ Built | `src/buildwise/planning/` implements the pure-Python planner; `BuildWiseConsultingFlow.plan_specialists()` now calls it, stores the `SpecialistExecutionPlan`, registers selected executions, and passes that exact plan to the Technical Planning Crew |
| Technical Planning Crew | ✅ Built | `crews/technical_planning.py`, incl. `assemble_technical_planning_result` → `TechnicalPlanningResult` |
| Cost Aggregator | ✅ Built | `application/cost_aggregator.py` deterministically collects project/build estimates from Product, Market & GTM, Solution, AI, Security, and QA outputs into a canonical `CostSummary` before Lead Review. It preserves source ownership, normalizes range and point estimates, and totals only matching currency/frequency groups without exchange-rate or annualization assumptions. The separate `application/usage_aggregator.py` remains responsible for BuildWise's own LLM tokens, requests, duration, and provider-reported execution cost |
| Lead Review Crew | ✅ Built | `crews/lead_review.py` + `tasks/lead_review.py` |
| approved → blueprint | ✅ Built | The live review router handles `APPROVED` and `APPROVED_WITH_LIMITATIONS`, verifies `approved_for_blueprint`, and invokes `BlueprintAssembler` by default while retaining the injectable `BlueprintBuilder` boundary |
| revisions → rerun affected planning Crew | ✅ Built | `flows/revisions.py` deterministically maps Product Definition, Requirements, and Market & GTM to the Product Planning Crew, and Solution, AI, Security, and QA revisions to the Technical Planning Crew. Technical revisions rerun only the target plus selected downstream dependants (Solution → selected AI/Security/QA; AI → selected Security/QA; Security → selected QA; QA only). The Flow retains revision history and enforces `state.limits.maximum_specialist_revisions`; no revision-planning Agent is used |
| Output validation | 🟡 Partial | `validation/output_validator.py::validate_output` is wired as a pre-assembly cross-stage gate: it verifies ownership, aggregate/execution-graph consistency, selected specialist outputs, current project costs, and Lead Review approval. The diagram/catalog's post-assembly validation of the actual `ProductBlueprint` and rendered Markdown remains missing |
| Deterministic Blueprint Generator | ✅ Built | `reporting/assembler.py` deterministically maps the approved aggregates and usage summary into all 17 `ProductBlueprint` sections; `reporting/markdown_renderer.py` renders and writes `blueprint.md` without an LLM call |
| S3 report storage | ✅ Built | After blueprint generation, `reporting/storage.py` writes Markdown to `consultations/{consultation_id}/blueprints/v1/blueprint.md` in S3, with optional `blueprint.json`. Local development defaults to `data/reports/{consultation_id}/blueprint.md`. PostgreSQL stores the version-1 key, generation time, and Lead Review ID in `blueprint_reports` |
| Final Report / Frontend | ✅ Built | The frontend renders the completed typed blueprint as a navigable 17-section document, surfaces open questions separately from limitations, and downloads `generated_markdown` as `blueprint.md` |
| Persistence (implicit, cross-cutting) | ✅ Built | `persistence/models.py` defines the original five MVP tables plus `blueprint_reports`; `repositories.py` handles consultation snapshots, versioned artifacts, clarification rounds, revisions, usage, and report-location metadata; `flow_store.py::BuildWiseFlowStore` is the native CrewAI adapter. PostgreSQL is running through Docker Compose and the active local configuration connects on `localhost:5433`; containers use `postgres:5432` internally |

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

#### Targeted revision router — `src/buildwise/flows/revisions.py`

Revision planning is a small deterministic module rather than another Agent.
It maps product-output targets to the existing Product Planning Crew and
technical-output targets to the existing Technical Planning Crew. For
technical revisions it computes the dependency cascade against the specialists
selected for the current Flow:

- Solution revision → Solution plus selected AI, Security, and QA
- AI revision → AI plus selected Security and QA
- Security revision → Security plus selected QA
- QA revision → QA only

Partial Technical Planning Crew runs reuse unchanged upstream artifacts and
merge their revised outputs back into the existing `TechnicalPlanningResult`.
Unsupported targets and technical targets not selected for the Flow are
rejected deterministically. Before a revision starts, the router checks
`state.revision_count` against
`state.limits.maximum_specialist_revisions`; exhaustion routes the Flow to
failure. A `COST_SUMMARY` revision deterministically rebuilds the summary
without creating or invoking another Agent or Crew.

#### Project Cost Aggregator — `src/buildwise/application/cost_aggregator.py`

After Technical Planning, the Flow gathers implementation-project estimates
owned by Product Definition, optional Market & GTM, Solution Architecture,
optional AI Architecture, optional Security Architecture, and optional QA &
Evaluation. Range estimates retain their minimum, expected, and maximum
values; point estimates are normalized to equal minimum/expected/maximum
values. `CostSummary` keeps every estimate's source and totals only values
with the same currency and frequency, so one-time, monthly, annual, and
per-request costs are never incorrectly combined.

The summary is retained in Flow state and persistence, passed into the Lead
Review Crew as structured context, checked for staleness after revisions, and
used by the blueprint Costs section. This project-cost path is deliberately
separate from `usage_aggregator.py`, which measures the cost and usage of
running BuildWise itself.

### 3. ✅ Done — Minimal persistence — `src/buildwise/persistence/`
Implemented the five MVP tables: `consultations`, `artifacts`,
`clarification_rounds`, `revisions`, and `usage`. The SQLAlchemy repositories
upsert mutable session data, preserve immutable artifact versions, and avoid
duplicate revision records. `BuildWiseFlowStore` implements CrewAI's native
`FlowPersistence`, creates the schema, saves after Flow methods, and restores
state by CrewAI Flow UUID. No user, organization, permission, authentication,
API-key, or tenant-isolation tables were added.

The runtime database setup is also complete: Docker Compose runs
`buildwise-postgres` with a named `buildwise-postgres-data` volume. The host
uses the published port configured by `POSTGRES_PORT` (currently `5433`), while
the application container receives the Compose-network URL using
`postgres:5432`. Only one `DATABASE_URL` is used in each runtime context.
SQLite and a local `data/` directory are not required for the active setup.

### 4. 🟡 Partial — Output validation — `src/buildwise/validation/`
`validation/output_validator.py::validate_output(state)` is the final
deterministic cross-stage pass before blueprint assembly. It requires
Discovery, Product Planning, the specialist execution plan, Technical
Planning, `CostSummary`, and Lead Review; verifies all session-owned
artifacts; rejects a stale or inconsistent project-cost summary; reruns the
existing aggregate, ownership, and execution-graph domain validators; checks
the technical outputs against selected specialists; and prevents blueprint
approval when the Lead Review is inconsistent or retains a blocking revision.
`BuildWiseConsultingFlow.build_blueprint()` now invokes this validator before
the deterministic generator.

This is not yet the catalog's final-output validator: no validator receives
the assembled `ProductBlueprint` or checks its rendered Markdown before
storage and delivery.

Lead Review decision consistency now has one reusable domain check,
`LeadReview.validate_decision_consistency()`, shared by the task guardrail and
the final output validator rather than duplicating the decision rules.

### 5. ✅ Done — Deterministic Blueprint Generator — `src/buildwise/reporting/`
`BlueprintAssembler` consumes Discovery, Product Planning, the specialist
execution plan, Technical Planning, the canonical project `CostSummary`, Lead
Review, and the Flow usage summary.
It produces a 17-section `ProductBlueprint`, aggregates risks, assumptions,
open questions, limitations, implementation phases, and usage, and renders
the complete Markdown deterministically. `MarkdownRenderer` can write that
content to `blueprint.md`. The live Flow uses this assembler by default; no
LLM call is involved.

#### S3 report storage — `src/buildwise/reporting/storage.py`

The Flow stores the generated Markdown before marking the consultation
complete. S3 uses the fixed MVP key
`consultations/{consultation_id}/blueprints/v1/blueprint.md`; structured JSON
at the matching `blueprint.json` key is configurable. Local and test
environments can use the filesystem backend at
`data/reports/{consultation_id}/blueprint.md` without AWS credentials.
`blueprint_reports` retains `consultation_id`, `blueprint_version` (fixed at
`1` for the MVP), `s3_key`, `generated_at`, and `lead_review_id`. Comparison,
replacement, and multi-version update workflows remain intentionally out of
scope.

### 6. 🟡 Partial — Complete runtime-budget accounting
The lightweight usage aggregator is complete: each successful Crew execution
appends a record and updates token, request, duration, and reliably supplied
cost totals. Provider/model attribution remains optional because CrewAI's
aggregate `UsageMetrics` currently exposes token and successful-request counts
but not model identity or cost. Tool-call and retry instrumentation, plus
enforcement of the remaining `FlowRuntimeLimits`, are still required.

### 7. ✅ Done — Consultation API endpoints — `src/buildwise/api/v1/`
Implemented start, clarification submission, status lookup, and result lookup.
`ConsultationService` reconstructs typed state through `BuildWiseFlowStore`,
checks the submitted clarification round, delegates active-question and
required-answer validation to `BuildWiseFlowState`, checkpoints accepted
answers before resuming, and runs the Flow until its next pause or terminal
result. Creating the service initializes the five-table schema.

### 8. ✅ Done — Frontend — `web/`
The repository now includes a responsive frontend module built with React,
Next-compatible routing, TypeScript, and the Sites/Vite runtime. It starts
consultations from the full product-intake form, persists the consultation ID
locally for refresh/resume, renders all supported clarification question
types, polls active Flow stages, displays failures, presents the completed
17-section blueprint, and downloads `blueprint.md`.

The frontend requires no authentication. It connects to
`http://localhost:8080/api/v1` by default, supports
`NEXT_PUBLIC_BUILDWISE_API_URL` and an in-app API setting, and the FastAPI app
enables the CORS bridge required for browser access. Setup and run instructions
are documented in the root `README.md`.

---

## Smaller loose ends

- ~~`flows/routing.py`'s `SpecialistRoutingPlan` and
  `domain/specialist_planning.py`'s `SpecialistExecutionPlan` are two
  different models...~~ **Resolved.** There was only ever one model
  (`SpecialistExecutionPlan`); `routing.py` held a second, buggy
  implementation of the selection *rules* targeting that same model. It has
  been removed in favor of `src/buildwise/planning/` (see step 1 above).
- Tests now include planner, mocked Consulting Flow, persistence, output
  assembler, and consultation API/service coverage. Coverage
  includes the happy path, intake rejection, typed clarification, serialized
  state resume through completion, active-round/question validation, status
  and result retrieval, all four review decisions, malformed revision
  decisions, revision-limit exhaustion, and session ownership. The full suite
  contains 82 passing tests with no live LLM calls. The frontend additionally
  passes ESLint, TypeScript checking, and its production build.
- The planner's budget policy is intentionally coarse per the PRD (no exact
  token/dollar estimation): it only reads
  `FlowRuntimeLimits.maximum_agent_executions` and
  `.maximum_estimated_cost_usd`. The Flow now enforces
  `.maximum_session_tokens` from aggregated Crew usage and
  `.maximum_estimated_cost_usd` when every recorded Crew supplies reliable
  cost metadata. `.maximum_tool_calls` and `.maximum_execution_seconds`
  remain unenforced, although Crew execution duration is now measured and
  retained.
- `reporting/` now contains the deterministic assembler and Markdown renderer;
  `validation/` contains the final cross-stage validator described in step 4.

---

# PRD Alignment — `prd.md` vs. current implementation

The section above tracks the target *flow diagram*. This section tracks the
PRD document itself (`prd.md`) line by line: Functional/Non-Functional
Requirements, the Agents roster, the CrewAI feature checklist, and the Final
Output shape. Same legend: ✅ Built · 🟡 Partial · 🔴 Missing.

## Functional Requirements

| PRD ID | Requirement | Status | Evidence |
|---|---|---|---|
| FR1 | Accept vague ideas | ✅ Built | `POST /api/v1/consultations` accepts the intentionally permissive `ProductIdeaRequest` shape and starts the Discovery Flow |
| FR2 | Generate dynamic questions | ✅ Built | Discovery produces `ClarificationQuestionSet` and the Flow exposes it as the typed pause result |
| FR3 | Pause and resume sessions | ✅ Built | The Flow pauses in `AWAITING_USER_INPUT`; `POST /api/v1/consultations/{id}/clarifications` reloads its durable state, validates the active round/question set, checkpoints answers, and resumes execution to the next pause or terminal state |
| FR4 | Select specialists dynamically | ✅ Built | The live Flow calls `SpecialistPlanner.create_execution_plan(...)`, stores its plan, and uses it to construct Technical Planning |
| FR5 | Generate product blueprint | ✅ Built | `reporting/assembler.py::BlueprintAssembler` produces the typed blueprint from the approved stage aggregates and is the Flow's default builder |
| FR6 | Support markdown export | ✅ Built | `reporting/markdown_renderer.py` populates `generated_markdown` and writes a deterministic `blueprint.md` |
| FR7 | Provide execution tracing | ✅ Built | Native CrewAI tracing is explicitly configured on the live Flow and every Crew through `CREWAI_TRACING_ENABLED`; CrewAI owns trace collection and storage |

## Non-Functional Requirements

| PRD requirement | Status | Evidence |
|---|---|---|
| Performance: < 2 minutes end-to-end | 🔴 Not verifiable | The orchestrator exists, but no live-LLM end-to-end performance benchmark has been run |
| Reliability: partial specialist failures shouldn't fail the whole workflow | 🟡 Partial | The live Flow tracks specialist lifecycle and routes required-specialist failure, but Crew-level exception normalization and optional-specialist degraded continuation are not yet complete |
| Security — Prompt Injection Protection | 🔴 Missing | No sanitization or prompt-injection defenses found anywhere in `tasks/` or `domain/intake.py`; input is only Pydantic-schema-validated, not adversarially screened |
| Security — Tool Restrictions | ✅ Built | `tools/registry.py` exposes a small, explicit `ToolKey` whitelist (`web_search`, `web_scraper`, `github_search`) with per-tool env-var gating; agents can only request tools by these keys |
| Security — Input Validation | ✅ Built | The live consultation endpoints apply strict Pydantic request validation to vague intake, clarification rounds, and structured answers; semantic prompt-injection and secret detection remain separate missing security controls |
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

## CrewAI Features Utilized

| PRD claims | Status | Evidence |
|---|---|---|
| Flows | ✅ Built | `BuildWiseConsultingFlow` is the live typed orchestrator and is covered by mocked end-to-end tests |
| Crews | ✅ Built | Four real Crews: `crews/discovery.py`, `crews/product_planning.py`, `crews/technical_planning.py`, `crews/lead_review.py` |
| Human Feedback | ✅ Built | Structured clarification pause/resume, native persistence, active-question validation, and the HTTP bridge are complete without manual JSON parsing. The `web/` module exposes the full interaction through typed clarification controls and automatic continuation/status updates |
| Structured Outputs | ✅ Built | `TaskOutput.pydantic` enforced pervasively via `tasks/guardrails.py::require_pydantic_output` and friends |
| Tool Usage | ✅ Built | `tools/registry.py` wraps official CrewAI tools (`SerperDevTool`, `ScrapeWebsiteTool`, `GithubSearchTool`) |
| Parallel Execution | 🔴 Missing | The Flow currently executes its Crews sequentially; no Crew branches run concurrently |
| Tracing | ✅ Built | Native CrewAI tracing is explicitly configured on the live Flow and every Crew through `CREWAI_TRACING_ENABLED`; CrewAI captures Flow, Crew, agent, task, LLM, and tool execution |
| Reflection Loops | ✅ Built | Task guardrail retries and the higher-level Lead Review → targeted Crew revision → Lead Review loop are both wired and bounded |
| Dynamic Routing | ✅ Built | Native `@router` methods now drive Discovery, review, revision, blueprint, and failure branches |

## Final Output — Product Blueprint sections

PRD specifies 12 sections; the actual `BlueprintSectionType` enum
(`domain/enums.py`) defines 17. The deterministic assembler populates all of
them.

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
| 11. Open Questions | ✅ Built | `OPEN_QUESTIONS` plus `ProductBlueprint.open_questions`; unresolved decisions remain distinct from constraints in `limitations` |
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
2. **Prompt Injection Protection is unimplemented** — the PRD calls it out
   explicitly under Security, and nothing in `tasks/` or `domain/intake.py`
   addresses it beyond standard Pydantic schema validation.
3. ~~**"Open Questions" has no home**~~ **Resolved.**
   `ProductBlueprint.open_questions` and `BlueprintSectionType.OPEN_QUESTIONS`
   now represent unresolved decisions independently from limitations.

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
| Application Service Layer (`full_architecture_flow.md` §3: Session Service, Flow Execution Service, Human Feedback Service, Blueprint Service, Usage and Cost Service, Validation Service, Guardrail Service, Tool Execution Service) | 🟡 Partial | `api/v1/consultation_service.py::ConsultationService` provides the session/Flow/human-feedback boundary; `application/cost_aggregator.py` and `usage_aggregator.py` provide project-cost and runtime-usage aggregation; `validation/output_validator.py` plus `tasks/guardrails.py` provide validation and guardrail logic. Separate Blueprint and Tool Execution services remain missing |
| JSON-first Crew standard (`crewai_runtime_architecture.md` §22, §25: `crews/<name>/crew.jsonc` + `agents/<name>.jsonc`, loaded by a shared Python loader) | 🔴 Missing / diverged | The actual implementation is 100% Python: `crews/*.py` factory functions (`create_discovery_crew`, `create_product_planning_crew`, etc.), `tasks/*.py`, and `agents/*.py` contract modules (`agents/base.py::AgentContract`, `agents/registry.py`, `agents/factory.py`). No `.jsonc` file exists anywhere in `src/`. This is a foundational, repo-wide structural choice that contradicts the contract's canonical folder tree — needs an explicit decision to update the contract or migrate the code |
| Final folder structure (`crewai_runtime_architecture.md` §22) | 🟡 Diverged | Beyond the JSON-first Crew point above: `infrastructure/` exists as a directory but is completely empty (no `__init__.py`, no `llm.py`/`clock.py`); `knowledge/` is empty (no `README.md`, no `product/`/`architecture/`/etc. subdirs); `observability/` has `context.py` + `middleware.py`, not the target's `events.py`/`tracing.py`/`usage.py`; `tools/` has no `policies.py` or `research/`; `flows/` has no `persistence.py` or `guardrails.py` (guardrails currently live in `tasks/guardrails.py` instead); domain module names differ from the target list (`market_and_gtm.py` vs. target `market.py`, `qa.py` vs. target `qa_evaluation.py`) and the domain package has grown several modules the contract's tree doesn't mention (`product_planning.py`, `technical_planning.py`, `specialist_planning.py`, `agent.py`, `api.py`) — a natural result of the Crew-refactor work happening after this contract was written |
| Crews are focused single-outcome units | ✅ Built | The four real Crews (`discovery`, `product_planning`, `technical_planning`, `lead_review`) each match this principle in spirit even though they aren't JSON-defined |
| Sequential process by default, no hierarchical Crews | ✅ Built | All four Crew factories pass `process=Process.sequential`; nothing uses hierarchical execution |

## Specialist roster & selection-timing conflicts

| Conflict | `crewai_runtime_architecture.md` | `full_architecture_flow.md` | `prds/05_specialist_planner.md` (implemented) | Status |
|---|---|---|---|---|
| Market & GTM Strategist selection | §6.6: **"Always included"** alongside Solution Architect and Lead Reviewer, decided in the same specialist-planning stage as AI/Security/QA | Conditional (`MARKET_DECISION` node), decided in the *same* single "Specialist Planning" stage as AI/Security/QA — no separate early stage | Conditional, decided by a **separate, earlier** `should_include_early_market_context()` policy *before* the Product Planning Crew is built, and explicitly **forbidden** from ever appearing in the later Technical Planning `SpecialistExecutionPlan` | 🔴 Three-way conflict | The implementation (`src/buildwise/planning/`) follows the third model. It also fixed a bug where `flows/routing.py`'s old code literally implemented the first model (force-including Market & GTM as `required=True` in the *technical* plan) — see build-order item 1 above. All three documents need to agree on one timing model |
| Solution Architect invocation mode | Implicitly "always runs" (`full_architecture_flow.md` diagram: "Always Runs") | Same | Planner always selects it with `required=True` and rejects exclusion | ✅ Agreement | All three agree Solution Architect is mandatory; only `agents/registry.py`'s `invocation_mode=CONDITIONAL` disagrees (see "Key misalignments" item 1) |

## Security & guardrail depth

| Contract requirement | Status | Notes |
|---|---|---|
| Semantic input validation / prompt-injection detection / secret detection as explicit pre-acceptance pipeline stages (`full_architecture_flow.md` §7–9: "Prompt Injection Check", "Secret Detection", 12-item AI-security threat list including indirect injection via web results, hidden instruction attacks, cross-session leakage) | 🔴 Missing | The consultation API now provides strong structural Pydantic validation, but no semantic prompt-injection or secret-detection stage exists in `tasks/`, `domain/intake.py`, or `api/`. This is the same gap as "Key misalignments" item 3, now specified in much more detail by both new documents — including the principle "all user input, external content, and tool output must be treated as untrusted data", which nothing currently enforces |
| Tool definitions require purpose, allowed users/operations, input constraints, output schema, timeout, retry policy, rate limit, side-effect classification, sensitive-data policy, logging policy, failure behavior (`crewai_runtime_architecture.md` §10) | 🟡 Partial | `tools/registry.py::ToolRegistry` implements the default-deny key allowlist and per-tool env-var gating (§10.1) cleanly, but none of the other governance fields exist as structured policy — there's no `tools/policies.py`, no timeout/retry/rate-limit config per tool, no tool-output sanitization or untrusted-content handling |
| Tool output must pass a security/injection guardrail before being used by a specialist (`full_architecture_flow.md` diagram: `TOOL_OUTPUT_GUARDRAIL`) | 🔴 Missing | No such guardrail exists; tool results returned by `ToolRegistry.resolve_many()` flow directly into the agent with no intermediate check |
| Deterministic + LLM guardrail split (`crewai_runtime_architecture.md` §17) | 🟡 Partial | Deterministic guardrails exist and are used extensively (`tasks/guardrails.py::require_pydantic_output` and friends); no LLM-based subjective guardrails (clarity, coherence, vague-recommendation detection) exist yet, and the doc's specific "one repair attempt then mark partial" pattern isn't implemented — current guardrails retry then fail the task rather than continuing with a partial/degraded result |

## Operational infrastructure

| Contract requirement | Status | Notes |
|---|---|---|
| Docker (multi-stage build, non-root user, health check, production ASGI server, `.dockerignore`, pinned deps) | ✅ Built | `Dockerfile` matches the spec closely: multi-stage `python:3.12-slim` build, non-root `buildwise` user, `HEALTHCHECK` hitting `/health`, `uv`-pinned deps. `docker-compose.yml` wires a Postgres service too. Not previously credited anywhere in this document |
| CI (GitHub Actions: Ruff, mypy, pytest, coverage, startup smoke test) | 🔴 Missing | No `.github/workflows/` directory exists at all — zero automated CI, despite both architecture docs treating it as a required MVP control (`crewai_runtime_architecture.md` §2.8, `full_architecture_flow.md` §16–17) |
| Docker/security CI workflow (image build, container smoke test, dependency audit, secret scanning, image scanning) | 🔴 Missing | Same as above — the Docker image itself is ready to be built by CI, but nothing builds or scans it automatically |
| `GET /metrics/summary` endpoint (`full_architecture_flow.md` §6) | 🔴 Missing | Operational health/readiness and all four consultation endpoints exist, but no metrics-summary endpoint is registered |
| PostgreSQL system of record | ✅ Built and configured | The portable SQLAlchemy schema supports SQLite for isolated tests, but the active runtime is PostgreSQL. Docker Compose runs `buildwise-postgres`, persists data in the named `buildwise-postgres-data` volume, exposes the configured host port (`5433` currently), and injects `postgres:5432` into the application container. `.env.example` now presents PostgreSQL as the single runtime setup instead of also declaring a conflicting SQLite URL. `Settings.database_url` retains a SQLite fallback only when no environment configuration is supplied |
| CrewAI tracing wired to Flow/Crew/agent/task/tool/LLM execution | 🟡 Partial | `Settings.crewai_tracing_enabled` is passed explicitly into the Flow and every Crew, and stage-level structlog events exist. BuildWise still has no trace adapter that correlates/persists trace IDs per consultation or verifies complete agent/task/tool/LLM coverage |

---

# Processor and Classifier Catalog Alignment — `docs/architecture/2. buildwise_processors_classifiers_catalog.md`

This section audits every non-agent component in the catalog against the
current runtime. “Partial” includes behavior embedded in an Agent task or
CrewAI primitive when the catalog calls for a separate deterministic
component, and behavior whose core exists but whose stated controls are not
enforced.

| Catalog component | Status | Current implementation evidence | Gaps, mismatches, and alignment notes |
|---|---|---|---|
| Input Validator | ✅ Built | FastAPI request models in `domain/api.py` reuse constrained Pydantic intake and clarification models from `domain/intake.py`; malformed payloads receive FastAPI's standard 422 response | No `preferred_output_format` input exists, so that catalog item is not applicable to the current API contract. Validation errors use FastAPI's shape rather than a BuildWise-specific normalized 422 model |
| Input Guardrail Processor | ✅ Built | `application/input_guardrail.py` recursively screens typed intake and clarification payloads before persistence/model use; `security/content.py` detects high-confidence prompt-injection and credential patterns; rejected input receives a normalized `INPUT_GUARDRAIL_REJECTED` response | This is deliberately deterministic rather than a broad semantic harmful-request classifier. Detection reports contain pattern names only and do not echo submitted secrets |
| Completeness Evaluator | 🟡 Partial / embedded | `DiscoveryResult.completeness` is a rich `CompletenessResult`; domain validators enforce score/percentage, blocking-unknown, continuation, and clarification consistency; `route_after_discovery` routes deterministically | Completeness is produced inside the Primary-tier Discovery Agent task, not by a separate deterministic/fast classifier. There is no deterministic fallback scorer or explicit assumption fallback when the maximum clarification round is reached |
| Clarification Question Generator | 🟡 Partial / embedded | The Discovery task produces typed `ClarificationQuestionSet` data; domain validators enforce answer types/options and the Flow persists, displays, validates, and resumes answers | It is not a focused processor; it shares the Discovery Agent call. Duplicate/history awareness is prompt-driven, and no deterministic missing-dimension fallback template exists |
| Preliminary Capability Classifier | 🟡 Partial / embedded | Discovery produces `CapabilityClassification`; deterministic early-market and specialist policies consume its flags and signals | Classification is produced by the Discovery Agent rather than a separate fast/hybrid classifier, with no deterministic fallback classifier |
| Initial Product Definition Validator | 🟡 Partial | Pydantic/domain validators cover Product Definition and Requirements structure, ownership, IDs, traceability, decisions, and many testability rules; task guardrails re-use selected domain checks; `ProductPlanningResult` validates aggregate ownership | No canonical `ProductDefinitionValidationResult`, unified contradiction/duplicate/untestable-requirement report, or bounded semantic repair handoff exists |
| Specialist Planner | 🟡 Built with documented divergence | `planning/planner.py`, `policies.py`, and `execution_graph.py` deterministically select specialists, explain reasons, build dependencies/groups, and apply coarse budget trimming | The catalog says a model/hybrid planner and requires Market & GTM in the specialist plan. The implemented PRD deliberately uses pure Python and routes optional Market & GTM earlier, outside the Technical Planning plan. “Degraded mode” and token-category outputs are absent |
| Cost Budget Controller | 🟡 Partial | `FlowRuntimeLimits`, planner budget policy, clarification/revision limits, and Flow checks enforce token and reliably-known LLM cost limits; optional specialists can be trimmed before execution | No single controller runs before every agent/tool call. Tool-call and execution-time limits are not enforced; actual agent-run limits are only approximated during planning; no runtime degraded-mode transition or remaining-budget result exists |
| Tool Policy Manager | 🟡 Partial | `tools/registry.py::ToolRegistry` is a default-deny key registry with lazy construction, duplicate prevention, credential gating, and agent-contract tool selection | Missing structured per-tool input/output policies, domain restrictions, timeouts, retries, result/output-size limits, invocation accounting, and normalized tool errors |
| Tool Output Sanitizer | ✅ Built | `tools/sanitizer.py` wraps every tool resolved by `ToolRegistry`, marks data untrusted, removes lines containing indirect prompt-injection patterns, redacts recognized credentials, normalizes non-string output, and enforces a 50,000-character limit before content reaches an Agent | This is an MVP deterministic sanitizer, not a general malware/content-classification service. Tool calls made outside the registry are intentionally unsupported and would bypass this boundary |
| Agent Output Validator | 🟡 Partial | Every task uses `TaskOutput.pydantic` guardrails; `tasks/guardrails.py` provides type, non-empty collection, ownership, domain, and Lead Review checks; Pydantic models contain extensive agent-specific rules | No unified `AgentOutputValidationResult`; unsupported claims, placeholder text, citation existence, source credibility, recommendation-to-requirement relevance, and semantic contradictions are not generally checked |
| Output Repair Processor | 🟡 Partial / CrewAI-native | Task guardrail failures return corrective instructions and CrewAI retries according to `guardrail_max_retries` | There is no separate fast-model repair processor, no canonical repaired-output contract, and the catalog's maximum-one-repair/revalidate-once behavior differs from the configured retry loop (normally two retries) |
| Cost Aggregator | ✅ Built | `application/cost_aggregator.py` collects Product, GTM, Solution, AI, Security, and QA implementation estimates into `domain/costs.py::CostSummary`, retaining source ownership and totaling only compatible currency/frequency groups | The normalized model is deliberately simpler than all recommended analytical fields: it does not infer engineering-effort categories, scaling drivers, optimization opportunities, exchange rates, or annualized totals. This avoids model-invented calculations |
| Lead Review Validator | 🟡 Partial | `LeadReview.validate_decision_consistency`, `require_review_consistency`, review routing, target validation, and bounded deterministic revision routing prevent inconsistent approval and unrestricted full restarts | It does not enforce at most one revision request, prove each finding references an actual source section, or emit a canonical `LeadReviewValidationResult`. Multiple bounded targets in one review round are supported intentionally |
| Blueprint Assembler | ✅ Built | `reporting/assembler.py::BlueprintAssembler` deterministically builds all canonical sections from approved artifacts, `CostSummary`, Lead Review, warnings/limitations, and usage | It does not attach a persisted CrewAI trace summary. Source ownership is preserved mainly in section placement and cost-source labels rather than through a complete provenance graph |
| Final Output Validator | ✅ Built | The pre-assembly `validation/output_validator.py` gate remains, and `validation/final_output_validator.py` now receives the actual assembled `ProductBlueprint` before storage/completion. It validates the canonical ordered section set, nonblank content, unresolved placeholders, rendered-title alignment, structural HTTP(S) references, project-cost estimate disclosure, risks/assumptions/questions/limitations/phases disclosure, usage totals, and exact Markdown freshness | URL validation is structural; it does not make network requests to prove that a referenced page is currently reachable |
| Markdown Renderer | ✅ Built with documented sequence | `reporting/markdown_renderer.py` deterministically renders ordered sections and usage; each section now renders its summary so disclosures are present in the deliverable; filesystem/S3 storage occurs only after final validation | BuildWise validates both the typed blueprint and its already-rendered Markdown in one post-assembly gate. This intentionally differs from the catalog's suggested validator-before-renderer ordering because the requested control must catch Markdown-only defects |
| Session Manager | ✅ Built | `api/v1/consultation_service.py::ConsultationService` creates, checkpoints, runs, pauses, resumes, reconstructs, fails, and exposes consultation state/results | Active execution tracking is process-local; an application restart marks in-flight work failed rather than resuming it automatically |
| Flow State Repository | ✅ Built | `persistence/flow_store.py::BuildWiseFlowStore`, SQLAlchemy repositories, and artifact versioning persist intake, discovery, questions/answers, planning outputs, `CostSummary`, Lead Review, revisions, blueprint, usage, errors, and report metadata | The implementation uses generic versioned artifact JSON rather than dedicated columns/tables for every catalog artifact, which is an intentional MVP persistence design |
| Usage and Cost Tracker | 🟡 Partial | `application/usage_aggregator.py` appends per-Crew `UsageRecord`s and totals tokens, provider requests, duration, and explicitly supplied provider/model/cost metadata; usage JSON is persisted | CrewAI aggregate metrics do not expose provider/model/cost, so ordinary cost remains `null`. Tool calls, retries, failed calls, per-agent attribution, and degraded-mode decisions are not instrumented; no model-pricing table exists by design |
| Error Normalizer | 🟡 Partial | Canonical `SessionError` records exist and background Flow exceptions are converted to a stable failure record | There is no centralized mapper for Pydantic, provider, rate-limit, tool, timeout, persistence, HTTP conflict, and unknown exceptions. Raw exception text is still used in the background failure message |
| Rate Limiter | 🔴 Missing | Clarification and revision **workflow** limits exist in Flow state | No per-IP/API limiter, active-session cap, answer-submission limiter, retry-abuse protection, in-memory limiter, or Redis integration exists |
| Trace Adapter | 🟡 Partial | `CREWAI_TRACING_ENABLED` is passed to the Flow and all Crew factories; Flow stages also emit structured events | There is no BuildWise trace adapter that binds request/session/flow IDs into CrewAI traces, persists trace IDs, or explicitly records tools, retries, pauses, failures, latency, and usage as a correlated application trace |
| Structured Logger | 🟡 Partial | `config/logging.py` configures Structlog JSON; request middleware binds request/session/flow/trace/stage keys and logs latency; Flow/service code emits stage and session events | Most non-HTTP events do not consistently bind agent/task/tool/status/retry/cost fields. There is no centralized sensitive-value/redaction processor, so the catalog's “must not log” policy is convention rather than enforcement |
| Health and Readiness Service | 🟡 Partial | `/health` reports process identity; `/ready` checks database connectivity and LLM-provider configuration | `/metrics/summary` is missing. Readiness does not separately verify schema/persistence readiness, S3 report storage, configured tools, or live provider reachability |

## Highest-priority catalog gaps

| Priority | Gap | Why it matters |
|---|---|---|
| 1 | Runtime Cost Budget Controller completion | Tool-call, elapsed-time, retry, and actual execution-count limits exist as configuration/model fields but are not consistently enforced around runtime operations |
| 2 | Tool Policy Manager completion | Tool keys are allowlisted and output is now sanitized/size-limited, but execution constraints, timeouts, accounting, and normalized failures remain absent |
| 3 | Rate Limiter | Public API/session abuse controls are absent even though workflow-internal round limits exist |
| 4 | Unified error normalization and redaction | Failure and logging behavior is not consistently safe or stable across provider, tool, persistence, and validation boundaries |
| 5 | Separate/fallback lightweight classifiers | Completeness, clarification generation, and preliminary capability classification currently share the Primary-tier Discovery Agent and have no deterministic fallback path |

## Catalog inconsistencies requiring an architecture decision

| Catalog statement | Current/other-contract position | Required decision |
|---|---|---|
| Market & GTM is always included by the Specialist Planner | The implemented specialist-planner PRD and target flow route Market & GTM conditionally **before** Product Planning and forbid it from the Technical Planning plan | Update the catalog to the implemented early-market model, or replace the implemented planner/flow contract |
| Specialist Planner may use a balanced model | The implemented planner PRD explicitly requires deterministic Python with no LLM | Keep the deterministic planner and correct the catalog, or formally authorize a model-assisted planning redesign |
| Final Output Validator receives `ProductBlueprint` before Markdown rendering | BuildWise now retains the pre-assembly state gate and adds a post-assembly validator that checks both the typed blueprint and already-rendered Markdown before storage | Update the catalog to the stronger implemented sequence, or split rendering into a second stage and add another Markdown-specific validator |
| Output Repair allows one fast-model attempt | Current CrewAI task guardrails use their native retry loop, generally configured for two retries | Standardize on native guardrail retries or introduce the catalog's dedicated one-shot repair service |

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
| Per-tier cost tracking (doc's entire §6-§9 cost comparison implies costs get measured) | 🟡 Partial | The Flow constructs one `UsageRecord` per Crew and aggregates tokens, successful requests, and duration. The aggregator retains provider, model, and estimated cost when reliable metadata is supplied, but CrewAI's aggregate `UsageMetrics` does not currently expose those fields, so ordinary runs keep cost `null` and tier-specific reporting remains incomplete |

## Key misalignments to resolve

1. **Reviewer tier has no cost/capability separation from Architecture tier** — the doc's core argument ("Opus/Terra only for the reviewer, Sonnet/Luna everywhere else, because the reviewer runs once and can afford to be pricier") is moot today since `lead_reviewer_model` and `architect_model` default to the identical `gpt-5.2`.
2. **Security Architect and QA Architect tier placement disagrees between code and docs** — both the doc under review and `.env.example`'s comments say Primary/Balanced tier; `agents/security_architect.py` and `agents/qa_evaluation_architect.py` actually declare `ModelTier.ARCHITECT`. Pick one and reconcile the other two.
3. **The doc's Fast tier has no agents to route** — until Completeness Evaluator / Capability Classifier / Output Repair agents exist (none do), `FAST_MODEL` is configured but dead weight.
4. **The doc assumes the Specialist Planner is a model call; it isn't** — it's deterministic Python by design (`prds/05_specialist_planner.md`). The doc should either be corrected or explicitly note the planner as a non-LLM exception.
5. **`.env.example` documents a whole cross-provider evaluation subsystem (`EVALUATION_*`, `CLAUDE_*_MODEL`, `MODEL_FALLBACK_*`) that has zero corresponding fields in `Settings` and zero implementing code** — right now these env vars do nothing if set, which is a silent-failure trap for anyone following `.env.example` expecting them to work.
