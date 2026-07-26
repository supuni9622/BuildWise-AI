"""Lead Review task factory.

Creates the native CrewAI Task assigned to the Lead Reviewer. The task
performs the final cross-specialist review: consistency, completeness,
traceability, feasibility, and implementation readiness across every
required and selected specialist artifact, producing a ``LeadReview`` with a
bounded set of revision requests and an approval decision.
"""

from __future__ import annotations

from crewai import Agent, Task

from buildwise.domain.ai_architecture import AIArchitecture
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.discovery import DiscoveryResult
from buildwise.domain.market_and_gtm import MarketAndGTMStrategy
from buildwise.domain.product import ProductDefinition
from buildwise.domain.qa import QAEvaluationPlan
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import LeadReview, RevisionRequest
from buildwise.domain.security import SecurityArchitecture
from buildwise.domain.specialist_planning import SpecialistExecutionPlan
from buildwise.tasks.guardrails import (
    compose_guardrails,
    require_pydantic_output,
    require_review_consistency,
)

DEFAULT_GUARDRAIL_MAX_RETRIES = 2


def create_lead_review_task(
    *,
    agent: Agent,
    discovery: DiscoveryResult,
    product_definition: ProductDefinition,
    requirements: RequirementsSpecification,
    specialist_plan: SpecialistExecutionPlan,
    market_and_gtm: MarketAndGTMStrategy | None = None,
    solution_architecture: SolutionArchitecture | None = None,
    ai_architecture: AIArchitecture | None = None,
    security_architecture: SecurityArchitecture | None = None,
    qa_evaluation: QAEvaluationPlan | None = None,
    revision_history: list[RevisionRequest] | None = None,
    guardrail_max_retries: int = DEFAULT_GUARDRAIL_MAX_RETRIES,
) -> Task:
    """Build the Lead Review task for the Lead Reviewer.

    Every required artifact (discovery, product definition, requirements,
    and the specialist execution plan) must be supplied. Every conditional
    specialist artifact is optional and must be treated as correctly
    unselected rather than as a failure when it is ``None``.

    Args:
        agent: Native CrewAI agent created for ``AgentType.LEAD_REVIEWER``.
        discovery: The completed DiscoveryResult.
        product_definition: The approved ProductDefinition.
        requirements: The approved RequirementsSpecification.
        specialist_plan: The specialist selection and execution plan.
        market_and_gtm: The completed MarketAndGTMStrategy, when selected.
        solution_architecture: The completed SolutionArchitecture, when
            selected.
        ai_architecture: The completed AIArchitecture, when selected.
        security_architecture: The completed SecurityArchitecture, when
            selected.
        qa_evaluation: The completed QAEvaluationPlan, when selected.
        revision_history: Revision requests already issued in prior review
            rounds, so the reviewer does not re-request an already-addressed
            change.
        guardrail_max_retries: Bounded guardrail retry budget.

    Returns:
        A native ``crewai.Task`` producing a ``LeadReview``.
    """

    if agent is None:
        raise ValueError("create_lead_review_task requires an agent.")

    if guardrail_max_retries < 0:
        raise ValueError("guardrail_max_retries cannot be negative.")

    context_lines = [
        f"DiscoveryResult: {discovery.model_dump_json()}",
        f"ProductDefinition: {product_definition.model_dump_json()}",
        f"RequirementsSpecification: {requirements.model_dump_json()}",
        f"SpecialistExecutionPlan: {specialist_plan.model_dump_json()}",
    ]

    optional_artifacts = {
        "MarketAndGTMStrategy": market_and_gtm,
        "SolutionArchitecture": solution_architecture,
        "AIArchitecture": ai_architecture,
        "SecurityArchitecture": security_architecture,
        "QAEvaluationPlan": qa_evaluation,
    }

    for label, artifact in optional_artifacts.items():
        if artifact is not None:
            context_lines.append(f"{label}: {artifact.model_dump_json()}")

    selected_labels = [
        label for label, artifact in optional_artifacts.items() if artifact is not None
    ]
    unselected_labels = [
        label for label, artifact in optional_artifacts.items() if artifact is None
    ]

    revision_history_section = ""

    if revision_history:
        formatted_history = "\n".join(
            f"  - target={entry.target.value}, reason={entry.reason}" for entry in revision_history
        )
        revision_history_section = (
            "\nRevision requests already issued in prior review rounds "
            "(do not re-request these unless they remain unresolved):\n"
            f"{formatted_history}\n"
        )

    description = (
        "Objective: Perform the final cross-specialist review of this "
        "BuildWise consultation and decide whether it is ready for blueprint "
        "assembly.\n\n"
        "Available structured context:\n" + "\n".join(context_lines) + "\n\n"
        f"Selected specialist artifacts included above: "
        f"{', '.join(selected_labels) or 'none'}.\n"
        f"Specialist artifacts not selected for this consultation (treat as "
        f"correctly out of scope, not as failures): "
        f"{', '.join(unselected_labels) or 'none'}.\n"
        f"{revision_history_section}\n"
        "Required decisions:\n"
        "- Verify completeness of every required and selected artifact.\n"
        "- Verify cross-artifact consistency and requirement traceability.\n"
        "- Identify contradictions, unsupported assumptions, and missing "
        "items.\n"
        "- Review specialist selection against the supplied "
        "SpecialistExecutionPlan.\n"
        "- Review architectural, AI, security, and QA feasibility for every "
        "selected artifact.\n"
        "- Review risks and cost consistency across artifacts.\n"
        "- Assess implementation readiness and assign an "
        "implementation_readiness_score.\n"
        "- Produce findings, consistency checks, and any bounded revision "
        "requests.\n"
        "- Decide the final review decision and whether blueprint assembly "
        "may proceed.\n\n"
        "Required output: A schema-valid LeadReview whose decision, "
        "approved_for_blueprint, findings, and revision_requests are "
        "mutually consistent:\n"
        "- approved -> approved_for_blueprint=true, no blocking revision "
        "requests.\n"
        "- approved_with_limitations -> approved_for_blueprint=true, "
        "limitations must exist.\n"
        "- revision_required -> approved_for_blueprint=false, at least one "
        "revision request.\n"
        "- rejected -> approved_for_blueprint=false, documented weaknesses "
        "or contradictions explaining the rejection.\n\n"
        "Important boundaries:\n"
        "- Do not rewrite or redesign any specialist output; only evaluate "
        "it.\n"
        "- Do not invoke or simulate specialist agents.\n"
        "- Do not assemble the final blueprint.\n"
        "- Keep every revision request bounded and scoped to one "
        "RevisionTarget; do not request a full regeneration when a "
        "targeted fix is sufficient.\n\n"
        "Failure or uncertainty handling: When an artifact you would "
        "normally expect is missing because it was not selected, note that "
        "explicitly in your reasoning rather than treating it as a defect."
    )

    expected_output = (
        "A schema-valid LeadReview JSON object matching the LeadReview "
        "Pydantic model exactly, with no additional prose."
    )

    guardrails = compose_guardrails(
        require_pydantic_output(LeadReview),
        require_review_consistency,
    )

    return Task(
        name="lead_review",
        description=description,
        expected_output=expected_output,
        agent=agent,
        output_pydantic=LeadReview,
        guardrails=guardrails,
        guardrail_max_retries=guardrail_max_retries,
    )
