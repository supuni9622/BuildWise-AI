"""Security Architecture Task factory."""

from __future__ import annotations

from crewai import Agent, Task

from buildwisev2.domain.ai_architecture import AIArchitecture
from buildwisev2.domain.architecture import SolutionArchitecture
from buildwisev2.domain.review import RevisionRequest
from buildwisev2.domain.security_architecture import SecurityArchitecture
from buildwisev2.tasks.formatting import resolve_upstream_artifact, revision_section
from buildwisev2.tasks.guardrails import compose_guardrails, require_pydantic_output

REQUIRED_KICKOFF_KEYS = ("requirements",)
OPTIONAL_KICKOFF_KEYS = ("solution_architecture_context", "ai_architecture_context")

_DESCRIPTION_TEMPLATE = """\
Objective
Design the security architecture required by the proposed system, built on
top of the solution architecture and AI architecture (if selected).

Solution architecture
{solution_architecture_block}

AI architecture
{ai_architecture_block}

Approved requirements
{{requirements}}

Required decisions
- Identity, authentication, authorization, and privileged-access design.
- Secrets management, encryption strategy, data classification, retention.
- Trust boundaries and attack surfaces.
- A threat model: every threat must reference at least one control id,
  and every control must be referenced by at least one threat.
- Audit requirements, compliance considerations (applicability only — you
  never issue formal certification), and residual risk with explicit
  acceptance rationale for anything left unmitigated.
- Incident-response readiness, implementation phases, and cost estimates.

Required output
A schema-valid SecurityArchitecture.

Important boundaries
Do not redesign software components or AI workflows, select product
features, or approve organizational risk or the final blueprint. Never
claim formal legal or compliance certification.

{revision_instructions}
"""


def create_security_architecture_task(
    *,
    agent: Agent,
    solution_architecture_task: Task | None = None,
    prior_solution_architecture: SolutionArchitecture | None = None,
    ai_architecture_task: Task | None = None,
    prior_ai_architecture: AIArchitecture | None = None,
    revision_request: RevisionRequest | None = None,
    guardrail_max_retries: int = 2,
) -> Task:
    """Create the Security Architecture Task.

    Solution Architecture is mandatory context: supply exactly one of
    ``solution_architecture_task`` or ``prior_solution_architecture``. AI
    Architecture context is optional and mutually exclusive between its
    live/prior forms: supply at most one of ``ai_architecture_task`` or
    ``prior_ai_architecture`` (both absent means AI was not selected for
    this consultation).
    """

    if (solution_architecture_task is None) == (prior_solution_architecture is None):
        raise ValueError(
            "create_security_architecture_task requires exactly one of "
            "solution_architecture_task or prior_solution_architecture."
        )
    if ai_architecture_task is not None and prior_ai_architecture is not None:
        raise ValueError(
            "create_security_architecture_task accepts at most one of "
            "ai_architecture_task or prior_ai_architecture."
        )

    solution_architecture_block, solution_context_task = resolve_upstream_artifact(
        live_task=solution_architecture_task,
        prior_artifact=prior_solution_architecture,
        label="solution architecture",
        placeholder_key="solution_architecture_context",
    )
    ai_architecture_block, ai_context_task = resolve_upstream_artifact(
        live_task=ai_architecture_task,
        prior_artifact=prior_ai_architecture,
        label="AI architecture",
        placeholder_key="ai_architecture_context",
    )

    description = _DESCRIPTION_TEMPLATE.format(
        solution_architecture_block=solution_architecture_block,
        ai_architecture_block=ai_architecture_block,
        revision_instructions=revision_section(revision_request),
    )
    context = [task for task in (solution_context_task, ai_context_task) if task is not None]

    return Task(
        name="security_architecture",
        description=description,
        expected_output="A schema-valid SecurityArchitecture object.",
        agent=agent,
        context=context or None,
        output_pydantic=SecurityArchitecture,
        guardrails=compose_guardrails(require_pydantic_output(SecurityArchitecture)),
        guardrail_max_retries=guardrail_max_retries,
    )
