from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from buildwise.domain.common import (
    ConfidenceLevel,
    CostCategory,
    CostFrequency,
    RiskLikelihood,
    RiskSeverity,
)


# =============================================================================
# Authentication
# =============================================================================


class AuthenticationStrategy(BaseModel):
    """
    Defines how users authenticate to the platform.
    """

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(
        description="Authentication provider.",
        examples=["Auth0", "AWS Cognito", "Clerk"],
    )

    protocol: str = Field(
        description="Authentication protocol.",
        examples=["OIDC", "OAuth2", "SAML"],
    )

    supports_mfa: bool = Field(
        default=True,
        description="Whether MFA is supported.",
    )

    supports_social_login: bool = Field(
        default=False,
        description="Whether social login is supported.",
    )

    session_strategy: str = Field(
        description="JWT, Cookie, Session etc.",
    )

    justification: str = Field(
        description="Reason this strategy was selected.",
    )


# =============================================================================
# Authorization
# =============================================================================


class AuthorizationStrategy(BaseModel):
    """
    Defines access control approach.
    """

    model_config = ConfigDict(extra="forbid")

    model: str = Field(
        description="Authorization model.",
        examples=["RBAC", "ABAC", "Hybrid"],
    )

    description: str

    resource_level_permissions: bool = True

    tenant_isolation: bool = False

    notes: str | None = None


# =============================================================================
# Identity Architecture
# =============================================================================


class IdentityArchitecture(BaseModel):
    """
    Complete identity and access architecture.
    """

    model_config = ConfigDict(extra="forbid")

    authentication: AuthenticationStrategy

    authorization: AuthorizationStrategy

    user_identity_store: str = Field(
        description="Primary identity store.",
    )

    supports_api_keys: bool = False

    supports_service_accounts: bool = False

    supports_machine_identity: bool = False

    notes: str | None = None


# =============================================================================
# Secret Management
# =============================================================================


class SecretManagementStrategy(BaseModel):
    """
    Strategy for storing application secrets.
    """

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(
        description="Secret management platform.",
        examples=[
            "AWS Secrets Manager",
            "Vault",
            "1Password",
        ],
    )

    automatic_rotation: bool = True

    rotation_period_days: Annotated[
        int,
        Field(
            ge=1,
            le=365,
        ),
    ] = 90

    environment_separation: bool = True

    encrypted_at_rest: bool = True

    notes: str |None = None

# =============================================================================
# Encryption
# =============================================================================


class EncryptionStrategy(BaseModel):
    """
    Defines how sensitive data is encrypted.
    """

    model_config = ConfigDict(extra="forbid")

    data_at_rest: bool = True

    data_in_transit: bool = True

    algorithm_at_rest: str = Field(
        default="AES-256",
        description="Encryption algorithm for stored data.",
    )

    protocol_in_transit: str = Field(
        default="TLS 1.3",
        description="Protocol protecting network communication.",
    )

    customer_managed_keys: bool = False

    key_rotation_enabled: bool = True

    key_rotation_days: Annotated[
        int,
        Field(
            ge=1,
            le=365,
        ),
    ] = 90

    notes: str | None = None


# =============================================================================
# PII Handling
# =============================================================================


class PIIHandlingStrategy(BaseModel):
    """
    Strategy for collecting and protecting personally identifiable information.
    """

    model_config = ConfigDict(extra="forbid")

    collects_pii: bool

    pii_categories: list[str] = Field(
        default_factory=list,
        description="Examples: email, phone number, address.",
    )

    masking_enabled: bool = True

    anonymization_enabled: bool = False

    pseudonymization_enabled: bool = False

    deletion_supported: bool = True

    retention_policy_reference: str | None = None

    notes: str | None = None


# =============================================================================
# Data Classification
# =============================================================================


class DataClassification(BaseModel):
    """
    Defines a category of data handled by the system.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="Classification name.",
        examples=[
            "Public",
            "Internal",
            "Confidential",
            "Restricted",
        ],
    )

    description: str

    encryption_required: bool = True

    audit_logging_required: bool = False

    retention_period_days: Annotated[
        int,
        Field(
            ge=1,
        ),
    ]

    examples: list[str] = Field(
        default_factory=list,
    )


# =============================================================================
# Data Retention
# =============================================================================


class DataRetentionPolicy(BaseModel):
    """
    Defines how long data is retained.
    """

    model_config = ConfigDict(extra="forbid")

    applies_to: str = Field(
        description="Dataset or record type.",
    )

    retention_days: Annotated[
        int,
        Field(
            ge=1,
        ),
    ]

    automatic_deletion: bool = True

    legal_hold_supported: bool = False

    archive_before_deletion: bool = False

    justification: str


# =============================================================================
# Secure Storage
# =============================================================================


class SecureStorageStrategy(BaseModel):
    """
    Describes how application data is stored securely.
    """

    model_config = ConfigDict(extra="forbid")

    primary_storage: str = Field(
        description="Primary storage technology.",
        examples=[
            "PostgreSQL",
            "S3",
            "MongoDB",
        ],
    )

    encrypted_storage: bool = True

    versioning_enabled: bool = False

    immutable_backups: bool = False

    backup_frequency: str = Field(
        description="Daily, hourly, weekly, etc.",
    )

    disaster_recovery_plan: str

    notes: str | None = None

# =============================================================================
# Threat Modeling
# =============================================================================


class AttackSurface(BaseModel):
    """
    Represents an exposed surface that could be attacked.
    """

    model_config = ConfigDict(extra="forbid")

    name: str

    description: str

    exposed_to_public: bool = True

    technologies: list[str] = Field(
        default_factory=list,
        description="Technologies exposed through this surface.",
    )

    notes: str | None = None


class Threat(BaseModel):
    """
    Represents a single security threat.
    """

    model_config = ConfigDict(extra="forbid")

    identifier: str = Field(
        description="Unique threat identifier.",
        examples=["T001", "AUTH-01"],
    )

    title: str

    description: str

    affected_components: list[str] = Field(
        default_factory=list,
    )

    attack_surface: str

    likelihood: RiskLikelihood

    severity: RiskSeverity

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    recommended_controls: list[str] = Field(
        default_factory=list,
    )

    residual_risk: str | None = None


class ThreatScenario(BaseModel):
    """
    Describes how an attacker could exploit the system.
    """

    model_config = ConfigDict(extra="forbid")

    title: str

    attacker: str = Field(
        description="Threat actor.",
        examples=[
            "Anonymous attacker",
            "Authenticated user",
            "Malicious administrator",
            "Compromised API",
        ],
    )

    entry_point: str

    attack_steps: list[str] = Field(
        default_factory=list,
    )

    business_impact: str

    mitigations: list[str] = Field(
        default_factory=list,
    )


class TrustBoundary(BaseModel):
    """
    Represents a trust boundary within the solution architecture.
    """

    model_config = ConfigDict(extra="forbid")

    name: str

    description: str

    source_zone: str

    destination_zone: str

    authentication_required: bool = True

    encryption_required: bool = True

    notes: str | None = None


class ThreatModel(BaseModel):
    """
    Complete threat model for the proposed system.
    """

    model_config = ConfigDict(extra="forbid")

    methodology: str = Field(
        default="STRIDE",
        description="Threat modeling methodology.",
    )

    attack_surfaces: list[AttackSurface] = Field(
        default_factory=list,
    )

    trust_boundaries: list[TrustBoundary] = Field(
        default_factory=list,
    )

    threats: list[Threat] = Field(
        default_factory=list,
    )

    scenarios: list[ThreatScenario] = Field(
        default_factory=list,
    )

    assumptions: list[str] = Field(
        default_factory=list,
    )

    summary: str

# =============================================================================
# Security Controls
# =============================================================================


class SecurityControl(BaseModel):
    """
    Represents a security control recommended for the solution.
    """

    model_config = ConfigDict(extra="forbid")

    identifier: str = Field(
        description="Unique control identifier.",
        examples=["SC-001", "AUTH-001"],
    )

    name: str

    description: str

    objective: str = Field(
        description="What risk this control mitigates.",
    )

    implementation_guidance: list[str] = Field(
        default_factory=list,
        description="Concrete implementation recommendations.",
    )

    mitigated_threats: list[str] = Field(
        default_factory=list,
        description="Threat identifiers mitigated by this control.",
    )

    priority: RiskSeverity

    automated: bool = False

    owner: str = Field(
        description="Responsible team or role.",
        examples=[
            "Backend Team",
            "DevOps",
            "Platform Team",
            "Security Team",
        ],
    )

    notes: str | None = None


class SecurityRequirement(BaseModel):
    """
    Functional or non-functional security requirement.
    """

    model_config = ConfigDict(extra="forbid")

    identifier: str

    title: str

    description: str

    rationale: str

    mandatory: bool = True

    related_controls: list[str] = Field(
        default_factory=list,
    )

    related_components: list[str] = Field(
        default_factory=list,
    )


class SecurityValidation(BaseModel):
    """
    Validation activity proving that a control is effective.
    """

    model_config = ConfigDict(extra="forbid")

    control_identifier: str

    validation_method: str = Field(
        description="Pen test, code review, automated scan, etc.",
    )

    expected_result: str

    automation_possible: bool = True

    validation_frequency: str = Field(
        description="Per deployment, weekly, quarterly, etc.",
    )

    owner: str

    notes: str | None = None


class AuditRequirement(BaseModel):
    """
    Audit and traceability requirements.
    """

    model_config = ConfigDict(extra="forbid")

    identifier: str

    description: str

    audit_events: list[str] = Field(
        default_factory=list,
        description="Events that must be logged.",
    )

    retention_days: Annotated[
        int,
        Field(
            ge=1,
        ),
    ]

    immutable_storage: bool = False

    searchable: bool = True

    notes: str | None = None


class ComplianceRequirement(BaseModel):
    """
    Regulatory or organizational compliance requirement.
    """

    model_config = ConfigDict(extra="forbid")

    framework: str = Field(
        description="Compliance framework.",
        examples=[
            "GDPR",
            "SOC2",
            "ISO 27001",
            "HIPAA",
            "PCI DSS",
        ],
    )

    applicable: bool = True

    mandatory_controls: list[str] = Field(
        default_factory=list,
    )

    implementation_notes: list[str] = Field(
        default_factory=list,
    )

    evidence_required: list[str] = Field(
        default_factory=list,
    )

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

# =============================================================================
# Security Risks
# =============================================================================


class SecurityRisk(BaseModel):
    """
    Represents a remaining security risk after applying controls.
    """

    model_config = ConfigDict(extra="forbid")

    identifier: str = Field(
        description="Unique security risk identifier.",
    )

    title: str

    description: str

    severity: RiskSeverity

    likelihood: RiskLikelihood

    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    mitigation: str

    accepted: bool = False

    owner: str

    notes: str | None = None


# =============================================================================
# Incident Response
# =============================================================================


class IncidentResponsePlan(BaseModel):
    """
    High-level incident response recommendations.
    """

    model_config = ConfigDict(extra="forbid")

    monitoring_strategy: str

    alerting_strategy: str

    incident_detection: list[str] = Field(
        default_factory=list,
    )

    containment_steps: list[str] = Field(
        default_factory=list,
    )

    recovery_steps: list[str] = Field(
        default_factory=list,
    )

    post_incident_actions: list[str] = Field(
        default_factory=list,
    )

    owner: str

    notes: str | None = None


# =============================================================================
# Security Cost Estimate
# =============================================================================


class SecurityCostEstimate(BaseModel):
    """
    Estimated implementation cost for security recommendations.
    """

    model_config = ConfigDict(extra="forbid")

    category: CostCategory = CostCategory.SECURITY

    item: str

    estimated_cost: float = Field(
        ge=0,
    )

    frequency: CostFrequency

    justification: str

    optional: bool = False


# =============================================================================
# Root Security Architecture
# =============================================================================


class SecurityArchitecture(BaseModel):
    """
    Complete security architecture produced by the Security Architect.
    """

    model_config = ConfigDict(extra="forbid")

    executive_summary: str

    identity: IdentityArchitecture

    secrets: SecretManagementStrategy

    encryption: EncryptionStrategy

    pii_strategy: PIIHandlingStrategy

    data_classifications: list[DataClassification] = Field(
        default_factory=list,
    )

    retention_policies: list[DataRetentionPolicy] = Field(
        default_factory=list,
    )

    storage_strategy: SecureStorageStrategy

    threat_model: ThreatModel

    controls: list[SecurityControl] = Field(
        default_factory=list,
    )

    security_requirements: list[SecurityRequirement] = Field(
        default_factory=list,
    )

    validations: list[SecurityValidation] = Field(
        default_factory=list,
    )

    audit_requirements: list[AuditRequirement] = Field(
        default_factory=list,
    )

    compliance: list[ComplianceRequirement] = Field(
        default_factory=list,
    )

    residual_risks: list[SecurityRisk] = Field(
        default_factory=list,
    )

    incident_response: IncidentResponsePlan

    estimated_costs: list[SecurityCostEstimate] = Field(
        default_factory=list,
    )

    implementation_phases: list[str] = Field(
        default_factory=list,
    )

    assumptions: list[str] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        default_factory=list,
    )

    overall_security_posture: ConfidenceLevel = ConfidenceLevel.MEDIUM

    notes: str | None = None

