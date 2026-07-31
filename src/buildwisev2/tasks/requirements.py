"""Requirements Task factory."""

from __future__ import annotations

from crewai import Agent, Task

from buildwisev2.domain.product import ProductDefinition
from buildwisev2.domain.requirements import RequirementsSpecification
from buildwisev2.domain.review import RevisionRequest
from buildwisev2.tasks.formatting import revision_section
from buildwisev2.tasks.guardrails import compose_guardrails, require_pydantic_output

OPTIONAL_KICKOFF_KEYS = ("product_definition",)

_DESCRIPTION_TEMPLATE = """\
Objective
Convert the approved product definition into implementation-ready
requirements.

Approved product definition
{product_definition_block}

Required decisions
- Functional requirements traceable to product feature ids.
- Non-functional requirements with an explicit category (performance,
  availability, reliability, security, accessibility, recoverability,
  data_integrity, compliance, scalability, usability, other).
- Business rules, data requirements, integration requirements (mark
  whether an integration uses an LLM provider or is privileged).
- User journeys per persona and blocking/non-blocking edge cases.
- Every functional requirement that is fundamentally AI-shaped must use
  category="ai" so downstream specialist planning can detect it.

Required output
A schema-valid RequirementsSpecification.

Important boundaries
Do not redesign the product definition, choose technologies, define
service boundaries, select AI models, design RAG, perform threat
modeling, or create release gates.

{revision_instructions}
"""


def create_requirements_task(
    *,
    agent: Agent,
    product_definition_task: Task | None = None,
    prior_product_definition: ProductDefinition | None = None,
    revision_request: RevisionRequest | None = None,
    guardrail_max_retries: int = 2,
) -> Task:
    """Create the Requirements Task.

    Consumes the approved Product Definition through exactly one of:

    - ``product_definition_task``: same-Crew dependency (native context) —
      used when Product Definition is being (re)generated in this run.
    - ``prior_product_definition``: an already-approved artifact from an
      earlier run, embedded as a kickoff placeholder — used for a targeted
      Requirements-only revision that must not force Product Definition to
      regenerate.
    """

    if (product_definition_task is None) == (prior_product_definition is None):
        raise ValueError(
            "create_requirements_task requires exactly one of "
            "product_definition_task or prior_product_definition."
        )

    if product_definition_task is not None:
        product_definition_block = "(provided above as prior Task context)"
        context = [product_definition_task]
    else:
        product_definition_block = "{product_definition}"
        context = None

    description = _DESCRIPTION_TEMPLATE.format(
        product_definition_block=product_definition_block,
        revision_instructions=revision_section(revision_request),
    )
    return Task(
        name="requirements",
        description=description,
        expected_output="A schema-valid RequirementsSpecification object.",
        agent=agent,
        context=context,
        output_pydantic=RequirementsSpecification,
        guardrails=compose_guardrails(require_pydantic_output(RequirementsSpecification)),
        guardrail_max_retries=guardrail_max_retries,
    )
