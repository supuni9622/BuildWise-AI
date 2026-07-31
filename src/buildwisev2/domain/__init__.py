"""BuildWise v2 domain models — framework-independent Pydantic artifacts."""

from buildwisev2.domain.ai_architecture import AIArchitecture, AIArchitectureDecision
from buildwisev2.domain.architecture import SolutionArchitecture, SolutionArchitectureDecision
from buildwisev2.domain.blueprint import BlueprintSection, ProductBlueprint
from buildwisev2.domain.common import (
    BuildWiseModel,
    CapabilityType,
    FlowRuntimeLimits,
    SpecialistType,
)
from buildwisev2.domain.discovery import DiscoveryDecision, DiscoveryResult
from buildwisev2.domain.intake import ClarificationAnswer, ProductIdeaContext, ProductIdeaRequest
from buildwisev2.domain.market_and_gtm import MarketAndGTMDecision, MarketAndGTMStrategy
from buildwisev2.domain.planning_results import ProductPlanningResult, TechnicalPlanningResult
from buildwisev2.domain.product import ProductDefinition, ProductDefinitionDecision
from buildwisev2.domain.qa import QAEvaluationDecision, QAEvaluationPlan
from buildwisev2.domain.requirements import RequirementsDecision, RequirementsSpecification
from buildwisev2.domain.review import LeadReview, ReviewDecision, RevisionRequest, RevisionTarget
from buildwisev2.domain.security_architecture import (
    SecurityArchitecture,
    SecurityArchitectureDecision,
)
from buildwisev2.domain.specialist_planning import (
    BudgetDecision,
    BudgetDecisionType,
    DependencyType,
    EffortLevel,
    ExecutionMode,
    SpecialistDependency,
    SpecialistExecutionGroup,
    SpecialistExecutionPlan,
    SpecialistRecommendation,
    SpecialistSelectionReason,
)

__all__ = [
    "AIArchitecture",
    "AIArchitectureDecision",
    "BlueprintSection",
    "BudgetDecision",
    "BudgetDecisionType",
    "BuildWiseModel",
    "CapabilityType",
    "ClarificationAnswer",
    "DependencyType",
    "DiscoveryDecision",
    "DiscoveryResult",
    "EffortLevel",
    "ExecutionMode",
    "FlowRuntimeLimits",
    "LeadReview",
    "MarketAndGTMDecision",
    "MarketAndGTMStrategy",
    "ProductBlueprint",
    "ProductDefinition",
    "ProductDefinitionDecision",
    "ProductIdeaContext",
    "ProductIdeaRequest",
    "ProductPlanningResult",
    "QAEvaluationDecision",
    "QAEvaluationPlan",
    "RequirementsDecision",
    "RequirementsSpecification",
    "ReviewDecision",
    "RevisionRequest",
    "RevisionTarget",
    "SecurityArchitecture",
    "SecurityArchitectureDecision",
    "SolutionArchitecture",
    "SolutionArchitectureDecision",
    "SpecialistDependency",
    "SpecialistExecutionGroup",
    "SpecialistExecutionPlan",
    "SpecialistRecommendation",
    "SpecialistSelectionReason",
    "SpecialistType",
    "TechnicalPlanningResult",
]
