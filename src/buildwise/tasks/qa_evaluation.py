"""QA and Evaluation task factory.

Creates the native CrewAI Task assigned to the QA and Evaluation Architect.
The task defines the test strategy, test suites and scenarios, performance
and reliability requirements, evaluation metrics, and release gates for the
approved solution (and its AI and security architectures, when selected).
"""

from __future__ import annotations

from crewai import Agent, Task

from buildwise.domain.ai_architecture import AIArchitecture
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.qa import QAEvaluationPlan
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import RevisionRequest
from buildwise.domain.security import SecurityArchitecture
from buildwise.tasks.guardrails import (
    compose_guardrails,
    require_non_empty_collections,
    require_pydantic_output,
)
from buildwise.tasks.revisions import format_revision_instructions

DEFAULT_GUARDRAIL_MAX_RETRIES = 2


def create_qa_evaluation_task(
    *,
    agent: Agent,
    requirements: RequirementsSpecification,
    solution_architecture: SolutionArchitecture,
    ai_architecture: AIArchitecture | None = None,
    security_architecture: SecurityArchitecture | None = None,
    revision_request: RevisionRequest | None = None,
    guardrail_max_retries: int = DEFAULT_GUARDRAIL_MAX_RETRIES,
) -> Task:
    """Build the QA and Evaluation task for the QA and Evaluation Architect.

    Only create this task when specialist planning selects QA and
    evaluation. When QA needs the final security output, run this task after
    Security Architecture rather than concurrently with it.

    Args:
        agent: Native CrewAI agent created for
            ``AgentType.QA_AND_EVALUATION_ARCHITECT``.
        requirements: The approved RequirementsSpecification.
        solution_architecture: The approved SolutionArchitecture.
        ai_architecture: The approved AIArchitecture, when AI architecture
            was selected. ``None`` when it was not.
        security_architecture: The approved SecurityArchitecture, when
            security architecture was selected. ``None`` when it was not.
        revision_request: A bounded targeted-revision instruction from the
            Lead Reviewer.
        guardrail_max_retries: Bounded guardrail retry budget.

    Returns:
        A native ``crewai.Task`` producing a ``QAEvaluationPlan``.
    """

    if agent is None:
        raise ValueError("create_qa_evaluation_task requires an agent.")

    if guardrail_max_retries < 0:
        raise ValueError("guardrail_max_retries cannot be negative.")

    context_lines = [
        f"RequirementsSpecification: {requirements.model_dump_json()}",
        f"SolutionArchitecture: {solution_architecture.model_dump_json()}",
    ]

    if ai_architecture is not None:
        context_lines.append(f"AIArchitecture: {ai_architecture.model_dump_json()}")

    if security_architecture is not None:
        context_lines.append(f"SecurityArchitecture: {security_architecture.model_dump_json()}")

    ai_instruction = (
        "- Define AI evaluation coverage (accuracy, groundedness, safety, or "
        "task-success metrics) for every AI capability in the supplied "
        "AIArchitecture.\n"
        if ai_architecture is not None
        else ""
    )
    security_instruction = (
        "- Define validation activities that confirm the security controls "
        "in the supplied SecurityArchitecture are effective.\n"
        if security_architecture is not None
        else ""
    )

    description = (
        "Objective: Design the QA and evaluation strategy for the approved "
        "solution.\n\n"
        "Available structured context:\n" + "\n".join(context_lines) + "\n\n"
        "Required decisions:\n"
        "- Define a test strategy and the test suites and scenarios needed "
        "to validate the must-have functional and non-functional "
        "requirements.\n"
        "- Define acceptance tests for the product's critical user "
        "journeys.\n"
        "- Define performance and reliability requirements consistent with "
        "the solution architecture's scalability and availability targets.\n"
        f"{ai_instruction}"
        f"{security_instruction}"
        "- Define release gates that must pass before shipping, and "
        "quality risks with mitigations.\n\n"
        "Required output: A schema-valid QAEvaluationPlan with at least one "
        "release gate and at least one test scenario.\n\n"
        "Important boundaries:\n"
        "- Do not redesign the solution, AI, or security architecture.\n"
        "- Do not build a custom evaluation framework; describe the "
        "strategy, metrics, and gates only.\n\n"
        "Failure or uncertainty handling: If a quality attribute cannot be "
        "responsibly validated with the given context, record it as a "
        "quality_risk rather than inventing a test that cannot actually be "
        "executed."
    )

    if revision_request is not None:
        description += "\n\n" + format_revision_instructions(revision_request)

    expected_output = (
        "A schema-valid QAEvaluationPlan JSON object matching the "
        "QAEvaluationPlan Pydantic model exactly, with no additional prose."
    )

    guardrails = compose_guardrails(
        require_pydantic_output(QAEvaluationPlan),
        require_non_empty_collections(
            QAEvaluationPlan,
            "release_gates",
            "test_scenarios",
        ),
    )

    return Task(
        name="qa_evaluation",
        description=description,
        expected_output=expected_output,
        agent=agent,
        output_pydantic=QAEvaluationPlan,
        guardrails=guardrails,
        guardrail_max_retries=guardrail_max_retries,
    )
