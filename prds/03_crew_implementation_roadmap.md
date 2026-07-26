# BuildWise AI
# CrewAI Crew Implementation Roadmap

Version: 1.0

Status: Approved

Scope: Crew implementation only

Framework: CrewAI v1.15.6

---

# Purpose

This document defines how the BuildWise Crew layer should be implemented.

It is intended to be the implementation guide for Claude Code.

This document does **not** redesign the architecture.

Instead, it converts the Crew Architecture PRD into an implementation roadmap.

---

# Overall Goal

Implement a Crew layer that:

- uses native CrewAI Crew
- uses BuildWise AgentFactory
- uses BuildWise Task factories
- returns structured outputs
- is reusable
- is testable
- remains Flow-driven

---

# Target Folder

```
src/buildwise/
    crews/
        __init__.py

        discovery.py
        product_definition.py
        requirements.py

        market_and_gtm.py
        solution_architecture.py
        ai_architecture.py
        security_architecture.py
        qa_evaluation.py

        lead_review.py

        registry.py
```

---

# Architecture

```
Flow
   │
   ▼

Crew Factory

   │

creates

   ▼

Native CrewAI Crew

   │

contains

   ▼

Native CrewAI Tasks

   │

executed by

   ▼

Native CrewAI Agents

   │

configured by

   ▼

Agent Factory
```

---

# Build Order

Implement crews in dependency order.

Never create every Crew simultaneously.

---

# Phase 1

Discovery Crew

File

```
discovery.py
```

Depends on

- AgentFactory
- Discovery Task

Produces

```
DiscoveryResult
```

Validation

- correct Agent
- correct Task
- Process.sequential

---

# Phase 2

Product Definition Crew

Depends on

```
Discovery Crew
```

Produces

```
ProductDefinition
```

Validation

- Product Manager assigned

- Product Definition task

- structured output

---

# Phase 3

Requirements Crew

Depends on

```
ProductDefinition
```

Produces

```
RequirementsSpecification
```

Validation

Business Analyst

Requirements Task

Structured output

---

# Phase 4

Solution Architecture Crew

Depends on

```
RequirementsSpecification
```

Produces

```
SolutionArchitecture
```

Validation

Solution Architect

Architecture Task

---

# Phase 5

Market & GTM Crew

Depends on

```
ProductDefinition
```

Produces

```
MarketAndGTMStrategy
```

Validation

Official CrewAI Tools attached

No custom tools

---

# Phase 6

AI Architecture Crew

Depends on

```
SolutionArchitecture
```

Produces

```
AIArchitecture
```

Validation

Conditional execution

No custom routing

---

# Phase 7

Security Crew

Depends on

```
SolutionArchitecture

AIArchitecture (optional)
```

Produces

```
SecurityArchitecture
```

Validation

Security Architect

---

# Phase 8

QA Crew

Depends on

```
Requirements

Architecture

AI (optional)

Security (optional)
```

Produces

```
QAEvaluationPlan
```

Validation

QA Architect

---

# Phase 9

Lead Review Crew

Consumes

Every previous artifact

Produces

```
LeadReview
```

Validation

Decision

Revision Requests

Approval

---

# Phase 10

Registry

Register every Crew factory

No Crew instances

Only factories

---

# Factory Pattern

Every Crew module exposes

```python
create_xxx_crew(...)
```

Example

```python
def create_discovery_crew(...):

    agent = ...

    task = ...

    return Crew(...)
```

Nothing else.

---

# Agent Construction

Never instantiate Agent directly.

Always

```
AgentFactory

↓

Agent Contract

↓

Crew
```

---

# Task Construction

Never instantiate Tasks manually.

Always

```
Task Factory

↓

Crew
```

---

# Process

Default

```python
Process.sequential
```

Only introduce

```
hierarchical
```

when justified.

Current answer

No.

---

# Delegation

Default

```
allow_delegation=False
```

Do not enable simply because CrewAI supports it.

---

# Memory

Default

```
memory=False
```

Flow already stores state.

Crew memory would duplicate state.

---

# Cache

Default

```
cache=True
```

---

# Verbose

Read from

```
settings.crewai_verbose
```

Never hardcode.

---

# Planning

Disabled

Current MVP

```
planning=False
```

---

# Manager LLM

Do not configure.

---

# Manager Agent

Do not configure.

---

# Knowledge

Knowledge belongs to Agents.

Crew should never configure Knowledge.

---

# Skills

Skills belong to Agents.

Crew should never read

```
SKILL.md
```

---

# Tools

Tools belong to Agents.

Crew never creates

```
Serper

Github Search

Website Scraper
```

---

# Context

Flow passes

structured inputs

Crew never reads database.

Crew never loads session.

---

# Output

Every Crew produces

one

Pydantic model.

Never

markdown.

Never

JSON parsing.

---

# Errors

Construction errors

Raise immediately.

Runtime errors

Propagate to Flow.

---

# Logging

Crew logs

construction only.

Flow logs

execution.

---

# Tracing

CrewAI tracing

only.

No wrapper.

---

# Retry

Crew retries

No.

Task Guardrail retries

Yes.

Flow retries

Yes.

---

# Async

Do not execute Crews concurrently inside Crew.

Flow owns concurrency.

---

# Human Input

Never.

Flow owns human approval.

---

# Revision

Crew accepts

```
RevisionRequest
```

Crew never decides

to revise.

---

# Registry

Registry stores

Crew Factories.

Not Crew instances.

---

# Registry API

Suggested

```python
register()

resolve()

list()

contains()
```

Nothing more.

---

# Unit Tests

Every Crew

verify

- Crew type

- one Agent

- one Task

- output model

- process

- settings

---

# Integration Tests

Verify

Agent Factory

↓

Crew

↓

Task

↓

Structured Output

---

# Ruff

Every file

```
ruff format

ruff check

mypy
```

before moving next.

---

# Acceptance Checklist

Every Crew

✓ native CrewAI

✓ one responsibility

✓ one structured output

✓ AgentFactory

✓ Task Factory

✓ sequential

✓ memory disabled

✓ cache enabled

✓ verbose configurable

✓ no orchestration

✓ no persistence

✓ no API

✓ no Flow state

✓ no custom runtime

✓ no custom scheduler

✓ no custom parser

---

# Definition of Done

Crew layer is complete when

✓ Every Crew file implemented

✓ Registry implemented

✓ All factories return Crew

✓ All tasks connected

✓ All agents connected

✓ All outputs structured

✓ All imports pass

✓ Ruff passes

✓ mypy passes

✓ Unit tests pass

✓ Ready for Flow implementation

---

# Next Phase

After Crews

↓

Implement

```
src/buildwise/flows/
```

using

Native CrewAI Flow.

The Flow becomes the application brain.

Crews become reusable execution units.

Tasks become reusable work units.

Agents remain specialists.

This completes the core CrewAI architecture.