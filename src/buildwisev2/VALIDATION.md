# BuildWise v2 — Live End-to-End Validation

This tracks real runs of `buildwisev2` through the actual FastAPI server
against real OpenAI models (not the mocked unit test suite — see
`PROGRESS.md` for that). Purpose: prove the full stack works together
(API → Flow → Crews → Tasks → Agents → Skills → planner → revision loop →
blueprint assembly), capture timing characteristics, and record real bugs
these runs surfaced that the mocked suite couldn't catch.

## Run 3 — Timed instrumented run (FieldFlow logistics app)

**Date:** 2026-07-31
**Method:** An instrumented script (`e2e_timed_test.py`) posted a
consultation, auto-answered clarification rounds with generic responses,
logged a timestamped entry on every `(status, stage)` transition, and
fetched the final blueprint. Full JSONL log and raw result JSON are in the
session scratchpad (not committed — this doc is the durable record).

**Input:** A web app for small logistics companies — dispatcher route
creation/assignment, driver completion tracking, an AI-assisted route
optimization suggestion, sensitive personal data (driver names/phone/
addresses), no formal compliance requirement, MVP in 10 weeks / $50,000.
Designed to trigger AI + Security + QA specialists alongside the always-on
Solution Architect.

### Timing breakdown

| Stage | Duration | % of total |
|---|---|---|
| Discovery (round 1) | 60.1s (1.0 min) | 4.0% |
| Clarification wait (auto-answered) | 4.0s | 0.3% |
| Discovery (round 2, resolved) | 56.1s (0.9 min) | 3.8% |
| Product Planning (Product Manager + Business Analyst) | 164.3s (2.7 min) | 11.0% |
| Technical Planning (Solution + AI + Security + QA) | 372.6s (6.2 min) | 24.9% |
| Lead Review + revision loop | 837.4s (14.0 min) | 56.0% |
| **Total** | **1494.4s (24.9 min)** | 100% |

Note: the API's `stage` field maps both the initial Lead Review pass *and*
any subsequent revision re-runs to `"lead_review"` (that's the
frontend-facing vocabulary — see `api/service.py::_STAGE_MAP`), so the
14-minute bucket is not one LLM call; it's the first review, one or more
targeted-revision re-runs of technical specialists, and a second review
pass, combined. **Lead Review + revision is the dominant cost driver** —
worth watching if latency needs to come down later (candidates: tighter
revision-request scoping from Lead Review, or capping
`maximum_specialist_revisions` more aggressively for time-sensitive use).

### Result quality

| Metric | Value |
|---|---|
| Sections produced | 8/8 (discovery, product_definition, requirements, solution_architecture, ai_architecture, security_architecture, qa_evaluation, lead_review) |
| Final status | `completed_with_limitations` |
| Lead Review readiness score | 78% |
| Known facts / assumptions | 11 / 9 |
| MVP features | 5 |
| Functional / non-functional requirements | 5 / 10 |
| Solution architecture components / integrations / data stores | 11 / 4 / 4 |
| AI capabilities designed | 1 |
| Security threats / controls | 16 / 32 |
| QA test suites / release gates | 11 / 7 |
| Open questions | 10 |
| Limitations | 19 |
| Generated Markdown size | 46.4 KB |

### Bugs found and fixed by this run and the two runs before it

1. **Discovery/planner completeness mismatch** (found in Run 2, verified
   fixed by Run 3's clean completion). Exhausting the clarification-round
   budget while Discovery still reported `completeness.can_continue=False`
   crashed `run_specialist_planning`, stranding the consultation
   ("The consultation stopped" in the frontend). Fixed with
   `routing.force_continue_discovery` — see `PROGRESS.md`'s Flows section.
   Regression test:
   `test_consulting_flow_force_continues_after_clarification_rounds_exhausted`.

2. **Blueprint title echoing the full raw brief** (found in Run 2). The
   Product Manager agent sometimes writes a "vision" with no early
   sentence break, so the title heuristic emitted the entire brief
   verbatim (195 characters in Run 3, since the fix — described next —
   wasn't yet live in the process that served Run 3; the server needs a
   restart to load new source). Fixed with
   `reporting.blueprint_builder._derive_title`: caps to `_MAX_TITLE_LENGTH`
   (90 chars) with a word-safe truncation + ellipsis. Covered by
   `test_derive_title_caps_length_when_vision_has_no_early_sentence_break`.
   **Not yet re-verified live** — needs a server restart to pick up the
   fix, then a fresh run to confirm the title comes back bounded.

## Run 2 — Manual run (BuildWise-describes-itself meta product)

**Date:** 2026-07-31. Deliberately recursive: asked BuildWise v2 to plan
BuildWise itself (multi-agent AI consulting platform, AI-core, sensitive
data). Triggered Solution + AI + Security + QA (8/8 sections, 55.2 KB
Markdown, `completed_with_limitations`, readiness 72%). This is where bugs
#1 and #2 above were found. Two full clarification rounds (11 questions
each) before Discovery resolved; total wall-clock time was long enough
(~30+ min including the pre-fix crash-and-restart) that exact per-stage
timing wasn't captured — Run 3 exists specifically to get clean timing
data on a fresh, correct process.

## Run 1 — Mocked-crew smoke test (internal scheduling tool)

**Date:** 2026-07-31, during initial API build-out (see `PROGRESS.md`).
Used a lightweight product idea to get a fast first signal that
API → Flow → Crews → blueprint assembly worked at all. Selected
Solution + Security + QA (correctly omitted AI, no AI capability in that
product). Completed successfully; first live proof the stack works.

## Open follow-ups

- [ ] Re-run after a server restart to confirm the title fix is live.
- [ ] If Lead Review + revision latency matters for the product, profile
      whether it's dominated by model latency (gpt-5.2 on ADVANCED tier,
      4 sequential architecture tasks, twice) or by an avoidable
      re-generation (e.g. revision requests broader than necessary).
- [ ] No automated timing regression test exists — these are manual/
      scripted runs, not part of `tests/unit_v2/` (which stays mock-only
      and fast by design, per `PROGRESS.md`).
