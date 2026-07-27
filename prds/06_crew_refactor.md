# Crew Refactor PRD

## Goal

Refactor the Crew layer to consume the deterministic `SpecialistExecutionPlan` instead of making specialist-selection decisions internally.

After this refactor:

- Flows own orchestration.
- Planner owns deterministic specialist selection.
- Crews own collaborative reasoning.
- Tasks own individual assignments.
- Agents remain specialists.

No Crew should contain business routing logic.

---

# Current Architecture

```
Discovery Crew
        ↓
Product Planning Crew
        ↓
Specialist Planner
        ↓
Technical Planning Crew
        ↓
Lead Review Crew
```

The planner now produces the canonical:

```
SpecialistExecutionPlan
```

The Technical Planning Crew must consume this plan.

---

# Scope

Refactor only:

```
src/buildwise/crews/
```

Expected files:

```
crews/
├── __init__.py
├── discovery.py
├── product_planning.py
├── technical_planning.py
└── lead_review.py
```

No new crews.

No new agents.

No new tasks.

---

# Discovery Crew

No architectural changes.

Responsibilities:

- create Discovery Agent
- create Discovery Task
- return DiscoveryResult

Must not:

- select specialists
- evaluate budget
- route execution

---

# Product Planning Crew

Responsibilities:

Run:

- optional Market & GTM
- Product Manager
- Business Analyst

Return:

```
ProductPlanningResult
```

Must not:

- choose technical specialists
- evaluate AI need
- evaluate Security
- evaluate QA

---

# Technical Planning Crew

This file receives the biggest refactor.

Current:

Crew decides which specialists participate.

New:

Planner decides.

Crew only executes.

Constructor should become conceptually:

```python
create_technical_planning_crew(
    execution_plan: SpecialistExecutionPlan,
)
```

The Crew must:

- inspect selected specialists
- construct required Agents
- construct required Tasks
- wire task context
- build native CrewAI Crew

The Crew must NOT:

- inspect DiscoveryResult
- inspect ProductPlanningResult
- infer AI need
- infer Security need
- infer QA need
- evaluate budget
- create routing decisions

Those decisions belong exclusively to the planner.

---

# Technical Planning Composition

Example

AI consultation

```
Solution Architect

↓

AI Architect

↓

Security Architect

↓

QA Architect
```

Standard SaaS

```
Solution Architect

↓

Security Architect

↓

QA Architect
```

Prototype

```
Solution Architect
```

The Crew composition must come entirely from
`SpecialistExecutionPlan`.

---

# Lead Review Crew

No structural changes.

Consumes:

- DiscoveryResult
- ProductPlanningResult
- TechnicalPlanningResult

Produces:

```
LeadReview
```

Revision decisions remain Flow responsibilities.

---

# Task Context

Crew must continue wiring Task context.

Example

```
Solution Architecture Task
        ↓
AI Architecture Task
        ↓
Security Task
        ↓
QA Task
```

Only valid dependencies from the execution plan should be connected.

---

# Dynamic Agent Construction

Use existing:

```
AgentFactory
```

Do not instantiate Agents manually.

---

# Dynamic Task Construction

Use existing task factories.

Do not duplicate Task definitions.

---

# Output

Technical Planning Crew returns:

```
TechnicalPlanningResult
```

Product Planning Crew returns:

```
ProductPlanningResult
```

Discovery returns:

```
DiscoveryResult
```

Lead Review returns:

```
LeadReview
```

---

# Validation

After refactor:

✓ No specialist-selection logic remains inside crews.

✓ No budget logic remains inside crews.

✓ No capability evaluation remains inside crews.

✓ Technical Planning Crew consumes only
`SpecialistExecutionPlan`.

✓ Planner becomes the single source of truth for specialist routing.

✓ Existing Agents, Tasks, Skills and Tools remain unchanged.

---

# Acceptance Criteria

- Crews contain orchestration only.
- Planner owns specialist selection.
- Technical Planning Crew is fully driven by `SpecialistExecutionPlan`.
- No duplicated routing logic exists.
- Ruff passes.
- mypy passes.