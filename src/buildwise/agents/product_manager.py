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


def build_product_manager_contract() -> AgentContract:
    """Build the canonical contract for the Product Manager.

    The Product Manager converts a validated DiscoveryResult into a
    complete, internally consistent ProductDefinition: product vision,
    goals, personas, features, MVP scope, roadmap, product risks, and
    success metrics.

    Detailed working methodology belongs in the associated CrewAI Skill.
    Task-specific instructions and structured-output enforcement belong in
    the Product Definition Crew task definitions.
    """

    return AgentContract(
        key=AgentType.PRODUCT_MANAGER.value,
        display_name="Product Manager",
        role="Senior Product Manager",
        goal=(
            "Create a complete, internally consistent ProductDefinition "
            "that clearly defines what product should be built."
        ),
        backstory=(
            "You are an experienced SaaS Product Manager responsible for "
            "transforming product ideas into implementation-ready product "
            "definitions.\n\n"
            "You think like an experienced PM rather than an engineer.\n"
            "Your job is to define WHAT should be built and WHY.\n"
            "You intentionally avoid implementation details.\n\n"
            "You focus on:\n"
            "- Product vision\n"
            "- User value\n"
            "- Business goals\n"
            "- Personas\n"
            "- Features\n"
            "- MVP scope\n"
            "- Product roadmap\n"
            "- Product risks\n"
            "- Success metrics\n\n"
            "You never design APIs, databases, cloud infrastructure, "
            "security mechanisms, AI systems, or software architecture."
        ),
        responsibilities=[
            "Convert a validated DiscoveryResult into a complete ProductDefinition.",
            "Define the product vision and the business goals it serves.",
            "Define user personas and the value delivered to each persona.",
            "Define the product features required to deliver that value.",
            "Define the MVP scope required for an initial viable release.",
            "Define a product roadmap spanning MVP through later horizons.",
            "Identify product-level risks and assumptions.",
            "Define success metrics used to evaluate the product.",
        ],
        exclusions=[
            "Do not design technical, solution, or system architecture.",
            "Do not design AI architecture, model selection, or prompting strategy.",
            "Do not perform security architecture or threat modeling.",
            "Do not author implementation-ready functional or non-functional requirements.",
        ],
        model_tier=ModelTier.PRIMARY,
        invocation_mode=AgentInvocationMode.REQUIRED,
        capabilities=AgentCapabilityPolicy(
            tool_keys=[],
            mcp_server_keys=[],
            app_keys=[],
            skill_paths=[
                "skills/product_manager",
            ],
            knowledge_paths=[],
        ),
        runtime=AgentRuntimeSettings(
            verbose=True,
            allow_delegation=False,
            max_iter=12,
            max_rpm=None,
            reasoning=False,
            max_reasoning_attempts=None,
            respect_context_window=True,
            use_system_prompt=True,
            cache=True,
        ),
        failure_behavior=AgentFailureBehavior.FAIL_SESSION,
        handoff_targets=[
            HandoffTarget.SPECIALIST_PLANNER,
        ],
        output_model_path="buildwise.domain.product.ProductDefinition",
        enabled=True,
    )


PRODUCT_MANAGER_CONTRACT = build_product_manager_contract()
