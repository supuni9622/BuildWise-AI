"""CrewAI crew definitions."""

from buildwise.crews.ai_architecture import create_ai_architecture_crew
from buildwise.crews.discovery import create_discovery_crew
from buildwise.crews.lead_review import create_lead_review_crew
from buildwise.crews.market_and_gtm import create_market_and_gtm_crew
from buildwise.crews.product_definition import create_product_definition_crew
from buildwise.crews.qa_evaluation import create_qa_evaluation_crew
from buildwise.crews.registry import CREW_REGISTRY, CrewKey, CrewRegistry
from buildwise.crews.requirements import create_requirements_crew
from buildwise.crews.security_architecture import create_security_architecture_crew
from buildwise.crews.solution_architecture import create_solution_architecture_crew

__all__ = [
    "CREW_REGISTRY",
    "CrewKey",
    "CrewRegistry",
    "create_ai_architecture_crew",
    "create_discovery_crew",
    "create_lead_review_crew",
    "create_market_and_gtm_crew",
    "create_product_definition_crew",
    "create_qa_evaluation_crew",
    "create_requirements_crew",
    "create_security_architecture_crew",
    "create_solution_architecture_crew",
]
