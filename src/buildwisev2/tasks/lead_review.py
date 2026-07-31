"""Lead Review Task factory."""

from __future__ import annotations

from crewai import Agent, Task

from buildwisev2.domain.review import LeadReview
from buildwisev2.tasks.guardrails import compose_guardrails, require_pydantic_output

REQUIRED_KICKOFF_KEYS = (
    "discovery_result",
    "product_definition",
    "requirements",
    "specialist_plan",
    "market_and_gtm",
    "solution_architecture",
    "ai_architecture",
    "security_architecture",
    "qa_evaluation",
    "revision_history",
)

_DESCRIPTION = """\
Objective
Perform the final cross-specialist review of this consultation. You do not
rewrite specialist work — you verify it and, if needed, request bounded
revisions.

Discovery
{discovery_result}

Product definition
{product_definition}

Requirements
{requirements}

Specialist execution plan (what was selected and why)
{specialist_plan}

Market & GTM strategy (states "Not selected." if omitted)
{market_and_gtm}

Solution architecture
{solution_architecture}

AI architecture (states "Not selected." if omitted)
{ai_architecture}

Security architecture (states "Not selected." if omitted)
{security_architecture}

QA & evaluation plan (states "Not selected." if omitted)
{qa_evaluation}

Prior revision history for this session
{revision_history}

Required decisions
- Verify completeness: every selected specialist's artifact is present and
  internally consistent. An artifact that was correctly not selected is
  NOT a gap.
- Verify cross-artifact consistency and traceability (requirements trace
  to product features; architecture covers requirements; security/QA
  reference real architecture components and controls).
- Identify contradictions, unsupported assumptions, and missing items.
- Assess implementation readiness with a 0.0-1.0 score.
- Choose exactly one decision: approved, approved_with_limitations,
  revision_required, or rejected, and keep approved_for_blueprint,
  revision_requests, and rejection_rationale consistent with that choice
  (see expected output contract).

Required output
A schema-valid LeadReview.

Important boundaries
Do not rewrite specialist outputs, invoke other Crews, assemble the final
blueprint, or communicate directly with the user.
"""


def create_lead_review_task(
    *,
    agent: Agent,
    guardrail_max_retries: int = 2,
) -> Task:
    """Create the Lead Review Task.

    Every input is a structured artifact supplied through Crew kickoff
    inputs (see ``REQUIRED_KICKOFF_KEYS``) — there is no same-Crew context
    to rely on since this Crew has exactly one Task.
    """

    return Task(
        name="lead_review",
        description=_DESCRIPTION,
        expected_output="A schema-valid LeadReview object.",
        agent=agent,
        output_pydantic=LeadReview,
        guardrails=compose_guardrails(require_pydantic_output(LeadReview)),
        guardrail_max_retries=guardrail_max_retries,
    )
