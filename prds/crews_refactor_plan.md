# BuildWise AI
# Crew Layer Refactor Plan

**Version:** 1.0  
**Status:** Approved for implementation  
**Scope:** Refactor the existing Crew layer before implementing the main CrewAI Flow  
**Framework:** CrewAI 1.15.6  

---

# 1. Purpose

This document defines the refactor required for the BuildWise Crew layer.

The current implementation contains one Crew per specialist Agent:

```text
Discovery Agent           → Discovery Crew
Product Manager           → Product Definition Crew
Business Analyst          → Requirements Crew
Market Strategist         → Market & GTM Crew
Solution Architect        → Solution Architecture Crew
AI Architect              → AI Architecture Crew
Security Architect        → Security Architecture Crew
QA Architect              → QA & Evaluation Crew
Lead Reviewer             → Lead Review Crew
```

Although this structure is technically valid, most Crews contain only:

```text
1 Agent
1 Task
```

This creates a near one-to-one mapping between Agents and Crews and does not reflect the BuildWise user-facing consulting journey.

The refactor will consolidate the current Crew layer into four meaningful business Crews while keeping all existing Agent contracts, Skills, Tools, and Task factories.

---

# 2. Refactor Goal

The refactored runtime must follow this architecture:

```text
FastAPI
   ↓
CrewAI Flow
   ↓
Focused business Crews
   ↓
Native CrewAI Tasks
   ↓
Native CrewAI Agents
   ↓
Structured Pydantic outputs
```

The CrewAI Flow remains the deterministic orchestrator.

The Crews become collaborative reasoning units that reflect the actual BuildWise process.

The target Crew topology is:

```text
1. Discovery Crew
2. Product Planning Crew
3. Technical Planning Crew
4. Lead Review Crew
```

---

# 3. User-Facing Business Flow

The refactor must preserve the original BuildWise workflow:

```text
Product idea
   ↓
Input validation
   ↓
Discovery analysis
   ↓
Completeness evaluation
   ↓
Clarification loop when needed
   ↓
Preliminary capability classification
   ↓
Optional early market context
   ↓
Product planning
   ↓
Requirements definition
   ↓
Deterministic specialist planning
   ↓
Technical specialist planning
   ↓
Lead review
   ↓
Targeted revision loop
   ↓
Output validation
   ↓
Deterministic blueprint generation
   ↓
Final report
```

The refactor changes the implementation grouping, not the business process.

---

# 4. Architectural Responsibilities

## Flow

The CrewAI Flow owns:

- state
- routing
- branching
- clarification loops
- pause and resume
- human feedback
- maximum clarification rounds
- specialist selection
- Crew execution order
- Crew concurrency
- revision routing
- revision limits
- persistence
- cost aggregation
- output validation
- blueprint generation
- completion status

## Crew

A Crew owns a focused collaborative business outcome.

Examples:

```text
Product Planning Crew
    → ProductDefinition
    → RequirementsSpecification
```

```text
Technical Planning Crew
    → SolutionArchitecture
    → optional AIArchitecture
    → optional SecurityArchitecture
    → optional QAEvaluationPlan
```

## Task

A Task owns one concrete assignment and one structured output.

## Agent

An Agent owns specialist reasoning and expertise.

## Skill

A Skill owns reusable methodology.

## Tool

A Tool owns an external action such as web search, scraping, or GitHub search.

---

# 5. Existing Assets to Keep

The following layers remain valid and should not be rebuilt.

## Keep all Agent contracts

```text
src/buildwise/agents/
```

Including:

- Product Discovery Analyst
- Product Manager
- Business Analyst
- Market & GTM Strategist
- Solution Architect
- AI Architect
- Security Architect
- QA & Evaluation Architect
- Lead Reviewer

## Keep the Agent registry and factory

```text
src/buildwise/agents/registry.py
src/buildwise/agents/factory.py
```

## Keep all CrewAI Skills

```text
skills/
```

## Keep the official CrewAI Tools registry

```text
src/buildwise/tools/registry.py
```

## Keep all native CrewAI Task factories

```text
src/buildwise/tasks/
```

Existing task files remain useful:

```text
src/buildwise/tasks/discovery.py
src/buildwise/tasks/product_definition.py
src/buildwise/tasks/requirements.py
src/buildwise/tasks/market_and_gtm.py
src/buildwise/tasks/solution_architecture.py
src/buildwise/tasks/ai_architecture.py
src/buildwise/tasks/security_architecture.py
src/buildwise/tasks/qa_evaluation.py
src/buildwise/tasks/lead_review.py
```

The refactor changes Crew composition only.

---

# 6. Current Crew Files to Replace

The current Crew package contains:

```text
src/buildwise/crews/
├── __init__.py
├── ai_architecture.py
├── discovery.py
├── lead_review.py
├── market_and_gtm.py
├── product_definition.py
├── qa_evaluation.py
├── registry.py
├── requirements.py
├── security_architecture.py
└── solution_architecture.py
```

The following one-specialist Crew wrappers should be removed or retired:

```text
src/buildwise/crews/product_definition.py
src/buildwise/crews/requirements.py
src/buildwise/crews/market_and_gtm.py
src/buildwise/crews/solution_architecture.py
src/buildwise/crews/ai_architecture.py
src/buildwise/crews/security_architecture.py
src/buildwise/crews/qa_evaluation.py
src/buildwise/crews/registry.py
```

Keep and refactor:

```text
src/buildwise/crews/discovery.py
src/buildwise/crews/lead_review.py
```

Add:

```text
src/buildwise/crews/product_planning.py
src/buildwise/crews/technical_planning.py
```

---

# 7. Target Crew Package

The final Crew package should be:

```text
src/buildwise/crews/
├── __init__.py
├── discovery.py
├── product_planning.py
├── technical_planning.py
└── lead_review.py
```

Do not add a Crew registry for the MVP.

The Flow should import these four Crew factories explicitly.

Explicit imports are preferable because BuildWise has a fixed business workflow rather than a plugin-based Crew system.

---

# 8. Discovery Crew

## File

```text
src/buildwise/crews/discovery.py
```

## Purpose

Convert a product idea and optional clarification answers into a structured discovery result.

## Composition

```text
Discovery Crew
└── Product Discovery Analyst
    └── Discovery Task
```

## Agent

```python
AgentType.PRODUCT_DISCOVERY_ANALYST
```

## Task

```python
create_discovery_task(...)
```

## Output

```python
DiscoveryResult
```

## Process

```python
Process.sequential
```

## Crew configuration

```python
Crew(
    agents=[discovery_agent],
    tasks=[discovery_task],
    process=Process.sequential,
    verbose=settings.crewai_verbose,
    cache=True,
    memory=False,
)
```

## Responsibilities

- idea interpretation
- problem extraction
- target-user identification
- domain classification
- assumptions
- ambiguity detection
- unknowns
- early risks
- clarification questions
- completeness assessment
- preliminary capability classification

## Flow responsibilities after Crew execution

The Flow reads `DiscoveryResult` and decides whether to:

- continue
- pause for clarification
- continue with limitations
- fail

The Crew must not track clarification-round counts or pause execution.

---

# 9. Product Planning Crew

## File

```text
src/buildwise/crews/product_planning.py
```

## Purpose

Convert an approved DiscoveryResult into a complete product and requirements package.

## Composition

```text
Product Planning Crew
├── Market & GTM Strategist — optional
├── Product Manager
└── Business Analyst
```

## Modes

### Standard product-planning mode

```text
Product Manager Task
   ↓
ProductDefinition
   ↓
Business Analyst Task
   ↓
RequirementsSpecification
```

### Early-market-context mode

```text
Market Research / GTM Task
   ↓
MarketAndGTMStrategy
   ↓
Product Manager Task
   ↓
ProductDefinition
   ↓
Business Analyst Task
   ↓
RequirementsSpecification
```

## Crew construction

The Flow decides whether early market context is required before creating the Crew.

Example conceptual signature:

```python
def create_product_planning_crew(
    *,
    discovery_result: DiscoveryResult,
    include_market_and_gtm: bool,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_requests: list[RevisionRequest] | None = None,
) -> Crew:
    ...
```

## Agents

Required:

```python
AgentType.PRODUCT_MANAGER
AgentType.BUSINESS_ANALYST
```

Conditional:

```python
AgentType.MARKET_AND_GTM_STRATEGIST
```

## Tasks

Required:

```python
create_product_definition_task(...)
create_requirements_task(...)
```

Conditional:

```python
create_market_and_gtm_task(...)
```

## Task context

When market context is included:

```python
product_definition_task.context = [market_and_gtm_task]
```

Requirements should consume Product Definition:

```python
requirements_task.context = [product_definition_task]
```

Use native CrewAI Task context inside the same Crew.

Do not manually concatenate raw task outputs.

## Process

```python
Process.sequential
```

## Output strategy

The Crew produces multiple structured task outputs:

- optional `MarketAndGTMStrategy`
- `ProductDefinition`
- `RequirementsSpecification`

The Flow should extract the structured output of each task after Crew execution.

If CrewAI requires one final root artifact for reliable output handling, add a lightweight aggregation Task with a structured model such as `ProductPlanningResult`.

Do not use a generic synthesis Agent solely to package fields.

Prefer deterministic collection by the Flow unless a native CrewAI limitation requires a final structured Task.

## Proposed aggregate model

If needed:

```python
class ProductPlanningResult(BaseModel):
    market_and_gtm: MarketAndGTMStrategy | None = None
    product_definition: ProductDefinition
    requirements: RequirementsSpecification
```

Place this model in the domain layer, not in the Crew module.

Suggested path:

```text
src/buildwise/domain/planning_results.py
```

## Revision behavior

The Flow may rerun this Crew for:

- Product Definition revisions
- Requirements revisions
- Market & GTM revisions

The Crew factory should accept bounded revision requests and pass each request only to the owning Task.

A Requirements revision must not force Market & GTM or Product Definition regeneration unless the Lead Review explicitly identifies a dependency.

---

# 10. Deterministic Specialist Planner

The specialist planner is not a Crew.

It is a pure deterministic application service invoked by the Flow after Product Planning.

It consumes:

- DiscoveryResult
- ProductDefinition
- RequirementsSpecification
- user-requested consultation scope
- budget policy
- risk signals

It produces:

```python
SpecialistExecutionPlan
```

The planner selects the composition of the Technical Planning Crew.

Example rules:

```python
if implementation_blueprint_requested:
    select(SpecialistType.SOLUTION_ARCHITECTURE)

if has_ai_capability:
    select(SpecialistType.AI_ARCHITECTURE)

if contains_sensitive_data or regulated_domain:
    select(SpecialistType.SECURITY_ARCHITECTURE)

if implementation_blueprint_requested:
    select(SpecialistType.QA_AND_EVALUATION)
```

Specialist selection must remain predictable, explainable, and testable.

---

# 11. Technical Planning Crew

## File

```text
src/buildwise/crews/technical_planning.py
```

## Purpose

Produce the complete technical implementation plan using only the specialists selected by the deterministic planner.

## Dynamic composition

```text
Technical Planning Crew
├── Solution Architect — normally required
├── AI Architect — conditional
├── Security Architect — conditional
└── QA & Evaluation Architect — conditional
```

## Example compositions

### Standard software product

```text
Solution Architect
   ↓
QA & Evaluation Architect
```

### AI product

```text
Solution Architect
   ↓
AI Architect
   ↓
Security Architect
   ↓
QA & Evaluation Architect
```

### Sensitive non-AI product

```text
Solution Architect
   ↓
Security Architect
   ↓
QA & Evaluation Architect
```

### Lightweight technical consultation

```text
Solution Architect
```

## Factory signature

Conceptual signature:

```python
def create_technical_planning_crew(
    *,
    requirements: RequirementsSpecification,
    specialist_plan: SpecialistExecutionPlan,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_requests: list[RevisionRequest] | None = None,
) -> Crew:
    ...
```

The actual signature may include ProductDefinition when needed for context.

## Agents

Create only the Agents selected by the plan.

Example:

```python
agents: list[Agent] = []

tasks: list[Task] = []

if plan.includes(SpecialistType.SOLUTION_ARCHITECTURE):
    solution_agent = agent_factory.create(AgentType.SOLUTION_ARCHITECT)
    solution_task = create_solution_architecture_task(...)
    agents.append(solution_agent)
    tasks.append(solution_task)

if plan.includes(SpecialistType.AI_ARCHITECTURE):
    ai_agent = agent_factory.create(AgentType.AI_ARCHITECT)
    ai_task = create_ai_architecture_task(...)
    agents.append(ai_agent)
    tasks.append(ai_task)
```

## Task dependencies

The standard dependency sequence is:

```text
Solution Architecture Task
   ↓
AI Architecture Task — when selected
   ↓
Security Architecture Task — when selected
   ↓
QA & Evaluation Task — when selected
```

Use native Task context only where a dependency exists.

### AI Architecture context

```python
ai_task.context = [solution_task]
```

### Security context

When AI exists:

```python
security_task.context = [solution_task, ai_task]
```

Without AI:

```python
security_task.context = [solution_task]
```

### QA context

Include only selected architecture tasks:

```python
qa_context = [solution_task]

if ai_task is not None:
    qa_context.append(ai_task)

if security_task is not None:
    qa_context.append(security_task)
```

## Process

```python
Process.sequential
```

The initial implementation should favor correctness and explicit dependencies over maximum concurrency.

Flow-level concurrency may still run Market & GTM in parallel with the Technical Planning Crew when safe.

## Output strategy

The Crew may produce:

- `SolutionArchitecture`
- optional `AIArchitecture`
- optional `SecurityArchitecture`
- optional `QAEvaluationPlan`

The Flow should collect each structured Task output.

If one final root artifact is required, use a domain model such as:

```python
class TechnicalPlanningResult(BaseModel):
    solution_architecture: SolutionArchitecture
    ai_architecture: AIArchitecture | None = None
    security_architecture: SecurityArchitecture | None = None
    qa_evaluation: QAEvaluationPlan | None = None
```

Do not use an extra generic Agent merely to aggregate fields.

## Revision behavior

The Flow may rerun this Crew with a subset of Tasks.

Examples:

- only AI Architecture revision
- only Security Architecture revision
- Solution Architecture revision followed by dependent AI/Security/QA regeneration
- only QA revision

The Flow determines dependency impact before constructing the revised Crew.

---

# 12. Lead Review Crew

## File

```text
src/buildwise/crews/lead_review.py
```

## Purpose

Perform the final holistic quality review across all approved artifacts.

## Composition

```text
Lead Review Crew
└── Lead Reviewer
    └── Lead Review Task
```

## Agent

```python
AgentType.LEAD_REVIEWER
```

## Task

```python
create_lead_review_task(...)
```

## Input

- DiscoveryResult
- optional MarketAndGTMStrategy
- ProductDefinition
- RequirementsSpecification
- SpecialistExecutionPlan
- SolutionArchitecture
- optional AIArchitecture
- optional SecurityArchitecture
- optional QAEvaluationPlan
- revision history
- current limitations
- cost summary when available

## Output

```python
LeadReview
```

## Process

```python
Process.sequential
```

## Responsibilities

- completeness review
- cross-document consistency
- traceability
- architecture review
- AI suitability review
- security-gap review
- QA-gap review
- market evidence review
- cost-gap review
- overengineering detection
- conflict detection
- implementation-readiness assessment
- bounded revision requests
- approval decision

## Flow handoff

The Flow reads `LeadReview` and decides whether to:

- approve blueprint assembly
- approve with limitations
- rerun Product Planning Crew
- rerun Technical Planning Crew
- rerun both when dependencies require it
- reject or fail the session

The Lead Review Crew must not invoke other Crews directly.

---

# 13. Memory Policy

All four Crews should use:

```python
memory=False
```

## Reason

BuildWise already has a canonical structured Flow state.

Crew memory would create a second, hidden source of context.

Current Crew runs are bounded and stage-specific:

```text
Crew starts
   ↓
receives structured inputs
   ↓
produces structured outputs
   ↓
Flow persists outputs
   ↓
Crew ends
```

Memory provides little value for this execution pattern.

It may introduce:

- stale context
- cross-session contamination
- lower reproducibility
- hidden dependencies
- duplicated state
- additional retrieval cost

## Future exception

Memory may be considered later for a long-running multi-task research Crew where Agents need to reuse evolving findings across many Tasks.

It should not be enabled globally.

---

# 14. Tool Policy

Tools remain attached through Agent contracts and AgentFactory.

The Crew layer must not instantiate:

- SerperDevTool
- ScrapeWebsiteTool
- GithubSearchTool

The Market & GTM Strategist may use official CrewAI tools when selected.

Task-level tool configuration may only narrow the Agent's existing permissions.

---

# 15. Skill Policy

Crew factories must not read or inject Skill content.

Skills are attached by AgentFactory.

Do not duplicate `SKILL.md` methodology inside Task descriptions or Crew configuration.

---

# 16. Context Policy

## Same-Crew context

Use native CrewAI Task context.

```python
Task(
    ...,
    context=[previous_task],
)
```

## Cross-Crew context

Use structured Flow state and kickoff inputs.

```text
Crew A
   ↓
Pydantic artifact
   ↓
Flow state
   ↓
Crew B input
```

Do not pass Task objects between completed Crew executions.

---

# 17. Output Policy

Every Task must retain its existing `output_pydantic` model.

The Flow must use structured outputs as the canonical artifacts.

Do not manually parse JSON from `CrewOutput.raw`.

Raw output may be retained for debugging or display only.

---

# 18. Cost Aggregation

Cost aggregation remains deterministic and Flow-owned.

The Flow should collect:

- CrewAI usage metrics
- token counts
- model calls
- tool usage
- execution duration
- estimated cost by Crew
- estimated cost by specialist

The Crew layer must not implement a second cost platform.

---

# 19. Blueprint Generation

Blueprint generation remains deterministic initially.

The assembler consumes approved structured artifacts and generates:

```python
ProductBlueprint
```

It should:

- preserve artifact content
- order sections
- preserve references
- include risks
- include limitations
- include recommendations
- include cost and usage summaries
- render Markdown

Do not create a Blueprint Crew solely to concatenate outputs.

---

# 20. Refactor Steps

## Step 1 — Freeze the current Crew implementation

Do not add new logic to the one-Agent Crew files.

## Step 2 — Create aggregate result models when required

Inspect whether CrewAI allows reliable access to every Task's structured output after kickoff.

If not, create:

```text
src/buildwise/domain/planning_results.py
```

with:

```python
ProductPlanningResult
TechnicalPlanningResult
```

Do not create these models if native Task output collection already satisfies the Flow requirements cleanly.

## Step 3 — Refactor Discovery Crew

Update:

```text
src/buildwise/crews/discovery.py
```

Keep one Agent and one Task.

Remove Flow responsibilities from the module.

## Step 4 — Create Product Planning Crew

Create:

```text
src/buildwise/crews/product_planning.py
```

Compose:

- optional Market & GTM Strategist
- Product Manager
- Business Analyst

Wire native Task context.

## Step 5 — Create Technical Planning Crew

Create:

```text
src/buildwise/crews/technical_planning.py
```

Build dynamic Agent and Task lists from `SpecialistExecutionPlan`.

Wire only necessary Task dependencies.

## Step 6 — Refactor Lead Review Crew

Update:

```text
src/buildwise/crews/lead_review.py
```

Keep one Agent and one Task.

Ensure it consumes the combined planning artifacts.

## Step 7 — Replace package exports

Update:

```text
src/buildwise/crews/__init__.py
```

Export only:

```python
create_discovery_crew
create_product_planning_crew
create_technical_planning_crew
create_lead_review_crew
```

## Step 8 — Remove the Crew registry

Delete or retire:

```text
src/buildwise/crews/registry.py
```

The Flow should import the four Crew factories explicitly.

## Step 9 — Remove obsolete one-Agent Crew files

Delete or move to a temporary archive branch:

```text
src/buildwise/crews/product_definition.py
src/buildwise/crews/requirements.py
src/buildwise/crews/market_and_gtm.py
src/buildwise/crews/solution_architecture.py
src/buildwise/crews/ai_architecture.py
src/buildwise/crews/security_architecture.py
src/buildwise/crews/qa_evaluation.py
```

Do not delete their Task modules.

## Step 10 — Run validation

```bash
uv run ruff format src/buildwise/crews
uv run ruff check src/buildwise/crews
uv run mypy src/buildwise/crews
```

## Step 11 — Update tests

Replace one-Crew-per-Agent tests with tests for the four business Crews.

## Step 12 — Build the deterministic specialist planner

Implement the planner before the main Flow.

## Step 13 — Build the CrewAI Flow

The Flow should orchestrate the four Crews according to the user-facing business journey.

---

# 21. Test Requirements

## Discovery Crew

Main cases:

- returns native Crew
- contains one Discovery Agent
- contains one Discovery Task
- outputs DiscoveryResult
- memory disabled

Edge cases:

- clarification context absent
- clarification answers supplied
- invalid product idea rejected before Crew construction

## Product Planning Crew

Main cases:

- standard mode creates Product Manager and Business Analyst
- market mode also creates Market & GTM Strategist
- task order is correct
- task context is correct
- outputs remain structured

Edge cases:

- market context not selected
- only Requirements revision requested
- only Product Definition revision requested
- invalid revision target

## Technical Planning Crew

Main cases:

- standard plan creates Solution and QA
- AI plan creates Solution, AI, optional Security, and QA
- security-only plan creates Solution, Security, and QA
- lightweight plan creates only Solution
- task dependencies are correct

Edge cases:

- AI selected without Solution Architecture
- QA selected without required upstream artifacts
- duplicate specialist entries
- unsupported specialist
- revision of upstream architecture correctly includes dependent Tasks

## Lead Review Crew

Main cases:

- all selected artifacts are included
- unselected optional artifacts are not treated as missing
- outputs LeadReview
- memory disabled

Edge cases:

- revision history empty
- approved-with-limitations input
- missing mandatory artifact
- unsupported revision target

No unit test should call a live LLM.

---

# 22. Acceptance Criteria

The refactor is complete when:

- the Crew package contains four business Crews
- the user-facing BuildWise process remains unchanged
- the Flow remains the sole orchestrator
- Product Planning contains collaborative Product, BA, and optional Market work
- Technical Planning dynamically composes selected specialists
- Lead Review remains a formal quality gate
- all existing Task factories are reused
- all existing Agent contracts are reused
- all existing Skills are reused
- all official CrewAI Tools remain Agent-owned
- no custom Crew runtime is introduced
- no custom scheduler is introduced
- no Crew registry is required
- no hidden Crew memory is used
- native Task context is used inside Crews
- structured Flow state is used between Crews
- all outputs remain Pydantic models
- specialist planning is deterministic
- cost aggregation is deterministic
- blueprint generation is deterministic initially
- Ruff passes
- mypy passes
- unit tests pass
- the Crew layer is ready for the main CrewAI Flow

---

# 23. Final Runtime After Refactor

```text
Actor
  ↓
Frontend
  ↓
FastAPI validation
  ↓
BuildWise CrewAI Flow
  │
  ├── Discovery Crew
  │      ↓
  │   DiscoveryResult
  │
  ├── Completeness router
  │      ├── clarification required
  │      │      ↓
  │      │   pause / frontend / answers / resume
  │      │
  │      └── sufficiently complete
  │
  ├── Early-market-context router
  │
  ├── Product Planning Crew
  │      ├── optional Market & GTM Strategist
  │      ├── Product Manager
  │      └── Business Analyst
  │
  ├── Deterministic Specialist Planner
  │
  ├── Technical Planning Crew
  │      ├── Solution Architect
  │      ├── optional AI Architect
  │      ├── optional Security Architect
  │      └── optional QA & Evaluation Architect
  │
  ├── Deterministic Cost Aggregator
  │
  ├── Lead Review Crew
  │      ├── approved
  │      ├── approved with limitations
  │      ├── revision required
  │      └── rejected
  │
  ├── Targeted revision router
  │
  ├── Output validation
  │
  └── Deterministic Blueprint Generator
         ↓
      Final Report
         ↓
      Frontend
```

---

# 24. Next Implementation Phase

After this Crew refactor, implement:

```text
src/buildwise/planning/
```

for the deterministic specialist planner.

Then implement:

```text
src/buildwise/flows/consulting_flow.py
```

using native CrewAI Flow features for:

- structured state
- routing
- clarification pause and resume
- Crew execution order
- conditional specialist execution
- revision routing
- persistence
- streaming
- usage metrics
