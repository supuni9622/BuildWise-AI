"""Security Architecture domain models — output of the Technical Planning
Crew (Security Architect).
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from buildwisev2.domain.common import BuildWiseModel


class SecurityArchitectureDecision(StrEnum):
    APPROVED = "approved"
    APPROVED_WITH_LIMITATIONS = "approved_with_limitations"
    NEEDS_REVISION = "needs_revision"


class TrustBoundary(BuildWiseModel):
    name: str
    description: str


class Threat(BuildWiseModel):
    id: str
    description: str
    severity: str
    related_control_ids: list[str] = Field(default_factory=list)


class SecurityControl(BuildWiseModel):
    id: str
    name: str
    description: str
    validation_method: str | None = None


class DataClassification(BuildWiseModel):
    data_type: str
    classification: str
    handling_notes: str


class ResidualRisk(BuildWiseModel):
    description: str
    severity: str
    accepted: bool = False
    rationale: str | None = None


class SecurityArchitecture(BuildWiseModel):
    """Structured output of the Security Architect's Task.

    Threats without at least one referenced control, and controls with no
    referencing threat, indicate an incomplete threat model — this is
    validated by task guardrails, not this model directly, to keep the
    domain layer free of cross-collection business logic beyond structural
    integrity.
    """

    session_id: UUID
    identity_architecture: str
    authentication_strategy: str
    authorization_strategy: str
    privileged_access_controls: list[str] = Field(default_factory=list)
    secrets_management: str
    encryption_strategy: str
    data_classifications: list[DataClassification] = Field(default_factory=list)
    retention_policy: str
    trust_boundaries: list[TrustBoundary] = Field(default_factory=list)
    threats: list[Threat]
    controls: list[SecurityControl]
    audit_requirements: list[str] = Field(default_factory=list)
    compliance_considerations: list[str] = Field(default_factory=list)
    residual_risks: list[ResidualRisk] = Field(default_factory=list)
    incident_response_readiness: str
    implementation_phases: list[str] = Field(default_factory=list)
    cost_estimates: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    decision: SecurityArchitectureDecision

    def control_ids(self) -> set[str]:
        return {control.id for control in self.controls}
