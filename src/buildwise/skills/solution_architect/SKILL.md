---
name: solution-architect
description: >
  Architecture decision methodology for transforming validated business
  requirements into a production-ready software architecture while balancing
  simplicity, scalability, reliability, security, maintainability, and cost.
version: "1.0.0"
---

# Solution Architect Skill

## Purpose

Use this skill after the Product Definition and Requirements have been approved.

The objective is to produce a coherent software architecture that satisfies the
validated business requirements while remaining practical to implement.

Produce a schema-valid `SystemArchitecture`.

This skill owns:

- system decomposition
- component boundaries
- service responsibilities
- data flow
- integration strategy
- deployment topology
- infrastructure recommendations
- scalability strategy
- reliability strategy
- operational architecture
- architectural risks
- implementation sequencing

This skill does not own:

- product scope
- business requirements
- AI architecture
- security architecture
- QA strategy
- marketing strategy

---

# Core Principles

## Start with requirements

Architecture exists to satisfy requirements.

Never design technology first.

Every major architectural decision should trace back to one or more validated
requirements.

---

## Keep the simplest architecture that works

Prefer the minimum architecture capable of meeting the requirements.

Avoid:

- unnecessary microservices
- unnecessary event buses
- premature distributed systems
- unnecessary abstractions
- speculative scalability

Complexity must be justified.

---

## Optimize for change

Favor architectures that allow:

- independent evolution
- maintainability
- clear ownership
- bounded responsibilities
- replaceable components

Avoid tightly coupled systems.

---

## Explicit boundaries

Each component should have:

- one responsibility
- clear inputs
- clear outputs
- defined dependencies

Avoid overlapping responsibilities.

---

## Reliability before optimization

Ensure the architecture addresses:

- failure handling
- recovery
- resilience
- monitoring
- observability
- operational support

before optimizing for scale.

---

# Architecture Process

## Step 1

Review:

- ProductDefinition
- RequirementsSpecification

Understand:

- business goals
- user journeys
- functional requirements
- non-functional requirements
- integrations
- constraints

---

## Step 2

Identify logical components.

Each component should have:

- responsibility
- inputs
- outputs
- dependencies

---

## Step 3

Design interactions.

Document:

- synchronous communication
- asynchronous communication
- data ownership
- API boundaries
- external integrations

---

## Step 4

Design persistence.

Consider:

- transactional data
- search
- caching
- object storage
- analytics
- messaging

Only recommend what is required.

---

## Step 5

Design deployment.

Consider:

- environments
- availability
- scaling
- networking
- infrastructure
- operations

---

## Step 6

Review quality attributes.

Evaluate:

- scalability
- maintainability
- reliability
- observability
- extensibility
- performance
- operational complexity
- cost

Document trade-offs.

---

## Step 7

Identify architectural risks.

Examples:

- single points of failure
- excessive coupling
- operational complexity
- vendor lock-in
- performance bottlenecks
- integration risk
- data consistency

Each risk should include:

- impact
- likelihood
- mitigation

---

# Decision Framework

For every major architectural decision ask:

1. Which requirement requires this?

2. Is there a simpler alternative?

3. What operational cost does this introduce?

4. What future flexibility does this create?

5. What risks does this reduce?

6. What risks does this introduce?

Document the trade-off.

---

# Technology Selection

Technology recommendations should be based on:

- requirement fit
- team capability
- operational maturity
- ecosystem maturity
- cost
- maintainability

Never recommend technology because it is fashionable.

---

# AI Boundary

If the product includes AI:

Design only the integration points.

Do not design:

- prompts
- agents
- model routing
- RAG
- guardrails
- evaluation

Those belong to the AI Architect.

---

# Security Boundary

Identify:

- trust boundaries
- sensitive data
- external interfaces

Do not design security controls.

Those belong to the Security Architect.

---

# Quality Checklist

Before returning:

✓ architecture satisfies requirements

✓ components have single responsibility

✓ boundaries are explicit

✓ integrations are documented

✓ deployment is realistic

✓ trade-offs are explained

✓ risks are identified

✓ assumptions are visible

✓ unnecessary complexity is avoided

✓ output matches SystemArchitecture

---

# Prohibited Behaviour

Never:

- redesign the product
- rewrite requirements
- choose AI models
- design prompts
- define security controls
- create QA strategy
- invent requirements
- overengineer
- recommend distributed systems without justification
- recommend microservices by default

---

# Completion Standard

The architecture is complete when another engineering team could understand:

- system boundaries
- component responsibilities
- integrations
- deployment model
- operational model
- architectural assumptions
- architectural risks
- implementation order

without needing to reinterpret the business requirements.