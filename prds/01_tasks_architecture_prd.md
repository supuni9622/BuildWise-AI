# BuildWise AI
# Tasks Layer Architecture PRD

Version: 1.0

Status: Approved

---

# Purpose

This document defines the architecture of the BuildWise Tasks layer.

The objective is to leverage native CrewAI Tasks instead of building a custom
task orchestration framework.

Tasks represent **individual units of specialist work** performed by an agent.

The Flow owns orchestration.

Crews own execution.

Tasks own work.

Agents own reasoning.

---

# Position within BuildWise Architecture

```
                    FastAPI
                       │
                       ▼
                 API Router
                       │
                       ▼
                 Consulting Flow
                       │
              (Routing / State)
                       │
                       ▼
             Focused Crew Execution
                       │
                       ▼
              Native CrewAI Tasks
                       │
                       ▼
              Native CrewAI Agents
                       │
        Skills + Tools + Knowledge
                       │
                       ▼
           Structured Pydantic Output
                       │
                       ▼
             Flow State / Persistence
```

The Tasks layer must remain thin.

Business logic belongs elsewhere.

---

# Responsibilities

The Tasks layer is responsible for:

- defining work for an agent
- assigning an agent
- describing expected output
- specifying structured output model
- attaching task guardrails
- attaching task context
- configuring retries
- configuring asynchronous execution where appropriate

The Tasks layer is NOT responsible for:

- orchestration
- routing
- persistence
- validation platform
- state management
- API handling
- logging
- tracing
- cost tracking
- model routing

---

# Relationship with CrewAI

BuildWise should use native CrewAI Tasks.

Do NOT create custom Task subclasses.

Use the official CrewAI Task object.

Example:

```python
Task(
    description=...,
    expected_output=...,
    agent=...,
    output_pydantic=...,
)
```

BuildWise extends Tasks only through helper functions.

---

# Design Principles

## Principle 1

One task performs one business responsibility.

Never combine multiple specialist responsibilities into one task.

Good

Product Definition Task

Bad

Product + Architecture + Security Task

---

## Principle 2

Tasks should be deterministic.

The prompt may contain AI reasoning.

Task construction should not.

Task factories should contain almost no business logic.

---

## Principle 3

Tasks consume structured context.

Never concatenate huge strings manually.

Instead consume outputs produced by previous tasks.

---

## Principle 4

Every important task returns structured output.

Always prefer

output_pydantic

instead of JSON parsing.

---

## Principle 5

Guardrails belong on tasks.

Validation does not belong inside prompts.

---

## Principle 6

Task descriptions explain

WHAT

not

HOW.

The HOW belongs inside Skills.

---

# Responsibilities by Layer

Flow

Owns

- orchestration
- routing
- branching
- pause/resume
- human clarification
- retries
- persistence
- state

Crew

Owns

- task execution
- collaboration
- execution process

Task

Owns

- work definition
- context
- output schema
- expected output
- guardrails

Agent

Owns

- reasoning
- expertise
- decision making

Skill

Owns

- methodology

Tool

Owns

- external actions

Knowledge

Owns

- retrieval

---

# Task Construction Pattern

Every task file should expose factory functions.

Example

```python
def create_product_definition_task(...):

    return Task(...)
```

Never instantiate Tasks throughout the application.

Always use factory functions.

---

# Standard Task Structure

Every task should define

Name

Description

Expected Output

Assigned Agent

Structured Output

Guardrails

Retries

Context

Optional async execution

Nothing else.

---

# Standard Description Pattern

Descriptions should contain

Goal

Business context

Available artifacts

Constraints

Expected reasoning

Required output

They should NOT contain

validation logic

large methodology

implementation guidance

Those belong inside Skills.

---

# Expected Output

Every task must describe the expected artifact.

Examples

DiscoveryResult

ProductDefinition

RequirementsSpecification

SolutionArchitecture

AIArchitecture

SecurityArchitecture

LeadReview

Never say

"Generate a report."

Always specify the concrete artifact.

---

# Structured Output

Every major task uses

output_pydantic

Never manually parse JSON.

Never ask the model to emit custom JSON.

CrewAI already supports structured outputs.

---

# Task Context

Context should use

CrewAI Task context

instead of manually copying outputs.

Good

```
Task A

↓

Task B(context=[task_a])
```

Bad

Take the previous output and paste it into another prompt manually.

---

# Guardrails

Every important task should have deterministic validation.

Examples

Pydantic validation

Business invariant validation

Session validation

Artifact ownership validation

Never implement business reasoning inside guardrails.

---

# Retries

Use

guardrail_max_retries

Do not implement custom retry loops.

CrewAI already supports retries after guardrail failures.

---

# Async Tasks

Async execution should be rare.

Use it only when independent specialists can execute simultaneously.

Examples

Security

QA

Market

can execute independently.

Product Definition

cannot execute before Discovery.

---

# Human Input

Tasks should NOT directly ask humans questions.

Human clarification belongs to the Flow.

The Flow pauses execution.

After user input

the Flow resumes.

---

# Logging

Tasks should not log business events.

Flows and API middleware own logging.

---

# Cost Tracking

Tasks should not calculate token costs.

CrewAI runtime already exposes usage metrics.

Flow collects them.

---

# Tracing

Tasks should rely on CrewAI tracing.

Do not wrap every task in custom tracing code.

---

# Model Selection

Tasks never choose models.

Agent contracts already define

ModelTier

The Agent Factory resolves the actual LLM.

---

# Tool Selection

Tasks never instantiate tools.

Agents already own tools.

---

# Skills

Tasks never load Skills.

Agents already own Skills.

---

# Knowledge

Tasks never load Knowledge.

Agents already own Knowledge.

---

# MCP

Tasks never configure MCP servers.

Agents already own MCP integrations.

---

# Apps

Tasks never configure CrewAI Apps.

Agents already own Apps.

---

# Error Handling

Task creation should fail immediately when

agent missing

schema missing

guardrail missing

invalid configuration

Never silently ignore configuration problems.

---

# File Organization

```
tasks/

    __init__.py

    guardrails.py

    discovery.py

    product_definition.py

    requirements.py

    specialist_planning.py

    market_and_gtm.py

    solution_architecture.py

    ai_architecture.py

    security_architecture.py

    qa_evaluation.py

    lead_review.py
```

Each file owns one business capability.

Never create giant task files.

---

# Dependencies

Tasks depend on

Domain Models

↓

Agent Factory

↓

Native CrewAI Tasks

They never depend directly on

FastAPI

Database

Persistence

Flow State

HTTP

---

# Coding Standards

Every task factory

must

have type hints

have docstrings

return native CrewAI Task

remain under approximately 150 lines when practical

avoid hidden side effects

use dependency injection

avoid global mutable state

---

# Native CrewAI Features We Must Use

- Task
- output_pydantic
- context
- guardrails
- guardrail_max_retries
- async_execution (only where appropriate)

---

# Native CrewAI Features We Must NOT Rebuild

Do not implement

custom task runtime

custom retries

custom task graph

custom structured output parser

custom context passing

custom task scheduler

custom async execution

custom guardrail engine

CrewAI already provides these capabilities.

---

# Definition of Done

The Tasks layer is complete when

- every specialist capability has a dedicated task module
- every task returns structured output
- every task uses native CrewAI Task
- no manual JSON parsing exists
- no orchestration logic exists inside tasks
- no model routing exists inside tasks
- no persistence logic exists inside tasks
- task factories remain thin
- all validation occurs through CrewAI guardrails and domain validation
- tasks can be composed into focused Crews without modification