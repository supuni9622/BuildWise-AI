---
name: business-analyst
description: Methodology for converting an approved product definition into implementation-ready, traceable requirements.
---

# Requirements Methodology

## Step 1 — Trace every functional requirement to a feature

Each functional requirement should reference the `related_feature_ids` it
implements. A requirement with no traceable origin in the product
definition is a scope-creep smell — ask whether it truly belongs.

Use `category="ai"` on any functional requirement whose behavior
fundamentally requires model reasoning or generation (not just "uses an
API that happens to call a model somewhere"). This is the signal the
deterministic specialist planner reads to decide whether AI Architecture
work is needed — do not use it loosely.

## Step 2 — Write acceptance criteria that are actually testable

"Works correctly" is not an acceptance criterion. Prefer concrete
observable outcomes ("returns HTTP 422 with a field-level error when the
email is malformed").

## Step 3 — Classify non-functional requirements honestly

Only mark a non-functional requirement `must_have` when its absence would
make the product unfit for its stated purpose. Category matters: pick the
one (performance, availability, reliability, security, accessibility,
recoverability, data_integrity, compliance, scalability, usability) that
best drives downstream specialist selection — a `must_have` `security`
category NFR is a strong signal Security Architecture should run.

## Step 4 — Data, integrations, and journeys

For every integration requirement, decide `uses_llm_provider` and
`is_privileged` honestly — both influence AI Architecture and Security
Architecture selection downstream. Write user journeys as ordered steps
per persona, not prose paragraphs.

## Step 5 — Edge cases

Mark an edge case `blocking=True` only when failing to handle it would
break the product's core promise or create a safety/data-integrity issue —
this flag also feeds specialist selection (QA & Evaluation).

## Boundaries

Do not redesign the product definition, choose databases or cloud
providers, define service boundaries, design prompts or RAG, perform
threat modeling, or create release gates. Requirements must stay
implementation-independent.
