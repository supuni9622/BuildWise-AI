"""Shared base model and cross-cutting enums for the BuildWise v2 domain layer."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class BuildWiseModel(BaseModel):
    """Base Pydantic model for every BuildWise v2 domain artifact.

    ``extra="forbid"`` ensures agents cannot smuggle unexpected fields
    through structured output, and every artifact stays serializable via
    ``model_dump(mode="json")`` for Crew inputs.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class SpecialistType(StrEnum):
    """Optional/conditional specialist capabilities selectable by the planner."""

    MARKET_AND_GTM = "market_and_gtm"
    SOLUTION_ARCHITECTURE = "solution_architecture"
    AI_ARCHITECTURE = "ai_architecture"
    SECURITY_ARCHITECTURE = "security_architecture"
    QA_AND_EVALUATION = "qa_and_evaluation"


class CapabilityType(StrEnum):
    """Preliminary capability classification produced during Discovery."""

    DETERMINISTIC = "deterministic"
    AI_ASSISTED = "ai_assisted"
    AI_CORE = "ai_core"
    RAG = "rag"
    AGENTIC_WORKFLOW = "agentic_workflow"


class FlowRuntimeLimits(BuildWiseModel):
    """Coarse session-level execution limits consumed by the Flow and planner.

    These are policy inputs, not measured usage. The planner uses them only
    to decide budget-constrained specialist selection; it never estimates
    exact token or dollar cost.
    """

    maximum_session_tokens: int = 400_000
    maximum_estimated_cost_usd: float = 5.0
    maximum_agent_executions: int = 20
    maximum_tool_calls: int = 20
    maximum_specialist_revisions: int = 2
    maximum_execution_seconds: int = 900
    maximum_clarification_rounds: int = 2
