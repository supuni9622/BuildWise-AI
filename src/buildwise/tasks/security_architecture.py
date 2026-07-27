"""Security Architecture task factory.

Creates the native CrewAI Task assigned to the Security Architect. The task
defines identity, secrets, encryption, data protection, threat modeling,
controls, audit, compliance, and residual risk for the approved solution
(and AI architecture, when one was selected).

``solution_architecture`` and ``ai_architecture`` each support two input
modes: same-Crew native task context (when composed inside the Technical
Planning Crew) or a literal structured value (when the upstream artifact
already completed in a separate Crew).
"""

from __future__ import annotations

from typing import Any

from crewai import Agent, Task
from crewai.tasks.task_output import TaskOutput

from buildwise.domain.ai_architecture import AIArchitecture
from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.enums import RiskLikelihood, RiskSeverity
from buildwise.domain.requirements import RequirementsSpecification
from buildwise.domain.review import RevisionRequest
from buildwise.domain.security import SecurityArchitecture
from buildwise.tasks.guardrails import compose_guardrails, require_pydantic_output
from buildwise.tasks.revisions import format_revision_instructions

DEFAULT_GUARDRAIL_MAX_RETRIES = 2


def create_security_architecture_task(
    *,
    agent: Agent,
    requirements: RequirementsSpecification,
    solution_architecture_task: Task | None = None,
    solution_architecture: SolutionArchitecture | None = None,
    ai_architecture_task: Task | None = None,
    ai_architecture: AIArchitecture | None = None,
    revision_request: RevisionRequest | None = None,
    guardrail_max_retries: int = DEFAULT_GUARDRAIL_MAX_RETRIES,
) -> Task:
    """Build the Security Architecture task for the Security Architect.

    Only create this task when specialist planning selects security
    architecture. Exactly one of ``solution_architecture_task`` or
    ``solution_architecture`` must be supplied. When AI architecture was
    also selected, supply exactly one of ``ai_architecture_task`` or
    ``ai_architecture``; when it was not selected, omit both and the task
    remains fully valid using only requirements and solution architecture.

    Args:
        agent: Native CrewAI agent created for
            ``AgentType.SECURITY_ARCHITECT``.
        requirements: The approved RequirementsSpecification.
        solution_architecture_task: The Solution Architecture task, when
            executing in the same Crew.
        solution_architecture: The completed SolutionArchitecture, when it
            ran in a separate Crew.
        ai_architecture_task: The AI Architecture task, when executing in
            the same Crew and AI architecture was selected.
        ai_architecture: The completed AIArchitecture, when it ran in a
            separate Crew and AI architecture was selected.
        revision_request: A bounded targeted-revision instruction from the
            Lead Reviewer.
        guardrail_max_retries: Bounded guardrail retry budget.

    Returns:
        A native ``crewai.Task`` producing a ``SecurityArchitecture``.
    """

    if agent is None:
        raise ValueError("create_security_architecture_task requires an agent.")

    if guardrail_max_retries < 0:
        raise ValueError("guardrail_max_retries cannot be negative.")

    if solution_architecture_task is None and solution_architecture is None:
        raise ValueError(
            "create_security_architecture_task requires either "
            "solution_architecture_task or solution_architecture."
        )

    if solution_architecture_task is not None and solution_architecture is not None:
        raise ValueError(
            "create_security_architecture_task accepts only one of "
            "solution_architecture_task or solution_architecture, not both."
        )

    if ai_architecture_task is not None and ai_architecture is not None:
        raise ValueError(
            "create_security_architecture_task accepts only one of "
            "ai_architecture_task or ai_architecture, not both."
        )

    context_lines = [f"RequirementsSpecification: {requirements.model_dump_json()}"]
    context_tasks: list[Task] = []

    if solution_architecture_task is not None:
        context_lines.append("SolutionArchitecture: provided as native task context.")
        context_tasks.append(solution_architecture_task)
    else:
        context_lines.append(
            f"SolutionArchitecture: {solution_architecture.model_dump_json()}"  # type: ignore[union-attr]
        )

    if ai_architecture_task is not None:
        context_lines.append("AIArchitecture: provided as native task context.")
        context_tasks.append(ai_architecture_task)
    elif ai_architecture is not None:
        context_lines.append(f"AIArchitecture: {ai_architecture.model_dump_json()}")

    description = (
        "Objective: Design the security architecture for the approved "
        "solution.\n\n"
        "Available structured context:\n" + "\n".join(context_lines) + "\n\n"
        "Required decisions:\n"
        "- Define identity, authentication, and authorization strategy.\n"
        "- Define secret management and encryption at rest and in "
        "transit.\n"
        "- Define PII handling, data classifications, and retention "
        "policies.\n"
        "- Build a threat model (attack surfaces, trust boundaries, "
        "threats, and attack scenarios) covering the solution architecture "
        "components and connections.\n"
        "- Recommend controls, each referencing the threat identifiers it "
        "mitigates.\n"
        "- Define security requirements, validation activities, audit "
        "requirements, and applicable compliance frameworks.\n"
        "- Record residual risks and an incident response plan.\n\n"
        "Required output: A schema-valid SecurityArchitecture with at least "
        "one identified threat and at least one recommended control, where "
        "every control's mitigated_threats references a threat identifier "
        "that actually appears in threat_model.threats.\n\n"
        "Important boundaries:\n"
        "- Do not redesign application components or technology choices; "
        "those belong to SolutionArchitecture.\n"
        "- Do not design the QA or test strategy.\n"
        "- Do not represent a compliance framework as certified or audited "
        "unless the supplied context already establishes that.\n\n"
        "Failure or uncertainty handling: A residual risk that is critical "
        "and likely (or almost certain) to occur must not be marked "
        "accepted; escalate it as unaccepted with a mitigation plan instead."
    )

    if revision_request is not None:
        description += "\n\n" + format_revision_instructions(revision_request)

    expected_output = (
        "A schema-valid SecurityArchitecture JSON object matching the "
        "SecurityArchitecture Pydantic model exactly, with no additional "
        "prose."
    )

    guardrails = compose_guardrails(
        require_pydantic_output(SecurityArchitecture),
        _validate_security_completeness,
    )

    task_kwargs: dict[str, object] = {
        "name": "security_architecture",
        "description": description,
        "expected_output": expected_output,
        "agent": agent,
        "output_pydantic": SecurityArchitecture,
        "guardrails": guardrails,
        "guardrail_max_retries": guardrail_max_retries,
    }

    if context_tasks:
        task_kwargs["context"] = context_tasks

    return Task(**task_kwargs)


def _validate_security_completeness(task_output: TaskOutput) -> tuple[bool, Any]:
    """Validate threat/control coverage and residual-risk acceptance rules.

    ``SecurityArchitecture`` does not define its own cross-field validators,
    so these runtime invariants are enforced here instead of inside the
    domain model.
    """

    output = task_output.pydantic

    if not isinstance(output, SecurityArchitecture):
        return (
            False,
            "The task did not produce a SecurityArchitecture in "
            "TaskOutput.pydantic. Return a schema-valid SecurityArchitecture.",
        )

    if not output.threat_model.threats:
        return (
            False,
            "threat_model.threats must identify at least one threat.",
        )

    if not output.controls:
        return (
            False,
            "controls must recommend at least one security control.",
        )

    threat_identifiers = {threat.identifier for threat in output.threat_model.threats}

    for control in output.controls:
        unknown_threats = set(control.mitigated_threats).difference(threat_identifiers)

        if unknown_threats:
            formatted = ", ".join(sorted(unknown_threats))
            return (
                False,
                (
                    f"Control '{control.identifier}' references unknown "
                    f"threats in mitigated_threats: {formatted}. "
                    "mitigated_threats must reference identifiers already "
                    "present in threat_model.threats."
                ),
            )

    control_identifiers = {control.identifier for control in output.controls}

    for validation in output.validations:
        if validation.control_identifier not in control_identifiers:
            return (
                False,
                (
                    f"Security validation references unknown "
                    f"control_identifier '{validation.control_identifier}'. "
                    "Reference an identifier already present in controls."
                ),
            )

    for risk in output.residual_risks:
        if (
            risk.accepted
            and risk.severity is RiskSeverity.CRITICAL
            and risk.likelihood
            in {
                RiskLikelihood.LIKELY,
                RiskLikelihood.ALMOST_CERTAIN,
            }
        ):
            return (
                False,
                (
                    f"Residual risk '{risk.identifier}' cannot be accepted "
                    "while critical and likely or almost-certain to occur. "
                    "Set accepted to false and document a mitigation plan."
                ),
            )

    return (True, task_output)
