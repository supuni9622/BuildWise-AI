# BuildWise v2 — Implementation Progress

A from-scratch rebuild of the BuildWise consulting backend under
`src/buildwisev2/`, built strictly from the specs in `prds/`. Nothing is
imported or copied from `src/buildwise` (the previous implementation) —
only the CrewAI framework itself is shared. Verified against the
installed CrewAI 1.15.5 API directly (Task/Crew/Agent/Flow/Skills/
persistence introspection) rather than assumed, and validated with a live
end-to-end run against a real OpenAI model through the HTTP API (see
"Live validation" below).

Legend: `[x]` done · `[~]` partial / simplified · `[ ]` not started

## Architecture

```
web/ (existing Next.js frontend, untouched)
   -> FastAPI (buildwisev2/api) — matches web/'s REST contract exactly
        -> Consulting Flow (buildwisev2/flows), SQLite-checkpointed
             -> Discovery Crew
             -> Product Planning Crew (Market&GTM? -> Product Manager -> Business Analyst)
             -> Deterministic Specialist Planner (buildwisev2/planning)
             -> Technical Planning Crew (Solution -> AI? -> Security? -> QA?)
             -> Lead Review Crew -> revision loop -> blueprint assembly
```

Only 4 business Crews are built (per `04_crews_refactor_plan.md`) — the
one-agent-per-crew topology in `01/02_crew*` was explicitly superseded by
the refactor plan and was never built.

## Domain layer — `buildwisev2/domain/` — DONE

All PRD artifact models: `DiscoveryResult`, `ProductDefinition`,
`RequirementsSpecification`, `MarketAndGTMStrategy`, `SolutionArchitecture`,
`AIArchitecture`, `SecurityArchitecture`, `QAEvaluationPlan`, `LeadReview`
(with a decision-consistency `model_validator`), `SpecialistExecutionPlan`,
`ProductBlueprint`, aggregate results (`ProductPlanningResult`,
`TechnicalPlanningResult`), and intake models. Field-level fidelity covers
every responsibility listed in the PRDs at a summary level, not every
itemized sub-bullet — safe to extend, all callers use keyword args.

## Config — `buildwisev2/config/settings.py` — DONE

`Settings` (pydantic-settings): `ModelTier` resolution, CrewAI runtime
flags, retries, `FlowRuntimeLimits`, CORS origins, API host/port, SQLite
persistence path. Reads **only** `BUILDWISEV2_`-prefixed process env vars
— deliberately does not load the shared repo-root `.env` (pydantic-settings'
dotenv source does not filter by `env_prefix` the same way it filters OS
env vars, so loading it caused real collisions with v1's unprefixed names
like `CORS_ALLOWED_ORIGINS`). Provider credentials (`OPENAI_API_KEY`, ...)
are read directly by CrewAI/LiteLLM from the process environment
regardless, so this doesn't affect model calls.

## Agents layer — `buildwisev2/agents/` — DONE

- `contracts.py` — 9 `AgentType`s + `AgentContract` (role/goal/backstory/
  model_tier/tool_keys)
- `factory.py` — `AgentFactory.create(AgentType) -> crewai.Agent`, wiring
  both tools and Skills
- `skills/<kebab-case-role>/SKILL.md` — 9 original Skill packages (one per
  specialist), loaded via CrewAI's inline-frontmatter-string form. **Note**:
  passing a bare directory `Path` to `Agent(skills=[...])` makes CrewAI
  treat it as a *search root* and pulls in every Skill under it
  (`crewai.skills.loader.discover_skills`) — the factory instead reads each
  `SKILL.md`'s raw text and passes the `"---\n..."` string, which loads
  exactly one Skill via `load_skill`'s inline-string branch. Verified: each
  `AgentType` gets exactly its own Skill (`tests/unit_v2/agents/test_skills.py`).
- `tools/registry.py` — resolves `AgentContract.tool_keys` -> official
  `crewai_tools` instances (`SerperDevTool`, `ScrapeWebsiteTool`); only the
  Market & GTM Strategist has tools attached.

## Tasks layer — `buildwisev2/tasks/` — DONE

`guardrails.py`, `formatting.py` (shared revision-instructions +
upstream-artifact-context helpers), and all 9 specialist task factories.
Every architecture-dependent task (`ai_architecture`, `security_architecture`,
`qa_evaluation`, `requirements`, `product_definition`) accepts **either** a
live same-Crew `Task` (native `context=`) **or** a prior approved artifact
(kickoff-placeholder text) for its upstream dependency — this is what
powers revision-aware Crew composition (see below). `specialist_planning.py`
task intentionally does not exist; planning is deterministic Python per
PRD 05.

## Crews layer — `buildwisev2/crews/` — DONE

`discovery.py`, `product_planning.py`, `technical_planning.py`,
`lead_review.py`, `_shared.py` (revision routing helper). No registry
module, per the refactor plan.

**Revision-aware composition** (beyond the original PRD's literal
"rerun the whole Crew"): a task regenerates only when its own
`RevisionTarget` was requested, or an upstream dependency within the same
Crew is also regenerating; everything else is skipped entirely (no LLM
call) and its prior artifact is reused as static context for whatever does
run. Verified for every cascade case in
`tests/unit_v2/crews/test_revision_composition.py` and exercised live (a
real `revision_required` -> targeted re-run -> `rerun_lead_review` loop
completed correctly end to end).

## Planning layer — `buildwisev2/planning/` — DONE

`policies.py`, `execution_graph.py`, `planner.py`. Selection reads only
structured signals (`discovery.capability_classification.*` flags/enums
and a small controlled-vocabulary `specialist_signals` list) — never
free-text keyword matching, per the PRD's "avoid keyword-only
classification" goal. Verified live: correctly selected Solution +
Security + QA (and correctly omitted AI) for a real internal tool
description with authentication and driver PII.

## Flows layer — `buildwisev2/flows/` — DONE

- `state.py` — `ConsultingFlowState` (adds a `blueprint` field), `FlowStage`
- `routing.py` — pure routing helpers, independently unit-testable
- `consulting_flow.py` — native `Flow[ConsultingFlowState]`: Discovery ->
  clarification pause/resume -> Product Planning -> Specialist Planner ->
  Technical Planning -> Lead Review -> revision loop -> `on_blueprint_ready`
  (calls `reporting.build_blueprint`, a pure rendering step — no LLM call)

**Bug found and fixed via the live run below**: exhausting the
clarification-round budget while Discovery still reported
`completeness.can_continue=False` made `route_discovery` return `CONTINUE`
without ever correcting that field, so `run_specialist_planning` crashed
(`SpecialistPlanner.create_execution_plan` hard-fails on incomplete
Discovery — correct behavior for the planner in isolation). Fixed with
`routing.force_continue_discovery`: when the Flow overrides Discovery's
own "still incomplete" judgment, it now rewrites the artifact to
`decision=CONTINUE_WITH_LIMITATIONS`, `completeness.can_continue=True`,
and appends an explicit limitation — so the artifact honestly reflects the
Flow's decision instead of contradicting it. Covered by
`test_consulting_flow_force_continues_after_clarification_rounds_exhausted`
in `tests/unit_v2/flows/test_consulting_flow.py`.

**Persistence**: `ConsultingFlow(persistence=SQLiteFlowPersistence(...))`
checkpoints `self.state` via the native `crewai.flow.persistence`
interface after every stage transition (`self._checkpoint(...)`), *not*
via the `@persist` class decorator — that decorator's auto-save wiring
turned out to be non-trivial to verify safe for a Flow with loops
(`run_lead_review`/`rerun_lead_review`), so explicit checkpoint calls were
chosen as the safer, fully-tested path. Resume contract (verified,
documented honestly rather than oversold): restoring a persisted session
after a process restart hydrates `ConsultingFlowState` immediately (status
and blueprint if it had completed are readable right away), but CrewAI's
persistence restores `self.state` only — not the in-memory
already-completed-method bookkeeping — so continuing an in-flight session
after restart would re-enter at `run_discovery`. In practice this matches
the same tolerant re-entry behavior the clarification pause/resume path
already relies on.

**Clarification round limit**: verified live — round 0 asked 9 real
questions, terse round-1 answers were judged insufficient and it asked
again, and at round 2 (`>= maximum_clarification_rounds`) the Flow
correctly force-continued instead of looping forever.

## Reporting layer — `buildwisev2/reporting/blueprint_builder.py` — DONE

Deterministic `build_blueprint(...)` — pure rendering, no LLM call. Only
selected specialists produce a section (an unselected optional specialist
is correctly absent, not an empty placeholder). Limitations aggregated
across every artifact are de-duplicated (specialists frequently restate
the same upstream limitation verbatim — discovered via the live run, fixed
and verified).

## API layer — `buildwisev2/api/` — DONE (matches existing `web/` frontend)

- `schemas.py` — request/response models mirroring `web/app/page.tsx`'s
  TypeScript types exactly
- `store.py` — `ConsultationStore`: in-memory session index backed by
  `SQLiteFlowPersistence`; falls back to restoring from SQLite when a
  consultation isn't in the in-memory index (e.g. after a restart)
- `service.py` — translates the frontend's intake shape (title,
  known_features, target_platforms, ai/sensitive-data hints, ...) into
  `ProductIdeaRequest` by composing them into `raw_idea` text and
  `known_constraints` (the domain layer stays intentionally minimal;
  UI-shape translation lives here, not in the domain); runs
  `ConsultingFlow.kickoff()` in a background thread so `POST` returns
  immediately; maps `ConsultingFlowState` -> the frontend's status/stage
  vocabulary
- `app.py` — FastAPI app, CORS, the 4 routes:
  `POST /api/v1/consultations`, `GET /api/v1/consultations/{id}`,
  `POST /api/v1/consultations/{id}/clarifications`,
  `GET /api/v1/consultations/{id}/result`
- `__main__.py` — `python -m buildwisev2.api` runs on `0.0.0.0:8080`
  (matches `web/.env.example`'s `NEXT_PUBLIC_BUILDWISE_API_URL`)

`web/` itself was not modified — it already speaks this exact contract.

### Running it against the frontend

```bash
# backend
OPENAI_API_KEY=... uv run python -m buildwisev2.api

# frontend (separate terminal)
cd web && npm run dev
```

## Live validation (real OpenAI models, real HTTP calls)

Ran a full consultation through the actual FastAPI server (not mocked)
for an internal logistics scheduling tool:

- Discovery asked 9 substantive, specific clarification questions
- Terse round-1 answers correctly triggered a second clarification round;
  round-2 correctly force-continued via the round-limit safety valve
- Product Planning produced a coherent product definition + requirements
- Specialist Planner correctly selected Solution + Security + QA and
  correctly omitted AI Architecture (no AI capability in this product)
- Technical Planning produced a real solution/security/QA design
- Lead Review returned `revision_required`; the Flow re-ran only the
  targeted Crew and re-reviewed; second pass returned
  `approved_with_limitations`
- Blueprint assembled: 7 sections, ~36KB of coherent Markdown, specific
  (non-generic) open questions and limitations

This is strong evidence the full stack — API, Flow, Crews, Tasks, Agents,
Skills, planner, revision loop, and blueprint assembly — works together
correctly end to end, not just in mocked unit tests.

## Not built (explicitly out of scope for this phase)

- Database persistence beyond the SQLite Flow-state checkpoint (no
  Postgres/session-metadata layer)
- Blueprint export formats beyond Markdown (PDF, etc.)
- Streaming responses / websockets
- MCP/Apps integration
- Cost/usage aggregation across Crew executions
- True mid-flow resume-without-recomputation after a process restart (see
  the Flows section's honest resume-contract note above)

## Validation status — ALL PASSING

- [x] `uv run ruff format src/buildwisev2 tests/unit_v2` — clean
- [x] `uv run ruff check src/buildwisev2 tests/unit_v2` — clean
- [x] `uv run mypy src/buildwisev2` — `Success: no issues found in 56 source files`
- [x] `uv run pytest tests/unit_v2 -q` — **56/56 passed**, zero live LLM
      calls in the automated suite (mocks `crewai.Crew.kickoff` with real
      `CrewOutput`/`TaskOutput` instances to exercise the actual
      `@start`/`@router`/`@listen` graph, and a real FastAPI `TestClient`
      for the API layer)
- [x] Live end-to-end run against the real API with a real OpenAI key (see
      above) — not part of the automated suite (costs money, takes
      minutes), but proves the whole stack works together for real

Test breakdown (`tests/unit_v2/`, 10 files, 56 tests):
`planning/` (9), `tasks/` (7), `crews/` (9 composition + 6 revision-cascade),
`flows/` (2 flow + 2 persistence), `agents/` (10 skills/tools),
`tools/` (4), `reporting/` (2), `api/` (6).

## Suggested next steps (not started)

1. Postgres/session-metadata persistence layer for consultation listing,
   auth, multi-tenant isolation (SQLite Flow-state checkpointing covers
   crash recovery for a single consultation, not a real session store).
2. True mid-flow resume: track and restore `_completed_methods` /
   `_method_outputs` (or re-derive equivalent) so a restart doesn't
   re-enter at `run_discovery`.
3. Blueprint PDF/DOCX export.
4. Cost/usage aggregation across Crew executions, surfaced in the API.
