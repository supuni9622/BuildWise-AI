# BuildWise AI
# Tasks Layer Technical Specification

Version: 1.0

Status: Approved

---

# Purpose

This document defines every task module that will be implemented inside

```
src/buildwise/tasks/
```

Each module exposes **Task Factory Functions** that construct native CrewAI
Tasks.

No custom task classes should be created.

---

# Common Standards

Every task factory must:

- return native `crewai.Task`
- receive dependencies through parameters
- use agents created by `AgentFactory`
- use `output_pydantic`
- attach deterministic guardrails
- avoid orchestration logic
- avoid persistence logic
- avoid model routing

---

# Standard Function Pattern

```python
def create_xxx_task(
    ...dependencies...
) -> Task:
    ...
```

Never instantiate Tasks directly inside Flows or Crews.

Always use task factories.

---

# Module

## guardrails.py

Purpose

Contains reusable deterministic validation used by multiple tasks.

Responsibilities

- schema validation
- artifact validation
- session validation
- ownership validation
- reference validation
- business invariant validation

Should expose functions like

```python
validate_schema()

validate_session()

validate_artifact()

validate_review()
```

Must NOT

- call LLMs
- perform reasoning
- access database
- mutate Flow state

---

# Module

## discovery.py

Purpose

Create Discovery Tasks.

Assigned Agent

Product Discovery Analyst

Output

DiscoveryResult

Responsibilities

Create

```
create_discovery_task(...)
```

Task Description

Understand the product idea.

Extract

- known facts
- assumptions
- unknowns
- product domain
- AI capability
- completeness
- risks

Expected Output

DiscoveryResult

Context

None

Guardrails

- schema
- completeness
- confidence

Dependencies

None

---

# Module

## product_definition.py

Purpose

Create Product Definition Tasks.

Assigned Agent

Product Manager

Output

ProductDefinition

Factory

```
create_product_definition_task(...)
```

Consumes

DiscoveryResult

Produces

ProductDefinition

Responsibilities

Generate

- vision
- personas
- goals
- features
- roadmap
- success metrics

Guardrails

- schema
- feature validation
- roadmap validation

---

# Module

## requirements.py

Assigned Agent

Business Analyst

Output

RequirementsSpecification

Consumes

ProductDefinition

Responsibilities

Generate

- functional requirements

- non-functional requirements

- business rules

- integrations

- user journeys

- acceptance criteria

Guardrails

- schema
- requirement traceability
- acceptance criteria validation

---

# Module

## specialist_planning.py

Assigned Agent

Business Analyst

Output

SpecialistExecutionPlan

Consumes

RequirementsSpecification

Responsibilities

Determine

- required specialists

- execution order

- dependencies

- execution mode

- estimated cost

Guardrails

- valid dependency graph

- supported specialists

- execution ordering

---

# Module

## market_and_gtm.py

Assigned Agent

Market & GTM Strategist

Output

MarketAndGTMStrategy

Consumes

RequirementsSpecification

SpecialistExecutionPlan

Uses Tools

Serper

Website Scraper

Responsibilities

Generate

- positioning

- ICP

- competitors

- pricing hypotheses

- launch strategy

- risks

Guardrails

- schema

- evidence references

- assumptions

---

# Module

## solution_architecture.py

Assigned Agent

Solution Architect

Output

SolutionArchitecture

Consumes

RequirementsSpecification

Responsibilities

Generate

- components

- APIs

- databases

- integrations

- deployment

- scalability

- observability

Guardrails

- schema

- component references

- dependency validation

---

# Module

## ai_architecture.py

Assigned Agent

AI Architect

Output

AIArchitecture

Consumes

RequirementsSpecification

SolutionArchitecture

Responsibilities

Generate

- AI capabilities

- model strategy

- routing

- RAG

- agents

- prompts

- evaluations

- guardrails

Guardrails

- schema

- AI capability validation

- model strategy validation

---

# Module

## security_architecture.py

Assigned Agent

Security Architect

Output

SecurityArchitecture

Consumes

RequirementsSpecification

SolutionArchitecture

AIArchitecture

Responsibilities

Generate

- identity

- authorization

- encryption

- threats

- controls

- audit

- compliance

Guardrails

- schema

- security completeness

- threat validation

---

# Module

## qa_evaluation.py

Assigned Agent

QA & Evaluation Architect

Output

QAEvaluationPlan

Consumes

Requirements

Architecture

AI

Security

Responsibilities

Generate

- testing strategy

- AI evaluation

- release gates

- performance testing

- reliability

Guardrails

- schema

- coverage

- release gate validation

---

# Module

## lead_review.py

Assigned Agent

Lead Reviewer

Output

LeadReview

Consumes

All previous artifacts

Responsibilities

Evaluate

- consistency

- completeness

- feasibility

- traceability

- implementation readiness

Generate

- findings

- revisions

- decision

Guardrails

- schema

- consistency

- review decision

---

# Task Context Rules

Always use

```
context=[
    previous_task,
]
```

Never manually inject large text.

CrewAI already manages task outputs.

---

# Structured Outputs

Every task except helper tasks must use

```
output_pydantic=
```

Never manually parse JSON.

---

# Async Execution

Allowed only when specialists are independent.

Good

Market

Security

QA

Bad

Discovery

↓

Product

↓

Requirements

These remain sequential.

---

# Human Clarification

Tasks never stop for user input.

The Flow pauses.

The Flow resumes.

Tasks stay deterministic.

---

# Error Handling

Task construction should fail if

- agent missing

- output model missing

- guardrails missing

- invalid configuration

Never silently recover.

---

# Acceptance Criteria

The Tasks layer is complete when

✓ every module exposes task factory functions

✓ every task returns native CrewAI Task

✓ every task has structured output

✓ every task has deterministic guardrails

✓ every task has expected output

✓ every task uses native context

✓ no orchestration logic exists

✓ no persistence logic exists

✓ no HTTP logic exists

✓ no database logic exists

✓ tasks are immediately usable by Crews