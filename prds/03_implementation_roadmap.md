# BuildWise AI
# Tasks Layer Implementation Roadmap

Version: 1.0

Status: Approved

---

# Purpose

This document defines the implementation order, dependencies, integration
points, validation steps, and Definition of Done for the BuildWise CrewAI Tasks
layer.

Claude Code should use this document together with:

- `01_tasks_architecture_prd.md`
- `02_task_specifications.md`

The goal is to implement a thin, native CrewAI task layer that can be composed
into focused Crews and orchestrated by the BuildWise Flow.

---

# Target Package

```text
src/buildwise/tasks/
├── __init__.py
├── guardrails.py
├── discovery.py
├── product_definition.py
├── requirements.py
├── specialist_planning.py
├── market_and_gtm.py
├── solution_architecture.py
├── ai_architecture.py
├── security_architecture.py
├── qa_evaluation.py
└── lead_review.py
```

---

# Architectural Constraint

The implementation must use native CrewAI components.

Use:

```python
from crewai import Agent, Task
```

Do not create:

- custom Task subclasses
- a custom task scheduler
- a custom task graph
- a custom task execution engine
- a custom structured-output parser
- custom retry loops
- custom asynchronous execution
- custom context propagation
- a parallel validation platform

The BuildWise task layer should construct and configure native `crewai.Task`
instances only.

---

# Runtime Position

```text
FastAPI
   ↓
CrewAI Flow
   ↓
Focused Crew
   ↓
Native CrewAI Task
   ↓
Native CrewAI Agent
   ├── Skill
   ├── Tool
   ├── MCP
   ├── App
   └── Knowledge
   ↓
Pydantic output
   ↓
Flow state
```

Tasks must not bypass Crews or Flow orchestration.

---

# Existing Dependencies

Before starting this phase, the following should exist.

## Domain layer

Expected models include:

```text
DiscoveryResult
ProductDefinition
RequirementsSpecification
SpecialistExecutionPlan
MarketAndGTMStrategy
SolutionArchitecture
AIArchitecture
SecurityArchitecture
QAEvaluationPlan
LeadReview
```

Use the exact model names available in the repository.

Do not invent replacement domain models.

If an imported class name differs from this roadmap, inspect the current domain
file and use the real model.

---

## Agent layer

Expected agent infrastructure includes:

```text
src/buildwise/agents/base.py
src/buildwise/agents/registry.py
src/buildwise/agents/factory.py
```

Expected canonical agent contracts include:

```text
Product Discovery Analyst
Product Manager
Business Analyst
Market & GTM Strategist
Solution Architect
AI Architect
Security Architect
QA & Evaluation Architect
Lead Reviewer
```

Tasks receive already-created native CrewAI agents.

Task factories must not construct agents internally.

---

## Skills layer

Expected skill packages include:

```text
skills/product_discovery_analyst/
skills/product_manager/
skills/business_analyst/
skills/market_and_gtm_strategist/
skills/solution_architect/
skills/ai_architect/
skills/security_architect/
skills/qa_evaluation_architect/
skills/lead_reviewer/
```

Tasks must not load these skills.

The Agent Factory owns Skill resolution.

---

## Tools layer

Expected tool infrastructure includes:

```text
src/buildwise/tools/registry.py
```

Tasks must not instantiate:

```text
SerperDevTool
ScrapeWebsiteTool
GithubSearchTool
```

The agent contract and Agent Factory own tool attachment.

---

# Implementation Strategy

Implement the task layer in dependency order.

Do not create all files at once without validation.

Complete and validate one stage before moving to the next.

---

# Phase 1 — Shared Guardrails

## File

```text
src/buildwise/tasks/guardrails.py
```

## Goal

Provide reusable deterministic CrewAI task guardrails.

## Responsibilities

Implement guardrails for:

- required Pydantic output
- expected output type
- non-empty structured artifact
- optional artifact/session identity validation
- optional review-decision consistency
- optional custom domain validator execution

## Recommended public API

The exact function names may be refined to match CrewAI v1.15.6 signatures.

Suggested API:

```python
def require_pydantic_output(
    expected_model: type[BaseModel],
) -> Callable[[TaskOutput], tuple[bool, Any]]:
    ...
```

```python
def require_artifact_session(
    expected_session_id: UUID | str,
) -> Callable[[TaskOutput], tuple[bool, Any]]:
    ...
```

```python
def require_review_consistency(
    result: TaskOutput,
) -> tuple[bool, Any]:
    ...
```

```python
def compose_guardrails(
    *guardrails: TaskGuardrail,
) -> list[TaskGuardrail]:
    ...
```

## Guardrail return contract

Follow the official CrewAI guardrail contract.

A successful guardrail should return:

```python
(True, accepted_output)
```

A failed guardrail should return:

```python
(False, actionable_feedback)
```

Feedback must be clear enough for the agent to correct the output.

Example:

```text
The task did not produce a ProductDefinition in TaskOutput.pydantic.
Return a schema-valid ProductDefinition and do not return only markdown.
```

## Guardrail rules

Guardrails must:

- be deterministic
- avoid LLM calls
- avoid database access
- avoid Flow-state mutation
- avoid network calls
- avoid persistence
- return actionable correction feedback
- preserve a valid `TaskOutput.pydantic` object

## Do not duplicate Pydantic

Do not manually reimplement:

- field type validation
- enum validation
- required-field validation
- model validators already present in domain models

Use task guardrails for runtime guarantees and cross-artifact checks only.

## Validation

Run:

```bash
uv run ruff format src/buildwise/tasks/guardrails.py
uv run ruff check src/buildwise/tasks/guardrails.py
uv run mypy src/buildwise/tasks/guardrails.py
```

Do not proceed until imports and CrewAI guardrail signatures are valid.

---

# Phase 2 — Discovery Task

## File

```text
src/buildwise/tasks/discovery.py
```

## Factory

```python
def create_discovery_task(
    *,
    agent: Agent,
    product_idea: ProductIdeaRequest,
    guardrail_max_retries: int = 2,
) -> Task:
    ...
```

Adapt parameters to the real intake models.

## Assigned agent

```text
Product Discovery Analyst
```

## Output

```text
DiscoveryResult
```

## Task responsibilities

The task should instruct the agent to:

- preserve the submitted product idea
- identify known facts
- identify assumptions
- identify unknowns
- identify early risks
- classify capabilities
- assess completeness
- determine whether clarification is required
- return a structured `DiscoveryResult`

## Task configuration

Use:

```python
Task(
    name="product_discovery",
    description=...,
    expected_output=...,
    agent=agent,
    output_pydantic=DiscoveryResult,
    guardrails=[...],
    guardrail_max_retries=guardrail_max_retries,
)
```

Use the exact constructor arguments supported by CrewAI v1.15.6.

## Context

None.

The product idea should be supplied through task inputs or formatted into the
description in a controlled, bounded way.

Do not pass entire session histories.

## Acceptance criteria

- returns native `Task`
- has Product Discovery Analyst assigned
- uses `DiscoveryResult`
- uses at least one deterministic guardrail
- does not ask the user directly
- does not pause the Flow
- does not create clarification answers
- does not persist data
- does not select later specialists

---

# Phase 3 — Product Definition Task

## File

```text
src/buildwise/tasks/product_definition.py
```

## Factory

```python
def create_product_definition_task(
    *,
    agent: Agent,
    discovery_task: Task | None = None,
    discovery_result: DiscoveryResult | None = None,
    guardrail_max_retries: int = 2,
) -> Task:
    ...
```

Prefer one canonical input pattern.

For tasks executed together inside one Crew, use:

```python
context=[discovery_task]
```

For tasks executed by separate Crews under the Flow, pass the structured
`DiscoveryResult` through Crew inputs rather than pretending a Task from another
Crew is local context.

## Assigned agent

```text
Product Manager
```

## Output

```text
ProductDefinition
```

## Responsibilities

- define product vision
- define product goals
- define personas
- define features
- prioritize scope
- define MVP
- define exclusions
- define roadmap
- define success metrics
- define product risks
- preserve assumptions and limitations

## Acceptance criteria

- native `Task`
- correct assigned agent
- `output_pydantic=ProductDefinition`
- no technical architecture instructions
- no market research instructions
- no implementation stack selection
- guardrails validate structured output
- task remains usable in a focused Product Crew

---

# Phase 4 — Requirements Task

## File

```text
src/buildwise/tasks/requirements.py
```

## Factory

```python
def create_requirements_task(
    *,
    agent: Agent,
    product_definition_task: Task | None = None,
    product_definition: ProductDefinition | None = None,
    guardrail_max_retries: int = 2,
) -> Task:
    ...
```

## Assigned agent

```text
Business Analyst
```

## Output

```text
RequirementsSpecification
```

## Responsibilities

- functional requirements
- non-functional requirements
- business rules
- data requirements
- integration requirements
- user journeys
- acceptance criteria
- edge cases
- traceability

## Guardrail focus

- structured output exists
- output type is correct
- requirements are present
- traceability collections are valid
- no raw-only response is accepted

Do not duplicate domain model validators.

## Acceptance criteria

- correct output model
- Business Analyst assigned
- no architecture decisions
- no model selection
- no direct persistence
- no user interaction
- context/input is ProductDefinition only
- task can be reused by a Requirements Crew

---

# Phase 5 — Specialist Planning Task

## File

```text
src/buildwise/tasks/specialist_planning.py
```

## Important architecture decision

Specialist planning may be either:

1. a deterministic Flow/application step, or
2. a native CrewAI Task assigned to a suitable planning agent.

Before implementing, inspect the existing architecture decision and domain
contracts.

Do not assign specialist planning to the Business Analyst merely because no
other agent exists unless that responsibility is already present in the agent
contract.

If specialist selection is deterministic from capability classifications,
sensitive-data flags, regulation signals, and execution budgets, prefer
application or Flow logic instead of an LLM Task.

## If implemented as a Task

### Factory

```python
def create_specialist_planning_task(
    *,
    agent: Agent,
    requirements: RequirementsSpecification,
    guardrail_max_retries: int = 2,
) -> Task:
    ...
```

### Output

```text
SpecialistExecutionPlan
```

### Responsibilities

- select supported specialists
- explain selection reasons
- define dependencies
- define sequential or parallel groups
- respect budget decisions
- avoid selecting unnecessary specialists

## Guardrails

- supported specialist values only
- no unknown dependencies
- no self-dependencies
- valid execution order
- required specialists not omitted
- conditional specialists justified

## Decision gate

If planning is deterministic, do not create this Task.

Keep the file only if it contains a small native task factory that adds genuine
reasoning value.

---

# Phase 6 — Market and GTM Task

## File

```text
src/buildwise/tasks/market_and_gtm.py
```

## Factory

```python
def create_market_and_gtm_task(
    *,
    agent: Agent,
    product_definition: ProductDefinition,
    requirements: RequirementsSpecification,
    guardrail_max_retries: int = 2,
    async_execution: bool = True,
) -> Task:
    ...
```

Use only inputs genuinely required by the real domain model.

## Assigned agent

```text
Market & GTM Strategist
```

## Tools

The assigned agent may already include:

```text
web_search
web_scraper
```

The task must not instantiate tools.

Task-level tool restriction may be used only when the official CrewAI Task API
supports it and when it narrows the agent's existing permissions.

Do not broaden tool access at task level.

## Output

Use the exact market/GTM root model available in:

```text
src/buildwise/domain/market_and_gtm.py
```

Possible name:

```text
MarketAndGTMStrategy
```

Do not guess. Inspect the domain file.

## Responsibilities

- identify target segments
- identify primary segment
- analyze competitors and substitutes
- define positioning
- define pricing hypotheses
- define channels
- define launch experiments
- identify commercial risks
- preserve evidence references and evidence gaps

## Guardrails

- structured model exists
- a primary segment exists where required
- evidence-dependent claims are represented appropriately
- decision metadata is internally consistent
- URLs and source references conform to the domain model

## Acceptance criteria

- native CrewAI Task
- official tools remain agent-owned
- can execute concurrently with independent specialist tasks
- does not change ProductDefinition
- does not invent unsupported market evidence
- output uses the exact domain root model

---

# Phase 7 — Solution Architecture Task

## File

```text
src/buildwise/tasks/solution_architecture.py
```

## Factory

```python
def create_solution_architecture_task(
    *,
    agent: Agent,
    requirements: RequirementsSpecification,
    guardrail_max_retries: int = 2,
    async_execution: bool = True,
) -> Task:
    ...
```

## Assigned agent

```text
Solution Architect
```

## Output

```text
SolutionArchitecture
```

## Responsibilities

- system boundaries
- components
- integrations
- data flows
- technology recommendations
- deployment view
- scalability
- reliability
- observability
- implementation phases
- cost estimates
- architectural risks

## Exclusions

The task must explicitly avoid asking for:

- model selection
- RAG
- prompt design
- full security architecture
- full QA strategy
- product-scope changes

## Guardrails

- structured output exists
- correct session/artifact ownership where available
- component references are valid
- integration references are valid
- decision metadata is consistent
- required architecture sections are populated

## Acceptance criteria

- native CrewAI Task
- outputs `SolutionArchitecture`
- can run before AI, security, and QA tasks
- no tool instantiation
- no Flow routing
- no persistence logic

---

# Phase 8 — AI Architecture Task

## File

```text
src/buildwise/tasks/ai_architecture.py
```

## Factory

```python
def create_ai_architecture_task(
    *,
    agent: Agent,
    requirements: RequirementsSpecification,
    solution_architecture: SolutionArchitecture,
    guardrail_max_retries: int = 2,
    async_execution: bool = False,
) -> Task:
    ...
```

## Assigned agent

```text
AI Architect
```

## Conditional execution

Create and run only when specialist planning selects AI Architecture.

## Output

```text
AIArchitecture
```

## Responsibilities

- justify AI capabilities
- define deterministic alternatives
- define model roles
- define model strategy
- define model selections
- define prompt contracts
- define tool policies
- define agent designs
- define AI workflows
- define RAG where required
- define guardrails
- define evaluation
- define observability
- define fallback
- define human oversight
- define AI risks and costs

## Guardrails

- every AI capability has model-requirement coverage
- every AI capability has evaluation coverage
- RAG capabilities have RAG design
- agentic capabilities have workflow design
- model and artifact references resolve
- decision metadata is consistent
- ownership validation against SolutionArchitecture succeeds where available

Use domain-provided ownership validation methods instead of recreating them.

## Acceptance criteria

- native CrewAI Task
- correct AI Architect agent
- exact `AIArchitecture` output
- no unsupported custom parsing
- no custom orchestration
- no unrestricted task-level tools
- runs after Solution Architecture where the model requires it

---

# Phase 9 — Security Architecture Task

## File

```text
src/buildwise/tasks/security_architecture.py
```

## Factory

```python
def create_security_architecture_task(
    *,
    agent: Agent,
    requirements: RequirementsSpecification,
    solution_architecture: SolutionArchitecture,
    ai_architecture: AIArchitecture | None = None,
    guardrail_max_retries: int = 2,
    async_execution: bool = True,
) -> Task:
    ...
```

## Assigned agent

```text
Security Architect
```

## Output

```text
SecurityArchitecture
```

## Responsibilities

- identity
- authentication
- authorization
- secrets
- encryption
- PII handling
- data classification
- retention
- secure storage
- attack surfaces
- trust boundaries
- threats
- controls
- audit requirements
- compliance considerations
- validation
- residual risks
- incident response
- costs and implementation phases

## Dependency rule

When AI Architecture is selected and available, Security Architecture should
consume it.

When AI is not selected, the task must remain valid without it.

## Guardrails

- structured output exists
- threats and controls are populated where required
- threat references are valid
- control references are valid
- security decision is internally consistent
- no unsupported compliance claim is represented as formal certification
- no unresolved accepted critical risk violates domain invariants

## Acceptance criteria

- native CrewAI Task
- optional AI context handled correctly
- no security tool platform added
- no direct legal claims
- output uses exact `SecurityArchitecture`
- suitable for a focused Security Crew

---

# Phase 10 — QA and Evaluation Task

## File

```text
src/buildwise/tasks/qa_evaluation.py
```

## Factory

```python
def create_qa_evaluation_task(
    *,
    agent: Agent,
    requirements: RequirementsSpecification,
    solution_architecture: SolutionArchitecture,
    ai_architecture: AIArchitecture | None = None,
    security_architecture: SecurityArchitecture | None = None,
    guardrail_max_retries: int = 2,
    async_execution: bool = True,
) -> Task:
    ...
```

## Assigned agent

```text
QA & Evaluation Architect
```

## Output

```text
QAEvaluationPlan
```

## Responsibilities

- quality objectives
- test strategy
- test suites
- test scenarios
- acceptance tests
- performance validation
- reliability validation
- security-control validation
- AI evaluation
- release gates
- production quality signals
- quality risks
- costs and implementation phases

## Dependency rule

QA may require:

- RequirementsSpecification
- SolutionArchitecture
- AIArchitecture when selected
- SecurityArchitecture when selected

If QA needs final Security output, do not execute QA in parallel with Security.

Use parallel execution only when dependencies genuinely allow it.

## Guardrails

- output type
- critical journeys covered
- release gates exist
- AI evaluation exists when AIArchitecture exists
- security validation exists when SecurityArchitecture exists
- decision and confidence fields are consistent
- no raw-only fallback accepted

## Acceptance criteria

- native CrewAI Task
- optional specialist artifacts handled safely
- uses the exact QA domain model
- no architecture redesign
- no custom evaluator framework
- compatible with a focused QA Crew

---

# Phase 11 — Lead Review Task

## File

```text
src/buildwise/tasks/lead_review.py
```

## Factory

```python
def create_lead_review_task(
    *,
    agent: Agent,
    discovery: DiscoveryResult,
    product_definition: ProductDefinition,
    requirements: RequirementsSpecification,
    specialist_plan: SpecialistExecutionPlan,
    market_and_gtm: MarketAndGTMStrategy | None = None,
    solution_architecture: SolutionArchitecture | None = None,
    ai_architecture: AIArchitecture | None = None,
    security_architecture: SecurityArchitecture | None = None,
    qa_evaluation: QAEvaluationPlan | None = None,
    guardrail_max_retries: int = 2,
) -> Task:
    ...
```

Adapt names to actual domain models.

## Assigned agent

```text
Lead Reviewer
```

## Output

```text
LeadReview
```

## Responsibilities

- account for required and conditional artifacts
- detect contradictions
- validate traceability
- validate specialist alignment
- validate feasibility
- validate risks
- validate cost consistency
- assess implementation readiness
- create bounded revision requests
- determine approval decision
- determine blueprint readiness

## Context size control

Do not concatenate every artifact into one enormous unstructured prompt.

Pass structured serialized inputs through Crew inputs.

Use concise model serialization, excluding fields not needed by the review where
appropriate.

Do not silently omit decision-critical fields.

## Guardrails

- `LeadReview` exists
- `approved_for_blueprint` matches decision
- revision-required decision contains revision requests
- approved decision contains no blocking revision request
- rejected decision contains rationale
- revision targets are supported
- implementation-readiness score is valid
- no unknown artifact references

## Acceptance criteria

- native CrewAI Task
- Lead Reviewer assigned
- `output_pydantic=LeadReview`
- all selected specialist artifacts are accounted for
- unselected optional specialists are not treated as failures
- review does not rewrite specialist outputs
- no blueprint assembly occurs in this task

---

# Phase 12 — Package Exports

## File

```text
src/buildwise/tasks/__init__.py
```

## Goal

Expose the supported public task factory API.

## Export

- common guardrail helpers
- every task factory
- task-specific public types only when needed

## Do not export

- internal helper functions
- implementation-only constants
- private formatting utilities

## Example structure

```python
from buildwise.tasks.ai_architecture import (
    create_ai_architecture_task,
)
from buildwise.tasks.discovery import create_discovery_task
...

__all__ = [
    "create_ai_architecture_task",
    "create_discovery_task",
    ...
]
```

Avoid circular imports.

---

# Prompt Construction Rules

Task descriptions must remain concise.

Use this structure:

```text
Objective

Available structured context

Required decisions

Required output artifact

Important boundaries

Failure or uncertainty handling
```

Do not duplicate full Skills inside task descriptions.

Do not copy hundreds of lines from `SKILL.md`.

The agent already receives the Skill through Agent Factory configuration.

---

# Task Input Strategy

## Same-Crew dependency

Use native Task context:

```python
second_task = Task(
    ...,
    context=[first_task],
)
```

Only use this when both tasks belong to the same Crew execution.

---

## Cross-Crew dependency

Use Flow state and Crew inputs.

Example:

```python
crew.kickoff(
    inputs={
        "requirements": requirements.model_dump_json(),
        "solution_architecture": architecture.model_dump_json(),
    }
)
```

Do not pass a Task object from a completed different Crew as if it were current
Crew context.

---

# Structured Serialization

Prefer:

```python
model.model_dump(mode="json")
```

or:

```python
model.model_dump_json()
```

according to the Crew input format.

Do not use:

```python
str(model)
```

Do not concatenate Python object representations.

Do not manually transform Pydantic models into ad hoc schemas unless needed for
context reduction.

---

# Context Reduction

For large specialist artifacts:

- pass only relevant artifacts
- avoid full session transcripts
- omit internal metadata that does not affect reasoning
- preserve identifiers used for traceability
- preserve assumptions
- preserve risks
- preserve decisions
- preserve limitations
- preserve relevant source references

Do not summarize away critical details before Lead Review.

---

# Guardrail Retry Policy

Default:

```python
guardrail_max_retries=2
```

Use settings when available:

```python
settings.max_retries_per_operation
```

Do not exceed application-wide retry policy.

Do not implement nested retry loops.

Runtime pattern:

```text
Task output
   ↓
Guardrail
   ↓ fail
CrewAI bounded retry
   ↓
Corrected output or failure
```

---

# Async Execution Plan

Do not mark all specialist tasks async automatically.

Recommended dependency analysis:

```text
Solution Architecture
        ↓
AI Architecture
        ↓
Security Architecture
        ↓
QA Evaluation
```

Market & GTM may run independently after Product Definition or Requirements.

Possible first implementation:

```text
Market & GTM       ── async candidate
Solution Architecture ─ required first
AI Architecture       ─ conditional after Solution
Security Architecture ─ conditional after Solution/AI
QA Evaluation         ─ after selected architectures
```

Prefer correctness over maximum concurrency.

The Flow should later decide which focused Crews run concurrently.

Task-level `async_execution=True` is appropriate only inside a Crew whose
process and dependencies support it.

---

# Human-in-the-Loop Boundary

Task files must not use `input()` or terminal prompts.

Do not enable direct task human input for the API runtime unless the architecture
explicitly changes.

Use CrewAI Flow human feedback for:

- clarification
- approval
- revision
- rejection
- consequential decisions

The Flow owns pause and resume.

---

# Crew Integration Expectations

Tasks should be directly usable in focused Crew factories.

Example:

```python
agent = agent_factory.create(AgentType.SOLUTION_ARCHITECT)

task = create_solution_architecture_task(
    agent=agent,
    requirements=requirements,
)

crew = Crew(
    agents=[agent],
    tasks=[task],
    process=Process.sequential,
)
```

Do not instantiate `Crew` inside task files.

---

# Flow Integration Expectations

The Flow should:

1. load structured state
2. decide which Crew runs
3. create the required native agents
4. create native tasks
5. create and run the focused Crew
6. read `CrewOutput.pydantic`
7. validate and persist the artifact
8. update Flow state
9. route to the next stage

Tasks should not know the Flow state object.

---

# Error Handling

## Construction errors

Raise immediately when:

- agent is `None`
- wrong agent role is supplied where validation is possible
- output model cannot be imported
- required structured input is missing
- invalid retry configuration is supplied
- required context is missing

Use clear application exceptions where needed.

---

## Runtime errors

Allow CrewAI to handle:

- model execution
- task execution
- task guardrail retries
- tool execution through agents
- Crew execution

Flow/application layer handles:

- failure policy
- fallback routing
- session failure
- continue-with-limitation behavior
- persistence
- user-facing status

---

# Testing Guidance

Even though test implementation may occur later, design task factories to be
testable.

## Main tests

Test:

- each factory returns `crewai.Task`
- correct agent is assigned
- correct `output_pydantic` is configured
- guardrails are configured
- retry count is configured
- context is configured correctly
- async flag is configured correctly
- expected output is non-empty
- descriptions include required placeholders or context

## Edge cases

Test:

- missing required input
- wrong output type from guardrail
- missing `TaskOutput.pydantic`
- incompatible artifact/session identity
- invalid review decision combination
- optional AI/Security artifact omitted correctly
- duplicate context task
- retry limit outside accepted range

Do not write tests that call real LLMs in the unit suite.

---

# Validation Commands

After each file:

```bash
uv run ruff format src/buildwise/tasks/<file>.py
uv run ruff check src/buildwise/tasks/<file>.py
uv run mypy src/buildwise/tasks/<file>.py
```

After the package is complete:

```bash
uv run ruff format src/buildwise/tasks
uv run ruff check src/buildwise/tasks
uv run mypy src/buildwise/tasks
```

Import validation:

```bash
uv run python -c "
import buildwise.tasks
print('BuildWise tasks imported successfully')
"
```

---

# Claude Code Implementation Rules

Claude Code must:

- inspect existing domain files before importing model names
- inspect existing agent files before using contract constants
- inspect the installed CrewAI v1.15.6 Task API
- use native CrewAI Task constructors
- use native `output_pydantic`
- use official guardrail signatures
- provide full files
- avoid partial snippets
- avoid placeholders such as `pass`
- avoid TODO-only implementations
- preserve current project naming
- preserve current Pydantic conventions
- preserve Ruff and mypy compatibility
- avoid introducing unnecessary dependencies

Claude Code must ask before proceeding when:

- a referenced domain model does not exist
- an agent constant name differs
- the CrewAI Task API differs from the specification
- the intended specialist-planning ownership is unclear
- existing validation utilities overlap with planned guardrails
- circular imports appear unavoidable
- Flow-state expectations conflict with task inputs

---

# Do Not Implement Yet

This roadmap covers the Tasks layer only.

Do not implement in this phase:

```text
src/buildwise/crews/
src/buildwise/flows/consulting_flow.py
FastAPI consultation endpoints
database repositories
session persistence
streaming endpoints
blueprint export
```

The next phase after Tasks is focused Crews.

---

# Final Tasks Layer Definition of Done

The Tasks layer is complete when:

- all agreed task modules exist
- all factories return native CrewAI `Task`
- all important reasoning tasks use `output_pydantic`
- all important tasks use deterministic guardrails
- all guardrail retries are bounded
- task descriptions remain concise
- methodology remains in Skills
- tools remain attached through agents
- models remain selected through agent contracts
- no task constructs an Agent
- no task constructs a Crew
- no task orchestrates a Flow
- no task accesses FastAPI
- no task accesses persistence
- no task mutates Flow state
- no manual JSON parsing exists
- cross-Crew context is designed for Flow inputs
- same-Crew context uses CrewAI Task context
- optional specialist artifacts are supported
- Ruff passes
- mypy passes
- all modules import successfully
- the package is ready for focused Crew implementation

---

# Next Phase

After the Tasks layer is approved, implement focused Crews.

Recommended Crew package direction:

```text
src/buildwise/crews/
├── discovery/
├── product_definition/
├── requirements/
├── market_and_gtm/
├── solution_architecture/
├── ai_architecture/
├── security_architecture/
├── qa_evaluation/
└── review/
```

Each Crew should use:

- native CrewAI `Crew`
- native BuildWise agent from `AgentFactory`
- native Task from this Tasks layer
- structured output
- focused responsibility
- bounded execution
- CrewAI tracing
- no Flow orchestration logic

The Flow phase follows after focused Crews are complete.