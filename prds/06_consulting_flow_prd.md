# BuildWise AI — CrewAI Consulting Flow PRD

## Goal

Implement the main CrewAI Flow that orchestrates the existing architecture.

The Flow owns:
- State transitions
- Routing
- Pause / Resume
- Crew execution
- Planner execution
- Revision routing
- Completion / Failure

The Flow must not contain business reasoning or specialist-selection logic.

---

## Flow

```text
Start
  ↓
Validate Intake
  ↓
Discovery Crew
  ↓
Discovery Router
  ├── Clarification
  │      ↓
  │ Pause → Resume → Discovery
  │
  └── Continue
          ↓
Early Market Decision
          ↓
Product Planning Crew
          ↓
Specialist Planner
          ↓
Technical Planning Crew
          ↓
Lead Review Crew
          ↓
Review Router
      ├── Revision → Re-run affected Crew
      ├── Approved → Blueprint Builder
      └── Rejected → Fail
```

---

## Target Files

```text
src/buildwise/flows/
├── __init__.py
├── consulting_flow.py
├── routing.py
├── state.py
└── smoke.py
```

Reuse existing:
- FlowState
- Routing helpers
- Planner
- Crew factories
- Domain models

---

## Required Steps

1. Validate intake and initialize Flow state.
2. Execute Discovery Crew and store `DiscoveryResult`.
3. Route Discovery:
   - Clarification
   - Continue
   - Fail
4. Pause/Resume for clarification using structured answers.
5. Call `planner.should_include_early_market_context(...)`.
6. Execute Product Planning Crew and store `ProductPlanningResult`.
7. Call `planner.create_execution_plan(...)`.
8. Store `SpecialistExecutionPlan`.
9. Execute Technical Planning Crew using only the execution plan.
10. Store `TechnicalPlanningResult`.
11. Execute Lead Review Crew.
12. Route:
    - Approved
    - Approved with limitations
    - Revision required
    - Rejected
13. Re-run only affected Crew for revisions.
14. Call `blueprint_builder.build(...)` after approval.

---

## Flow State

Maintain:

- Intake
- ProductIdeaContext
- DiscoveryResult
- ProductPlanningResult
- SpecialistExecutionPlan
- TechnicalPlanningResult
- LeadReview
- Revision history
- Usage
- Errors
- Warnings

Prefer aggregate results.

---

## Logging

Emit stage-level events only:

- Flow started
- Discovery completed
- Clarification requested
- Product Planning completed
- Specialist plan created
- Technical Planning completed
- Lead Review completed
- Revision started
- Flow completed
- Flow failed

---

## Out of Scope

- FastAPI
- Database
- Blueprint rendering
- Streaming
- Event bus
- New planner
- New domain models

---

## Implementation Order

1. Flow skeleton
2. Discovery
3. Clarification
4. Product Planning
5. Specialist Planner
6. Technical Planning
7. Lead Review
8. Revision routing
9. Blueprint boundary
10. Tests

---

## Acceptance Criteria

- Native CrewAI Flow
- Typed BuildWiseFlowState
- Discovery works
- Clarification pause/resume works
- Product Planning works
- Planner drives Technical Planning
- Lead Review works
- Revision routing works
- No planner logic inside Flow
- No manual JSON parsing
- Ruff passes
- mypy passes
- Mocked end-to-end Flow test passes
