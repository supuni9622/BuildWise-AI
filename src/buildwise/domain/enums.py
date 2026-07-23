from enum import StrEnum


class SessionStatus(StrEnum):
    """Overall lifecycle status of a BuildWise consulting session."""

    CREATED = "created"
    PROCESSING = "processing"
    AWAITING_USER_INPUT = "awaiting_user_input"
    RESUMING = "resuming"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    COMPLETED_WITH_LIMITATIONS = "completed_with_limitations"
    FAILED = "failed"


class SessionStage(StrEnum):
    """Current orchestration stage within the BuildWise consulting workflow."""

    INTAKE = "intake"
    DISCOVERY = "discovery"
    CLARIFICATION = "clarification"
    CAPABILITY_CLASSIFICATION = "capability_classification"
    PRODUCT_DEFINITION = "product_definition"
    REQUIREMENTS = "requirements"
    SPECIALIST_PLANNING = "specialist_planning"
    SPECIALIST_EXECUTION = "specialist_execution"
    COST_AGGREGATION = "cost_aggregation"
    LEAD_REVIEW = "lead_review"
    REFINEMENT = "refinement"
    BLUEPRINT_ASSEMBLY = "blueprint_assembly"
    COMPLETED = "completed"
    FAILED = "failed"


class FactSourceType(StrEnum):
    """Origin of a known fact or supporting reference."""

    USER_PROVIDED = "user_provided"
    CLARIFICATION_ANSWER = "clarification_answer"
    DERIVED = "derived"
    EXTERNAL_RESEARCH = "external_research"
    SPECIALIST_OUTPUT = "specialist_output"
    SYSTEM_GENERATED = "system_generated"


class ConfidenceLevel(StrEnum):
    """Normalized confidence level used across domain outputs."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskSeverity(StrEnum):
    """Business or technical impact of a risk."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLikelihood(StrEnum):
    """Estimated probability that a risk will occur."""

    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    ALMOST_CERTAIN = "almost_certain"


class RequirementPriority(StrEnum):
    """Priority assigned to requirements, features, and roadmap items."""

    MUST_HAVE = "must_have"
    SHOULD_HAVE = "should_have"
    COULD_HAVE = "could_have"
    WONT_HAVE = "wont_have"


class RequirementStatus(StrEnum):
    """Lifecycle state of a requirement."""

    PROPOSED = "proposed"
    VALIDATED = "validated"
    DEFERRED = "deferred"
    REJECTED = "rejected"


class FeatureCategory(StrEnum):
    """High-level product feature grouping."""

    CORE = "core"
    SUPPORTING = "supporting"
    ADMINISTRATION = "administration"
    ANALYTICS = "analytics"
    INTEGRATION = "integration"
    SECURITY = "security"
    AI = "ai"


class RoadmapHorizon(StrEnum):
    """Delivery horizon used by product roadmap items."""

    MVP = "mvp"
    NEAR_TERM = "near_term"
    MID_TERM = "mid_term"
    LONG_TERM = "long_term"


class SpecialistType(StrEnum):
    """Canonical conditional specialist roles supported by BuildWise."""

    MARKET_AND_GTM = "market_and_gtm"
    SOLUTION_ARCHITECTURE = "solution_architecture"
    AI_ARCHITECTURE = "ai_architecture"
    SECURITY_ARCHITECTURE = "security_architecture"
    QA_AND_EVALUATION = "qa_and_evaluation"


class SpecialistSelectionReason(StrEnum):
    """Primary reason a specialist is selected for a consultation."""

    ALWAYS_REQUIRED = "always_required"
    PRODUCT_COMPLEXITY = "product_complexity"
    AI_CAPABILITY_REQUIRED = "ai_capability_required"
    SENSITIVE_DATA = "sensitive_data"
    REGULATED_DOMAIN = "regulated_domain"
    EXTERNAL_INTEGRATIONS = "external_integrations"
    HIGH_RISK = "high_risk"
    EXPLICIT_USER_REQUEST = "explicit_user_request"


class ExecutionMode(StrEnum):
    """Execution strategy for a specialist group."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class DependencyType(StrEnum):
    """Relationship between two specialist executions."""

    REQUIRES_OUTPUT = "requires_output"
    REQUIRES_APPROVAL = "requires_approval"
    PROVIDES_CONTEXT = "provides_context"


class BudgetDecisionType(StrEnum):
    """Decision made by the budget controller."""

    APPROVED = "approved"
    APPROVED_WITH_LIMITS = "approved_with_limits"
    DEFERRED = "deferred"
    REJECTED = "rejected"


class CapabilityType(StrEnum):
    """Product capability categories detected during discovery."""

    STANDARD_SOFTWARE = "standard_software"
    AI_ASSISTED = "ai_assisted"
    AI_CORE = "ai_core"
    RAG = "rag"
    AGENTIC_WORKFLOW = "agentic_workflow"
    AUTOMATION = "automation"
    MARKETPLACE = "marketplace"
    ANALYTICS = "analytics"
    REAL_TIME = "real_time"
    INTEGRATION_HEAVY = "integration_heavy"
    SENSITIVE_DATA = "sensitive_data"
    REGULATED = "regulated"


class AIUseCaseType(StrEnum):
    """Canonical AI capability patterns used in AI architecture."""

    GENERATION = "generation"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    SEARCH = "search"
    RECOMMENDATION = "recommendation"
    FORECASTING = "forecasting"
    RAG = "rag"
    AGENTIC_AUTOMATION = "agentic_automation"
    CONVERSATIONAL_ASSISTANT = "conversational_assistant"


class ModelStrategyType(StrEnum):
    """High-level model deployment strategy."""

    SINGLE_MODEL = "single_model"
    MODEL_ROUTING = "model_routing"
    MULTI_PROVIDER = "multi_provider"
    SELF_HOSTED = "self_hosted"
    HYBRID = "hybrid"


class ArchitectureComponentType(StrEnum):
    """Common solution architecture component categories."""

    CLIENT = "client"
    API = "api"
    APPLICATION_SERVICE = "application_service"
    DATABASE = "database"
    CACHE = "cache"
    MESSAGE_BROKER = "message_broker"
    OBJECT_STORAGE = "object_storage"
    SEARCH_ENGINE = "search_engine"
    VECTOR_DATABASE = "vector_database"
    IDENTITY_PROVIDER = "identity_provider"
    EXTERNAL_SERVICE = "external_service"
    AI_SERVICE = "ai_service"
    OBSERVABILITY = "observability"
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"


class CostCategory(StrEnum):
    """Categories used to distribute cost estimates across outputs."""

    PRODUCT = "product"
    ARCHITECTURE = "architecture"
    AI = "ai"
    SECURITY = "security"
    QA = "qa"
    GTM = "gtm"
    INFRASTRUCTURE = "infrastructure"
    OPERATIONS = "operations"
    EXTERNAL_SERVICES = "external_services"


class CostFrequency(StrEnum):
    """Frequency associated with a cost estimate."""

    ONE_TIME = "one_time"
    PER_REQUEST = "per_request"
    DAILY = "daily"
    MONTHLY = "monthly"
    ANNUALLY = "annually"


class ReviewDecision(StrEnum):
    """Outcome of the Lead Reviewer stage."""

    APPROVED = "approved"
    APPROVED_WITH_LIMITATIONS = "approved_with_limitations"
    REVISION_REQUIRED = "revision_required"
    REJECTED = "rejected"


class RevisionTarget(StrEnum):
    """BuildWise output area targeted by a bounded revision."""

    DISCOVERY = "discovery"
    PRODUCT_DEFINITION = "product_definition"
    REQUIREMENTS = "requirements"
    MARKET_AND_GTM = "market_and_gtm"
    SOLUTION_ARCHITECTURE = "solution_architecture"
    AI_ARCHITECTURE = "ai_architecture"
    SECURITY_ARCHITECTURE = "security_architecture"
    QA_AND_EVALUATION = "qa_and_evaluation"
    COST_SUMMARY = "cost_summary"
    BLUEPRINT = "blueprint"


class BlueprintSectionType(StrEnum):
    """Canonical sections in the final BuildWise blueprint."""

    EXECUTIVE_SUMMARY = "executive_summary"
    PRODUCT_VISION = "product_vision"
    USERS_AND_PERSONAS = "users_and_personas"
    FEATURES_AND_SCOPE = "features_and_scope"
    REQUIREMENTS = "requirements"
    USER_JOURNEYS = "user_journeys"
    MARKET_AND_GTM = "market_and_gtm"
    SOLUTION_ARCHITECTURE = "solution_architecture"
    AI_ARCHITECTURE = "ai_architecture"
    SECURITY_ARCHITECTURE = "security_architecture"
    QA_AND_EVALUATION = "qa_and_evaluation"
    ROADMAP = "roadmap"
    COSTS = "costs"
    RISKS_AND_ASSUMPTIONS = "risks_and_assumptions"
    IMPLEMENTATION_GUIDANCE = "implementation_guidance"
    LIMITATIONS = "limitations"


class SourceReferenceType(StrEnum):
    """Type of evidence cited in a blueprint or specialist report."""

    USER_INPUT = "user_input"
    CLARIFICATION = "clarification"
    EXTERNAL_SOURCE = "external_source"
    INTERNAL_ARTIFACT = "internal_artifact"
    AGENT_OUTPUT = "agent_output"


class ModelTier(StrEnum):
    """BuildWise model routing tiers used by agent contracts."""

    FAST = "fast"
    PRIMARY = "primary"
    ARCHITECT = "architect"
    LEAD_REVIEWER = "lead_reviewer"


class AgentFailureBehavior(StrEnum):
    """Expected behavior when an agent invocation fails."""

    FAIL_SESSION = "fail_session"
    RETRY_THEN_FAIL = "retry_then_fail"
    RETRY_THEN_FALLBACK = "retry_then_fallback"
    CONTINUE_WITH_LIMITATION = "continue_with_limitation"
    REQUEST_USER_INPUT = "request_user_input"


class AgentInvocationMode(StrEnum):
    """Whether an agent is always used or selected conditionally."""

    REQUIRED = "required"
    CONDITIONAL = "conditional"


class HandoffTarget(StrEnum):
    """Canonical downstream handoff targets for agent contracts."""

    DISCOVERY_FLOW = "discovery_flow"
    PRODUCT_CREW = "product_crew"
    SPECIALIST_PLANNER = "specialist_planner"
    MARKET_AND_GTM_SPECIALIST = "market_and_gtm_specialist"
    SOLUTION_ARCHITECT = "solution_architect"
    AI_ARCHITECT = "ai_architect"
    SECURITY_ARCHITECT = "security_architect"
    QA_AND_EVALUATION_ARCHITECT = "qa_and_evaluation_architect"
    LEAD_REVIEWER = "lead_reviewer"
    BLUEPRINT_ASSEMBLER = "blueprint_assembler"
    SESSION_COMPLETION = "session_completion"
