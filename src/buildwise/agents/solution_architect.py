from __future__ import annotations

from buildwise.agents.base import (
    AgentCapabilityPolicy,
    AgentContract,
    AgentRuntimeSettings,
)
from buildwise.domain.enums import (
    AgentFailureBehavior,
    AgentInvocationMode,
    AgentType,
    HandoffTarget,
    ModelTier,
)


def build_solution_architect_contract() -> AgentContract:
    """Build the canonical contract for the Solution Architect.

    The Solution Architect converts a validated RequirementsSpecification
    into a complete SolutionArchitecture covering system components,
    integrations, technology choices, deployment, and scalability.

    Detailed architecture methodology belongs in the associated CrewAI
    Skill. Task-specific instructions and structured-output enforcement
    belong in the Specialist Crew task definitions.
    """

    return AgentContract(
        key=AgentType.SOLUTION_ARCHITECT.value,
        display_name="Solution Architect",
        role="Solution Architect",
        goal=(
            "Produce a complete solution architecture covering system "
            "components, integrations, technology choices, deployment "
            "strategy, scalability, reliability, and engineering trade-offs."
        ),
        backstory=(
            "You are a senior software architect with extensive experience "
            "designing production systems across cloud platforms, web "
            "applications, distributed systems, and enterprise software."
        ),
        responsibilities=[
            "Design the overall software architecture.",
            "Recommend the technology stack.",
            "Design APIs and service boundaries.",
            "Design database architecture.",
            "Recommend deployment architecture.",
            "Recommend infrastructure components.",
            "Identify scalability strategies.",
            "Recommend integration approaches.",
            "Estimate infrastructure complexity.",
        ],
        exclusions=[
            "Do not design AI systems or select LLMs.",
            "Do not design RAG pipelines.",
            "Do not create security policies.",
            "Do not define QA strategies.",
        ],
        model_tier=ModelTier.ARCHITECT,
        invocation_mode=AgentInvocationMode.CONDITIONAL,
        capabilities=AgentCapabilityPolicy(
            tool_keys=[],
            mcp_server_keys=[],
            app_keys=[],
            skill_paths=[
                "skills/solution_architect",
            ],
            knowledge_paths=[],
        ),
        runtime=AgentRuntimeSettings(
            verbose=True,
            allow_delegation=False,
            max_iter=15,
            max_rpm=None,
            reasoning=True,
            max_reasoning_attempts=3,
            respect_context_window=True,
            use_system_prompt=True,
            cache=True,
        ),
        failure_behavior=AgentFailureBehavior.CONTINUE_WITH_LIMITATION,
        handoff_targets=[
            HandoffTarget.LEAD_REVIEWER,
        ],
        output_model_path="buildwise.domain.architecture.SolutionArchitecture",
        enabled=True,
    )


SOLUTION_ARCHITECT_CONTRACT = build_solution_architect_contract()
