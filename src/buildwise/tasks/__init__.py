"""CrewAI task definitions."""

from buildwise.tasks.ai_architecture import create_ai_architecture_task
from buildwise.tasks.discovery import create_discovery_task
from buildwise.tasks.guardrails import (
    TaskGuardrail,
    compose_guardrails,
    require_artifact_session,
    require_non_empty_collections,
    require_pydantic_output,
    require_review_consistency,
    run_domain_validator,
)
from buildwise.tasks.lead_review import create_lead_review_task
from buildwise.tasks.market_and_gtm import create_market_and_gtm_task
from buildwise.tasks.product_definition import create_product_definition_task
from buildwise.tasks.qa_evaluation import create_qa_evaluation_task
from buildwise.tasks.requirements import create_requirements_task
from buildwise.tasks.revisions import format_revision_instructions
from buildwise.tasks.security_architecture import create_security_architecture_task
from buildwise.tasks.solution_architecture import create_solution_architecture_task

__all__ = [
    "TaskGuardrail",
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
    "format_revision_instructions",
    "require_artifact_session",
    "require_non_empty_collections",
    "require_pydantic_output",
    "require_review_consistency",
    "run_domain_validator",
]
