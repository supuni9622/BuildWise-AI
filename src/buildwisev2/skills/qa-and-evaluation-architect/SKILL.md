---
name: qa-and-evaluation-architect
description: Methodology for designing a quality and AI-evaluation plan proportional to product risk, validating what other specialists actually selected.
---

# QA & Evaluation Methodology

## Step 1 — Validate what was actually selected, not a template

Only include AI evaluation when an `AIArchitecture` was actually selected
for this consultation, and only include security-control validation when
a `SecurityArchitecture` was actually selected. Do not pad the plan with
sections for specialists that did not run.

## Step 2 — Quality objectives before test suites

State what "high quality" concretely means for this product before
listing test suites, so the suites can be justified against those
objectives rather than existing for their own sake.

## Step 3 — Critical scenarios and edge cases

Prioritize scenarios tied to blocking edge cases and must-have
non-functional requirements from the requirements specification. Trace
each critical scenario back to a requirement id where possible.

## Step 4 — Performance, reliability, AI evaluation

Write performance and reliability validation proportional to the stated
non-functional requirements — do not invent enterprise-grade targets for
a prototype. When AI Architecture exists, define an evaluation metric and
dataset approach per AI capability — a capability with no evaluation
approach is not actually validated.

## Step 5 — Release gates

Release gates must be enforceable — a human or automated check should be
able to determine pass/fail unambiguously. Mark a gate `blocking=True`
only when shipping without it passing would be irresponsible.

## Boundaries

Do not redesign architecture or requirements, select models, rewrite
security controls, or claim testing eliminates all risk. Keep QA scope
proportional to what was actually selected upstream.
