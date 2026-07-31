"""AI Architecture domain models — output of the Technical Planning Crew (AI Architect)."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from buildwisev2.domain.common import BuildWiseModel, CapabilityType


class AIArchitectureDecision(StrEnum):
    APPROVED = "approved"
    APPROVED_WITH_LIMITATIONS = "approved_with_limitations"
    NEEDS_REVISION = "needs_revision"


class AICapability(BuildWiseModel):
    id: str
    name: str
    capability_type: CapabilityType
    justification: str


class ModelSelection(BuildWiseModel):
    role: str
    provider: str
    model: str
    rationale: str


class PromptContract(BuildWiseModel):
    name: str
    purpose: str
    input_schema: str | None = None


class RAGDesign(BuildWiseModel):
    ingestion_strategy: str
    retrieval_strategy: str
    chunking_strategy: str


class AIAgentDesign(BuildWiseModel):
    name: str
    role: str
    tools: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)


class AIWorkflow(BuildWiseModel):
    name: str
    description: str
    agent_names: list[str] = Field(default_factory=list)


class AIEvaluationApproach(BuildWiseModel):
    metric: str
    method: str


class AIGuardrail(BuildWiseModel):
    name: str
    description: str


class AIArchitecture(BuildWiseModel):
    """Structured output of the AI Architect's Task.

    Must fit inside the approved ``SolutionArchitecture`` rather than
    redesigning it — task-level guardrails validate that referenced
    component ids resolve against the upstream architecture.
    """

    session_id: UUID
    capabilities: list[AICapability]
    deterministic_alternatives_considered: list[str] = Field(default_factory=list)
    model_selections: list[ModelSelection] = Field(default_factory=list)
    prompt_contracts: list[PromptContract] = Field(default_factory=list)
    tool_policies: list[str] = Field(default_factory=list)
    agent_designs: list[AIAgentDesign] = Field(default_factory=list)
    workflows: list[AIWorkflow] = Field(default_factory=list)
    rag_design: RAGDesign | None = None
    guardrails: list[AIGuardrail] = Field(default_factory=list)
    evaluation_approach: list[AIEvaluationApproach] = Field(default_factory=list)
    observability: list[str] = Field(default_factory=list)
    human_oversight: str
    fallback_behavior: str
    risks: list[str] = Field(default_factory=list)
    cost_controls: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    decision: AIArchitectureDecision
