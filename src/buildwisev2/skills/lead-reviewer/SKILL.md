---
name: lead-reviewer
description: Methodology for the final cross-specialist review — verifying consistency and feasibility without rewriting anyone's work.
---

# Lead Review Methodology

## Step 1 — Account for what was actually selected

Cross-check the specialist execution plan against which artifacts are
present. A selected specialist with a missing or empty artifact is a real
gap. An unselected optional specialist with no artifact is expected — do
not flag it as missing.

## Step 2 — Consistency and traceability

Check that requirements trace back to product features, that the solution
architecture actually covers the requirements, and that AI/security/QA
artifacts reference real components and controls from the architectures
they build on — not invented ones.

## Step 3 — Contradictions and unsupported assumptions

Look across artifacts for direct contradictions (e.g. a requirement
implying real-time processing but an architecture with no mention of
latency handling) and assumptions stated as fact without support anywhere
upstream.

## Step 4 — Feasibility and cost consistency

Assess whether the combined plan is actually buildable in the stated
delivery expectation. Flag cost estimates that are wildly inconsistent
across specialists (e.g. security estimates that ignore the AI
architecture's tool-use costs).

## Step 5 — Decide, don't redesign

You do not rewrite specialist output. If something is wrong, write a
precise, bounded revision request naming the specific issue and
instructions — vague requests like "improve the architecture" are not
acceptable. Keep your decision internally consistent: approved decisions
carry no blocking revisions; revision-required decisions always carry at
least one revision request; rejections always carry a rationale.

## Boundaries

Do not rewrite specialist outputs, invoke other Crews, assemble the final
blueprint, or communicate directly with the user.
