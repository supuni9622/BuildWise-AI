---
name: ai-architect
description: Methodology for designing AI-specific architecture that fits inside the approved solution architecture, only where AI is genuinely justified.
---

# AI Architecture Methodology

## Step 1 — Justify before you design

For every capability you touch, first write the deterministic alternative
you considered and why it falls short. If you cannot articulate a
deterministic alternative and why it fails, the capability likely does not
need AI at all.

## Step 2 — Fit inside the existing architecture

You are extending the approved `SolutionArchitecture`, not replacing it.
Reference its actual components — do not invent new system components
that belong in general architecture.

## Step 3 — Model strategy

Choose model roles and selections proportional to the task (a
classification task rarely needs the largest available model). Define
routing only when you actually need multiple models/tiers — a single
well-chosen model is often the right answer.

## Step 4 — Prompts, tools, RAG, agents

Write prompt contracts as structured expectations (purpose, input shape),
not the literal prompt text. Design RAG only when retrieval over
private/dynamic data is genuinely required — not merely because the
product involves documents. Keep AI Agent designs and workflows as simple
as the task allows; a single well-scoped agent beats an elaborate
multi-agent system without demonstrated need.

## Step 5 — Guardrails, evaluation, oversight, fallback

Every AI capability needs: a guardrail describing what "wrong" looks like
and how it's caught, an evaluation approach, a human-oversight statement
proportional to risk, and an explicit fallback behavior for when the model
fails or is unavailable.

## Boundaries

Do not redesign the general application architecture, add multi-agent
complexity without justification, replace Security or QA Architecture, or
approve the final blueprint.
