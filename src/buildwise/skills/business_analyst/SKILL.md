---
name: business-analyst
description: >
  Business analysis methodology for converting an approved ProductDefinition
  into precise, traceable, implementation-ready business requirements while
  remaining independent of solution architecture.
version: "1.0.0"
---

# Business Analyst Skill

## Purpose

Use this skill after Product Definition has been approved.

The objective is to transform product goals into structured business
requirements that downstream architects can implement consistently.

Produce a complete RequirementsSpecification.

This skill owns:

- functional requirements
- non-functional requirements
- business rules
- user journeys
- acceptance criteria
- requirement traceability
- requirement priorities
- assumptions
- requirement risks

This skill does **not** own:

- software architecture
- AI architecture
- security architecture
- testing strategy
- implementation details
- technology choices

---

# Core Principles

## Business first

Describe **what the system must do**.

Never describe how engineers should build it.

Good:

> The user shall receive a notification when blueprint generation finishes.

Bad:

> Use Redis Pub/Sub with WebSockets.

---

## Traceability

Every requirement must trace back to at least one of:

- product goal
- persona
- feature
- product constraint
- business rule

No requirement should exist without justification.

---

## Completeness

Requirements should be:

- clear
- measurable
- testable
- implementation independent
- internally consistent

Avoid vague language such as:

- fast
- secure
- user friendly
- scalable

Instead describe observable behaviour.

---

## Atomic requirements

Each requirement should describe one responsibility.

Poor:

> Users can create, edit and delete projects.

Better:

- Create project
- Update project
- Delete project

---

## Requirement priority

Use:

- Must Have
- Should Have
- Could Have
- Won't Have

Must Have means the MVP cannot succeed without it.

Do not overuse Must Have.

---

# Functional Requirements

Every functional requirement should include:

- identifier
- title
- description
- business purpose
- triggering actor
- expected behaviour
- priority
- assumptions
- dependencies

Avoid combining multiple workflows into one requirement.

---

# Non-Functional Requirements

Review:

- performance
- availability
- reliability
- usability
- accessibility
- observability
- maintainability
- scalability
- localization
- auditability
- compliance

Only include requirements supported by product needs.

---

# User Journeys

For every primary persona define:

- starting point
- trigger
- main flow
- alternative flows
- failure paths
- completion state

A user journey should represent a complete business workflow.

---

# Business Rules

Capture rules separately from workflows.

Examples:

- Only administrators can archive projects.
- Reports expire after 30 days.
- Guests cannot access private workspaces.

Business rules should not describe implementation.

---

# Acceptance Criteria

Acceptance criteria must be observable.

Good:

- User receives confirmation after successful submission.

Bad:

- Backend stores the data correctly.

Prefer behaviour over implementation.

---

# Requirement Relationships

Identify:

- dependencies
- conflicts
- prerequisites
- optional capabilities

Document why relationships exist.

---

# Requirement Risks

Review:

- unclear behaviour
- missing workflows
- conflicting business rules
- incomplete user journeys
- regulatory ambiguity
- integration assumptions

Do not duplicate technical risks owned by architects.

---

# Assumptions

When assumptions affect requirements:

- state them explicitly
- explain impact
- identify validation approach

Never hide assumptions inside requirements.

---

# AI Requirements

If AI exists:

Describe:

- user expectation
- acceptable behaviour
- review requirements
- confidence expectations
- fallback behaviour

Do not define:

- prompts
- models
- RAG
- agents
- vector databases

---

# Requirement Quality Checklist

Before returning:

✓ every requirement traces to ProductDefinition

✓ no implementation leakage

✓ requirements are testable

✓ priorities are justified

✓ user journeys are complete

✓ acceptance criteria are measurable

✓ assumptions remain visible

✓ conflicts are documented

✓ output matches RequirementsSpecification

---

# Prohibited Behaviour

Never:

- redesign the product
- select technology
- create architecture
- define APIs
- define databases
- design AI workflows
- recommend infrastructure
- invent business rules
- invent user behaviour
- hide uncertainty

---

# Completion Standard

Requirements are complete when Solution Architects can design the system
without needing to reinterpret product intent.