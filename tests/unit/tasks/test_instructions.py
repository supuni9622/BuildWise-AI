"""Regression guard: every UUID-identifier-producing task states the rules.

Only ``product_definition.py`` originally spelled out RFC 4122 identifier
rules. Every other task that generates UUID-typed fields lacked them, and
in a live run the Market & GTM task's LLM output used human-readable slugs
('seg-startup-founders', 'comp-chatprd') instead of UUIDs for every
identifier — a 138-error ValidationError that occurs while parsing the raw
LLM response, before any TaskOutput exists, so it bypasses the guardrail
retry-with-feedback loop entirely (the same failure shape as the original
crash, just triggered by field type instead of a business-rule validator).
There is no way to loosen a UUID field's type without losing cross-reference
integrity, so stating the rule firmly in every task is the only available
lever — these tests exist so a future edit can't silently drop it from one
task's description.
"""

from __future__ import annotations

from pydantic import SecretStr

from buildwise.agents.factory import AgentFactory
from buildwise.config.settings import Settings
from buildwise.domain.enums import AgentType
from buildwise.tasks.ai_architecture import create_ai_architecture_task
from buildwise.tasks.instructions import IDENTIFIER_RULES
from buildwise.tasks.market_and_gtm import create_market_and_gtm_task
from buildwise.tasks.product_definition import create_product_definition_task
from buildwise.tasks.requirements import create_requirements_task
from buildwise.tasks.solution_architecture import create_solution_architecture_task
from fixtures.planning import build_product_planning_inputs


def _offline_agent(agent_type: AgentType):
    settings = Settings(openai_api_key=SecretStr("sk-test-not-a-real-key"))
    return AgentFactory(settings=settings).create(agent_type)


def test_product_definition_task_states_identifier_rules() -> None:
    discovery, _planning = build_product_planning_inputs()
    task = create_product_definition_task(
        agent=_offline_agent(AgentType.PRODUCT_MANAGER),
        discovery_result=discovery,
    )

    assert IDENTIFIER_RULES in task.description


def test_requirements_task_states_identifier_rules() -> None:
    _discovery, planning = build_product_planning_inputs()
    task = create_requirements_task(
        agent=_offline_agent(AgentType.BUSINESS_ANALYST),
        product_definition=planning.product_definition,
    )

    assert IDENTIFIER_RULES in task.description


def test_market_and_gtm_task_states_identifier_rules() -> None:
    """The task that actually failed live with non-UUID identifiers."""

    _discovery, planning = build_product_planning_inputs()
    task = create_market_and_gtm_task(
        agent=_offline_agent(AgentType.MARKET_AND_GTM_STRATEGIST),
        product_definition=planning.product_definition,
        requirements=planning.requirements,
    )

    assert IDENTIFIER_RULES in task.description


def test_solution_architecture_task_states_identifier_rules() -> None:
    _discovery, planning = build_product_planning_inputs()
    task = create_solution_architecture_task(
        agent=_offline_agent(AgentType.SOLUTION_ARCHITECT),
        requirements=planning.requirements,
    )

    assert IDENTIFIER_RULES in task.description


def test_ai_architecture_task_states_identifier_rules() -> None:
    from buildwise.domain.architecture import SolutionArchitecture

    _discovery, planning = build_product_planning_inputs()
    solution = SolutionArchitecture.model_construct(
        id=planning.requirements.id,
        session_id=planning.requirements.session_id,
        requirements_specification_id=planning.requirements.id,
        architecture_style="microservices",
        architecture_style_rationale="scales independently",
        components=[],
        connections=[],
        deployment_units=[],
        data_architecture_summary="s",
        integration_architecture_summary="s",
        deployment_summary="s",
        operational_summary="s",
    )
    task = create_ai_architecture_task(
        agent=_offline_agent(AgentType.AI_ARCHITECT),
        requirements=planning.requirements,
        solution_architecture=solution,
    )

    assert IDENTIFIER_RULES in task.description
