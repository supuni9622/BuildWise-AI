"""AI Architecture Task factory."""

from __future__ import annotations

from crewai import Agent, Task

from buildwisev2.domain.ai_architecture import AIArchitecture
from buildwisev2.domain.architecture import SolutionArchitecture
from buildwisev2.domain.review import RevisionRequest
from buildwisev2.tasks.formatting import resolve_upstream_artifact, revision_section
from buildwisev2.tasks.guardrails import compose_guardrails, require_pydantic_output

REQUIRED_KICKOFF_KEYS = ("requirements",)
OPTIONAL_KICKOFF_KEYS = ("solution_architecture_context",)

_DESCRIPTION_TEMPLATE = """\
Objective
Design the AI-specific architecture that fits inside the approved solution
architecture {solution_architecture_block} for the requirements below.

Approved requirements
{{requirements}}

Required decisions
- For every AI capability, name the deterministic alternative you
  considered and why AI is justified instead.
- Define model roles/selections, prompt contracts, and tool-use policies.
- Define any AI Agent designs and workflows genuinely required.
- Define RAG design only if retrieval over private/dynamic data is needed.
- Define AI guardrails, evaluation approach, observability, human
  oversight, and fallback behavior.
- Identify AI-specific risks and cost controls.

Required output
A schema-valid AIArchitecture. Component/system references must be
consistent with the solution architecture above — do not invent new
components.

Important boundaries
Do not redesign the general application architecture, add multi-agent
systems without justification, replace Security or QA Architecture, or
approve the final blueprint.

{revision_instructions}
"""


def create_ai_architecture_task(
    *,
    agent: Agent,
    solution_architecture_task: Task | None = None,
    prior_solution_architecture: SolutionArchitecture | None = None,
    revision_request: RevisionRequest | None = None,
    guardrail_max_retries: int = 2,
) -> Task:
    """Create the AI Architecture Task.

    Depends on the Solution Architecture through exactly one of
    ``solution_architecture_task`` (same-Crew, being regenerated this run)
    or ``prior_solution_architecture`` (an earlier run's approved artifact,
    reused because this targeted revision does not touch it).
    """

    if (solution_architecture_task is None) == (prior_solution_architecture is None):
        raise ValueError(
            "create_ai_architecture_task requires exactly one of "
            "solution_architecture_task or prior_solution_architecture."
        )

    solution_architecture_block, context_task = resolve_upstream_artifact(
        live_task=solution_architecture_task,
        prior_artifact=prior_solution_architecture,
        label="solution architecture",
        placeholder_key="solution_architecture_context",
    )
    description = _DESCRIPTION_TEMPLATE.format(
        solution_architecture_block=solution_architecture_block,
        revision_instructions=revision_section(revision_request),
    )
    return Task(
        name="ai_architecture",
        description=description,
        expected_output="A schema-valid AIArchitecture object.",
        agent=agent,
        context=[context_task] if context_task is not None else None,
        output_pydantic=AIArchitecture,
        guardrails=compose_guardrails(require_pydantic_output(AIArchitecture)),
        guardrail_max_retries=guardrail_max_retries,
    )
