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
| Early Market Router | 🔴 Missing | No deterministic function yet decides `include_market_and_gtm: bool` before constructing the Product Planning Crew. Small and well-scoped — see below |
| Product Planning Crew | ✅ Built | `crews/product_planning.py`, incl. `assemble_product_planning_result` → `ProductPlanningResult` |
| Deterministic Specialist Planner | 🔴 Missing | `src/buildwise/planning/` doesn't exist. `SpecialistExecutionPlan` (the model it must produce) exists and is already consumed by Technical Planning Crew — only the deterministic rule engine itself is missing |
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

### 1. Deterministic Specialist Planner — `src/buildwise/planning/`
Pure function(s): `(DiscoveryResult, ProductDefinition, RequirementsSpecification) -> SpecialistExecutionPlan`,
following the example rules already sketched in `prds/crews_refactor_plan.md`
§10 (AI capability → select AI Architecture; sensitive data/regulated domain
→ select Security; blueprint requested → select Solution + QA). Note
`flows/routing.py::build_specialist_routing_plan` already implements very
similar logic against a different, older model
(`SpecialistRoutingPlan`/`SpecialistRoutingDecision` in `routing.py` itself,
not `domain/specialist_planning.py::SpecialistExecutionPlan`) — decide
whether to port that logic to emit the newer model or keep both (routing.py's
version predates the Crew refactor). This also needs a much smaller
**Early Market Router**: a boolean decision (does the idea need commercial
validation before product definition?) that can live in the same module.

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

- `flows/routing.py`'s `SpecialistRoutingPlan` and
  `domain/specialist_planning.py`'s `SpecialistExecutionPlan` are two
  different models covering overlapping ground (both represent "which
  specialists run and why"). Reconcile before building the planner in step 1
  so the Technical Planning Crew and the Flow agree on one shape.
- No tests exist yet (`tests/*/` are empty scaffolding). Every PRD's testing
  section describes what to cover once the Flow lands.
- `reporting/` and `validation/` currently contain only a one-line docstring
  each (`"""Blueprint assembly and rendering."""` /
  `"""Deterministic and model-assisted validation."""`) — no code yet; first
  real content in either will define their shape.
