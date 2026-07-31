"""Discovery Task factory."""

from __future__ import annotations

from crewai import Agent, Task

from buildwisev2.domain.discovery import DiscoveryResult
from buildwisev2.tasks.guardrails import compose_guardrails, require_pydantic_output

REQUIRED_KICKOFF_KEYS = ("product_idea", "clarification_context")

_DESCRIPTION = """\
Objective
Interpret the submitted product idea and produce a structured discovery
assessment. Preserve the user's actual intent — do not invent scope they
did not describe.

Submitted product idea
{product_idea}

Clarification context (may state "None yet.")
{clarification_context}

Required decisions
- Extract known facts, assumptions, unknowns, and early risks separately.
- Produce a preliminary capability classification (AI/RAG/agents/automation,
  sensitive data, regulated domain, real-time, external integrations).
- Assess completeness: can this proceed, or are there blocking unknowns
  that require the user to clarify before continuing?
- If clarification is required, write concrete clarification questions.

Required output
A schema-valid DiscoveryResult.

Important boundaries
Do not define product features, MVP scope, or architecture. Do not decide
which specialists should run later. Do not ask the user directly — return
clarification_questions in the structured output instead.
"""


def create_discovery_task(
    *,
    agent: Agent,
    guardrail_max_retries: int = 2,
) -> Task:
    """Create the Discovery Task. Consumes ``product_idea`` and
    ``clarification_context`` through Crew kickoff inputs (see
    ``REQUIRED_KICKOFF_KEYS``)."""

    return Task(
        name="product_discovery",
        description=_DESCRIPTION,
        expected_output="A schema-valid DiscoveryResult object.",
        agent=agent,
        output_pydantic=DiscoveryResult,
        guardrails=compose_guardrails(require_pydantic_output(DiscoveryResult)),
        guardrail_max_retries=guardrail_max_retries,
    )
