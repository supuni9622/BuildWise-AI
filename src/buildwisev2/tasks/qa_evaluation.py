"""QA & Evaluation Task factory."""

from __future__ import annotations

from crewai import Agent, Task

from buildwisev2.domain.ai_architecture import AIArchitecture
from buildwisev2.domain.architecture import SolutionArchitecture
from buildwisev2.domain.qa import QAEvaluationPlan
from buildwisev2.domain.review import RevisionRequest
from buildwisev2.domain.security_architecture import SecurityArchitecture
from buildwisev2.tasks.formatting import resolve_upstream_artifact, revision_section
from buildwisev2.tasks.guardrails import compose_guardrails, require_pydantic_output

REQUIRED_KICKOFF_KEYS = ("requirements",)
OPTIONAL_KICKOFF_KEYS = (
    "solution_architecture_context",
    "ai_architecture_context",
    "security_architecture_context",
)

_DESCRIPTION_TEMPLATE = """\
Objective
Design the quality and AI-evaluation plan for the architectures selected
for this consultation.

Solution architecture
{solution_architecture_block}

AI architecture
{ai_architecture_block}

Security architecture
{security_architecture_block}

Approved requirements
{{requirements}}

Required decisions
- Quality objectives and overall test strategy.
- Test suites and critical scenarios, mapped to requirement ids.
- Performance and reliability validation approach.
- If AI architecture is present: an AI evaluation plan (metric + dataset
  per capability). If absent, leave ai_evaluation empty — do not invent one.
- If security architecture is present: security-control validation steps
  referencing its controls. If absent, leave it empty.
- Enforceable, bounded release gates and production quality signals.

Required output
A schema-valid QAEvaluationPlan.

Important boundaries
Do not redesign architecture or requirements, select models, rewrite
security controls, or claim testing eliminates all risk.

{revision_instructions}
"""


def create_qa_evaluation_task(
    *,
    agent: Agent,
    solution_architecture_task: Task | None = None,
    prior_solution_architecture: SolutionArchitecture | None = None,
    ai_architecture_task: Task | None = None,
    prior_ai_architecture: AIArchitecture | None = None,
    security_architecture_task: Task | None = None,
    prior_security_architecture: SecurityArchitecture | None = None,
    revision_request: RevisionRequest | None = None,
    guardrail_max_retries: int = 2,
) -> Task:
    """Create the QA & Evaluation Task.

    Solution Architecture is mandatory context: supply exactly one of
    ``solution_architecture_task`` or ``prior_solution_architecture``. AI
    and Security Architecture context are each optional and mutually
    exclusive between their live/prior forms — both absent means that
    specialist was not selected for this consultation.
    """

    if (solution_architecture_task is None) == (prior_solution_architecture is None):
        raise ValueError(
            "create_qa_evaluation_task requires exactly one of "
            "solution_architecture_task or prior_solution_architecture."
        )
    if ai_architecture_task is not None and prior_ai_architecture is not None:
        raise ValueError(
            "create_qa_evaluation_task accepts at most one of "
            "ai_architecture_task or prior_ai_architecture."
        )
    if security_architecture_task is not None and prior_security_architecture is not None:
        raise ValueError(
            "create_qa_evaluation_task accepts at most one of "
            "security_architecture_task or prior_security_architecture."
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
    security_architecture_block, security_context_task = resolve_upstream_artifact(
        live_task=security_architecture_task,
        prior_artifact=prior_security_architecture,
        label="security architecture",
        placeholder_key="security_architecture_context",
    )

    description = _DESCRIPTION_TEMPLATE.format(
        solution_architecture_block=solution_architecture_block,
        ai_architecture_block=ai_architecture_block,
        security_architecture_block=security_architecture_block,
        revision_instructions=revision_section(revision_request),
    )
    context = [
        task
        for task in (solution_context_task, ai_context_task, security_context_task)
        if task is not None
    ]

    return Task(
        name="qa_evaluation",
        description=description,
        expected_output="A schema-valid QAEvaluationPlan object.",
        agent=agent,
        context=context or None,
        output_pydantic=QAEvaluationPlan,
        guardrails=compose_guardrails(require_pydantic_output(QAEvaluationPlan)),
        guardrail_max_retries=guardrail_max_retries,
    )
