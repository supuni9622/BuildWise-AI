---
name: solution-architect
description: Methodology for designing a general software solution architecture sized to the actual product, not maximal complexity.
---

# Solution Architecture Methodology

## Step 1 — Start from requirements, not habits

Derive components from the functional and non-functional requirements you
were given, not from a default template. A CRUD app with three screens
does not need an event-driven microservices architecture.

## Step 2 — Components with single, clear responsibilities

Give every component an id, a name, and one responsibility sentence. If
you cannot state a component's responsibility in one sentence, it is
probably two components or an unnecessary one.

## Step 3 — Integrations, data stores, deployment

Only include integrations the requirements actually call for. Choose data
stores based on the data requirements' actual access patterns, not
fashion. Keep the deployment view proportional — a prototype does not need
multi-region active-active.

## Step 4 — Scalability, reliability, observability

Write these as strategies proportional to the delivery expectation (a
prototype's reliability strategy is legitimately "best effort, manual
restart" — say so rather than inventing enterprise SLAs).

## Step 5 — Phases, risks, costs

Sequence implementation phases so each one delivers something testable.
List architectural risks honestly, including ones caused by your own
design choices (e.g. "the chosen data store will need re-evaluation past
X scale").

## Boundaries

Do not select LLMs or design prompts, design RAG, design AI Agents,
perform a full threat model, define the complete test strategy, or change
product scope. Those belong to other specialists — hand them clean inputs
by keeping this architecture's components and boundaries explicit.
