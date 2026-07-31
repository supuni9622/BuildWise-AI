"""Solution Architecture Task factory."""

from __future__ import annotations

from crewai import Agent, Task

from buildwisev2.domain.architecture import SolutionArchitecture
from buildwisev2.domain.review import RevisionRequest
from buildwisev2.tasks.formatting import revision_section
from buildwisev2.tasks.guardrails import compose_guardrails, require_pydantic_output

REQUIRED_KICKOFF_KEYS = ("requirements",)

_DESCRIPTION_TEMPLATE = """\
Objective
Design the general software solution architecture that satisfies the
approved requirements.

Approved requirements
{{requirements}}

Required decisions
- System context and components, each with an id and single responsibility.
- Integrations, data stores, and a deployment view.
- Scalability, reliability, and observability strategy.
- Implementation phases and rough cost estimates.
- Architectural risks and assumptions.

Required output
A schema-valid SolutionArchitecture.

Important boundaries
Do not select LLMs, define prompts, design RAG, perform a full threat
model, or define the complete test strategy. Do not change product scope.

{revision_instructions}
"""


def create_solution_architecture_task(
    *,
    agent: Agent,
    revision_request: RevisionRequest | None = None,
    guardrail_max_retries: int = 2,
) -> Task:
    """Create the Solution Architecture Task. Consumes ``requirements`` via kickoff inputs."""

    description = _DESCRIPTION_TEMPLATE.format(
        revision_instructions=revision_section(revision_request),
    )
    return Task(
        name="solution_architecture",
        description=description,
        expected_output="A schema-valid SolutionArchitecture object.",
        agent=agent,
        output_pydantic=SolutionArchitecture,
        guardrails=compose_guardrails(require_pydantic_output(SolutionArchitecture)),
        guardrail_max_retries=guardrail_max_retries,
    )
