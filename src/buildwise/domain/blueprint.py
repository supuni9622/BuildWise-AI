from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from buildwise.domain.enums import BlueprintSectionType

# =============================================================================
# Source References
# =============================================================================


class SourceReference(BaseModel):
    """
    Reference supporting a blueprint section.
    """

    model_config = ConfigDict(extra="forbid")

    source: str = Field(
        description="Origin of the information.",
        examples=[
            "User Idea",
            "Clarification Answer",
            "Discovery Analysis",
            "Market Research",
            "Architecture Review",
        ],
    )

    description: str

    url: str | None = None

    notes: str | None = None


# =============================================================================
# Blueprint Section
# =============================================================================


class BlueprintSection(BaseModel):
    """
    Individual section of the final BuildWise blueprint.
    """

    model_config = ConfigDict(extra="forbid")

    section: BlueprintSectionType

    title: str

    summary: str

    markdown: str = Field(
        description="Markdown representation of the section.",
    )

    references: list[SourceReference] = Field(
        default_factory=list,
    )

    notes: str | None = None


# =============================================================================
# Usage Summary
# =============================================================================


class UsageSummary(BaseModel):
    """
    AI execution summary for the consultation.
    """

    model_config = ConfigDict(extra="forbid")

    total_agents: int = 0

    total_llm_calls: int = 0

    prompt_tokens: int = 0

    completion_tokens: int = 0

    total_tokens: int = 0

    estimated_cost: float | None = Field(
        default=None,
        ge=0,
    )

    execution_time_seconds: float = Field(
        default=0,
        ge=0,
    )

    model_usage: dict[str, int] = Field(
        default_factory=dict,
        description="Model -> number of invocations.",
    )


# =============================================================================
# Product Blueprint
# =============================================================================


class ProductBlueprint(BaseModel):
    """
    Final BuildWise deliverable assembled after Lead Review.

    This document combines all specialist outputs into one
    implementation-ready blueprint.
    """

    model_config = ConfigDict(extra="forbid")

    title: str

    executive_summary: str

    sections: list[BlueprintSection] = Field(
        default_factory=list,
    )

    implementation_phases: list[str] = Field(
        default_factory=list,
    )

    assumptions: list[str] = Field(
        default_factory=list,
    )

    risks: list[str] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        default_factory=list,
    )

    open_questions: list[str] = Field(
        default_factory=list,
        description="Unresolved decisions that still require an answer.",
    )

    limitations: list[str] = Field(
        default_factory=list,
    )

    usage_summary: UsageSummary

    generated_markdown: str = Field(
        description="Complete markdown version of the blueprint.",
    )

    version: str = Field(
        default="1.0",
    )
