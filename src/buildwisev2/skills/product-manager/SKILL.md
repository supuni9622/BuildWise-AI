---
name: product-manager
description: Methodology for converting an approved discovery assessment into a scoped, prioritized product definition.
---

# Product Definition Methodology

## Step 1 — Anchor on vision and value proposition

State the vision in one or two sentences: who this is for and what changes
for them. The value proposition should name the specific pain being
removed, not generic benefits ("saves time" is not specific; "eliminates
the weekly manual reconciliation spreadsheet" is).

## Step 2 — Define personas from what discovery actually surfaced

Do not invent personas beyond what the discovery assessment's known facts
and target users support. Each persona needs concrete goals and pain
points, not demographic filler.

## Step 3 — Generate and prioritize features with MoSCoW

For every feature, ask: "does the vision survive without this in v1?" If
yes, it is not `must_have`. Be ruthless — a bloated MVP is a design
failure. Select the `mvp_feature_ids` subset explicitly; do not just mark
everything `must_have`.

Mark `ai_enabled=True` on a feature only when it genuinely requires model
reasoning or generation to work — this flag feeds the downstream
specialist planner's AI Architecture decision, so false positives cause
unnecessary specialist work and false negatives hide real AI scope.

## Step 4 — Roadmap and exclusions

Group non-MVP features into a small number of roadmap phases with a clear
theme each. Explicit exclusions matter as much as inclusions — write down
what you are deliberately NOT building and why, so it doesn't get silently
re-added later.

## Step 5 — Success metrics

Prefer metrics that are measurable from product usage over vague
aspirations. Tie at least one metric back to the core value proposition.

## Boundaries

Do not create detailed functional/non-functional requirements, choose
technology, perform market research yourself, select AI models, or define
security or QA plans. Preserve discovery's facts — do not silently
contradict them.
