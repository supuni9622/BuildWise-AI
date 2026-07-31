"""BuildWise v2 Task factories — thin wrappers around native ``crewai.Task``."""

from buildwisev2.tasks.ai_architecture import create_ai_architecture_task
from buildwisev2.tasks.discovery import create_discovery_task
from buildwisev2.tasks.guardrails import compose_guardrails, require_pydantic_output
from buildwisev2.tasks.lead_review import create_lead_review_task
from buildwisev2.tasks.market_and_gtm import create_market_and_gtm_task
from buildwisev2.tasks.product_definition import create_product_definition_task
from buildwisev2.tasks.qa_evaluation import create_qa_evaluation_task
from buildwisev2.tasks.requirements import create_requirements_task
from buildwisev2.tasks.security_architecture import create_security_architecture_task
from buildwisev2.tasks.solution_architecture import create_solution_architecture_task

__all__ = [
    "compose_guardrails",
    "create_ai_architecture_task",
    "create_discovery_task",
    "create_lead_review_task",
    "create_market_and_gtm_task",
    "create_product_definition_task",
    "create_qa_evaluation_task",
    "create_requirements_task",
    "create_security_architecture_task",
    "create_solution_architecture_task",
    "require_pydantic_output",
]
