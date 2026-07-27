"""Deterministic assembly of the final BuildWise product blueprint."""

from __future__ import annotations

from collections.abc import Iterable

from buildwise.domain.blueprint import (
    BlueprintSection,
    ProductBlueprint,
)
from buildwise.domain.blueprint import (
    UsageSummary as BlueprintUsageSummary,
)
from buildwise.domain.costs import CostSummary, ProjectCostEstimate
from buildwise.domain.discovery import DiscoveryResult
from buildwise.domain.enums import BlueprintSectionType, SpecialistType
from buildwise.domain.product import ProductFeature, ProductRoadmapItem
from buildwise.domain.product_planning import ProductPlanningResult
from buildwise.domain.requirements import RequirementsSpecification, UserJourney
from buildwise.domain.review import LeadReview
from buildwise.domain.specialist_planning import SpecialistExecutionPlan
from buildwise.domain.technical_planning import TechnicalPlanningResult
from buildwise.domain.usage import UsageSummary
from buildwise.reporting.markdown_renderer import render_blueprint_markdown


def assemble_blueprint(
    *,
    discovery: DiscoveryResult,
    product_planning: ProductPlanningResult,
    specialist_plan: SpecialistExecutionPlan,
    technical_planning: TechnicalPlanningResult,
    cost_summary: CostSummary,
    lead_review: LeadReview,
    usage_summary: UsageSummary,
) -> ProductBlueprint:
    """Assemble approved typed artifacts into a deterministic blueprint."""

    product = product_planning.product_definition
    requirements = product_planning.requirements
    solution = technical_planning.solution_architecture
    market = product_planning.market_and_gtm
    ai = technical_planning.ai_architecture
    security = technical_planning.security_architecture
    qa = technical_planning.qa_evaluation
    selected_specialists = {
        recommendation.specialist
        for recommendation in specialist_plan.recommendations
    }
    unavailable_specialist_limitations = [
        (
            f"{specialist.value} was selected but its analysis was unavailable; "
            "the blueprint continued with this limitation."
        )
        for specialist, artifact in (
            (SpecialistType.AI_ARCHITECTURE, ai),
            (SpecialistType.SECURITY_ARCHITECTURE, security),
            (SpecialistType.QA_AND_EVALUATION, qa),
        )
        if artifact is None and specialist in selected_specialists
    ]

    assumptions = _unique(
        [
            *(item.statement for item in discovery.assumptions),
            *product.assumptions,
            *requirements.assumptions,
            *solution.assumptions,
            *(ai.assumptions if ai else []),
            *(security.assumptions if security else []),
            *(qa.assumptions if qa else []),
            *lead_review.assumptions,
        ]
    )
    open_questions = _unique(
        [
            *(item.description for item in discovery.unknowns),
            *product.open_questions,
            *requirements.open_questions,
            *(market.open_questions if market else []),
            *solution.open_questions,
            *(ai.open_questions if ai else []),
            *lead_review.missing_items,
        ]
    )
    limitations = _unique(
        [
            *discovery.limitations,
            *product.limitations,
            *requirements.limitations,
            *(market.limitations if market else ["Market research was omitted."]),
            *solution.limitations,
            *(ai.limitations if ai else []),
            *lead_review.limitations,
            *unavailable_specialist_limitations,
        ]
    )
    risks = _unique(
        [
            *(risk.title for risk in discovery.risks),
            *(risk.title for risk in product.risks),
            *(risk.title for risk in (market.risks if market else [])),
            *(risk.title for risk in solution.risks),
            *(risk.title for risk in (ai.risks if ai else [])),
            *(risk.title for risk in (security.residual_risks if security else [])),
            *(risk.title for risk in (qa.quality_risks if qa else [])),
        ]
    )
    phases = _unique(
        [
            *(item.title for item in product.roadmap),
            *(security.implementation_phases if security else []),
            *(qa.implementation_phases if qa else []),
        ]
    )

    sections = [
        _section(
            BlueprintSectionType.EXECUTIVE_SUMMARY,
            "Executive Summary",
            lead_review.executive_summary,
            lead_review.executive_summary,
        ),
        _section(
            BlueprintSectionType.PRODUCT_VISION,
            "Product Vision",
            product.vision,
            _paragraphs(
                ("Vision", product.vision),
                ("Problem", product.problem_statement),
                ("Value proposition", product.value_proposition),
            ),
        ),
        _section(
            BlueprintSectionType.USERS_AND_PERSONAS,
            "Users and Personas",
            product.personas[0].description,
            _named_items(product.personas, "name", "description"),
        ),
        _section(
            BlueprintSectionType.FEATURES_AND_SCOPE,
            "Features and MVP Scope",
            f"{len(product.mvp_feature_ids)} features are included in the MVP.",
            _feature_markdown(product.features),
        ),
        _section(
            BlueprintSectionType.REQUIREMENTS,
            "Requirements",
            requirements.summary,
            _requirements_markdown(requirements),
        ),
        _section(
            BlueprintSectionType.USER_JOURNEYS,
            "User Journeys",
            f"{len(requirements.user_journeys)} user journeys define expected behavior.",
            _journeys_markdown(requirements.user_journeys),
        ),
        _section(
            BlueprintSectionType.MARKET_AND_GTM,
            "Market and GTM",
            market.executive_summary if market else "Market and GTM was not selected.",
            (
                _paragraphs(
                    ("Market", market.market_problem_summary),
                    ("Positioning", market.positioning.positioning_statement),
                    ("Launch strategy", market.launch_strategy),
                )
                if market
                else "Market and GTM analysis was not selected for this consultation."
            ),
        ),
        _section(
            BlueprintSectionType.SOLUTION_ARCHITECTURE,
            "Solution Architecture",
            solution.executive_summary,
            _paragraphs(
                ("Architecture style", str(solution.architecture_style)),
                ("Rationale", solution.architecture_style_rationale),
                ("Components", _names(solution.components)),
                ("Technology choices", _names(solution.technology_choices)),
                ("Deployment", solution.deployment_summary),
            ),
        ),
        _section(
            BlueprintSectionType.AI_ARCHITECTURE,
            "AI Architecture",
            (
                ai.executive_summary
                if ai
                else _optional_specialist_summary(
                    BlueprintSectionType.AI_ARCHITECTURE,
                    selected_specialists,
                )
            ),
            (
                _paragraphs(
                    ("Strategy", str(ai.model_strategy)),
                    ("Rationale", ai.model_strategy_rationale),
                    ("Capabilities", _names(ai.capabilities)),
                    ("Human oversight", ai.human_oversight_strategy),
                    ("Fallback", ai.fallback_strategy),
                )
                if ai
                else _optional_specialist_summary(
                    BlueprintSectionType.AI_ARCHITECTURE,
                    selected_specialists,
                )
            ),
        ),
        _section(
            BlueprintSectionType.SECURITY_ARCHITECTURE,
            "Security Architecture",
            (
                security.executive_summary
                if security
                else _optional_specialist_summary(
                    BlueprintSectionType.SECURITY_ARCHITECTURE,
                    selected_specialists,
                )
            ),
            (
                _paragraphs(
                    ("Summary", security.executive_summary),
                    ("Controls", _names(security.controls)),
                    ("Recommendations", _bullets(security.recommendations)),
                )
                if security
                else _optional_specialist_summary(
                    BlueprintSectionType.SECURITY_ARCHITECTURE,
                    selected_specialists,
                )
            ),
        ),
        _section(
            BlueprintSectionType.QA_AND_EVALUATION,
            "QA and Evaluation",
            (
                qa.executive_summary
                if qa
                else _optional_specialist_summary(
                    BlueprintSectionType.QA_AND_EVALUATION,
                    selected_specialists,
                )
            ),
            (
                _paragraphs(
                    ("Summary", qa.executive_summary),
                    ("Test suites", _names(qa.test_suites)),
                    ("Release gates", _names(qa.release_gates)),
                    ("Recommendations", _bullets(qa.recommendations)),
                )
                if qa
                else _optional_specialist_summary(
                    BlueprintSectionType.QA_AND_EVALUATION,
                    selected_specialists,
                )
            ),
        ),
        _section(
            BlueprintSectionType.ROADMAP,
            "Roadmap",
            f"{len(product.roadmap)} roadmap items sequence delivery.",
            _roadmap_markdown(product.roadmap),
        ),
        _section(
            BlueprintSectionType.COSTS,
            "Costs",
            "Cost estimates are directional and should be validated before commitment.",
            _cost_markdown(cost_summary, usage_summary),
        ),
        _section(
            BlueprintSectionType.RISKS_AND_ASSUMPTIONS,
            "Risks and Assumptions",
            f"{len(risks)} risks and {len(assumptions)} assumptions are recorded.",
            _paragraphs(("Risks", _bullets(risks)), ("Assumptions", _bullets(assumptions))),
        ),
        _section(
            BlueprintSectionType.OPEN_QUESTIONS,
            "Open Questions",
            f"{len(open_questions)} unresolved decisions remain.",
            _bullets(open_questions),
        ),
        _section(
            BlueprintSectionType.IMPLEMENTATION_GUIDANCE,
            "Implementation Guidance",
            lead_review.recommendations[0] if lead_review.recommendations else product.vision,
            _paragraphs(
                ("Execution plan", specialist_plan.execution_summary),
                ("Recommendations", _bullets(lead_review.recommendations)),
                ("Implementation phases", _bullets(phases)),
            ),
        ),
        _section(
            BlueprintSectionType.LIMITATIONS,
            "Limitations",
            f"{len(limitations)} constraints qualify this blueprint.",
            _bullets(limitations),
        ),
    ]

    usage = BlueprintUsageSummary(
        total_agents=usage_summary.agent_execution_count,
        total_llm_calls=usage_summary.request_count,
        prompt_tokens=usage_summary.input_tokens,
        completion_tokens=usage_summary.output_tokens,
        total_tokens=usage_summary.total_tokens,
        estimated_cost=usage_summary.estimated_cost_usd,
        execution_time_seconds=usage_summary.execution_duration_ms / 1000,
        model_usage=_model_usage(usage_summary),
    )
    blueprint = ProductBlueprint(
        title=f"{product.product_name} — Product Blueprint",
        executive_summary=lead_review.executive_summary,
        sections=sections,
        implementation_phases=phases,
        assumptions=assumptions,
        risks=risks,
        recommendations=_unique(lead_review.recommendations),
        open_questions=open_questions,
        limitations=limitations,
        usage_summary=usage,
        generated_markdown="",
    )
    return blueprint.model_copy(update={"generated_markdown": render_blueprint_markdown(blueprint)})


class BlueprintAssembler:
    """Injectable deterministic blueprint builder."""

    assemble = staticmethod(assemble_blueprint)

    def build(
        self,
        *,
        discovery: DiscoveryResult,
        product_planning: ProductPlanningResult,
        specialist_plan: SpecialistExecutionPlan,
        technical_planning: TechnicalPlanningResult,
        cost_summary: CostSummary,
        lead_review: LeadReview,
        usage_summary: UsageSummary | None = None,
    ) -> ProductBlueprint:
        return assemble_blueprint(
            discovery=discovery,
            product_planning=product_planning,
            specialist_plan=specialist_plan,
            technical_planning=technical_planning,
            cost_summary=cost_summary,
            lead_review=lead_review,
            usage_summary=usage_summary or UsageSummary(),
        )


def _section(
    section: BlueprintSectionType,
    title: str,
    summary: str,
    body: str,
) -> BlueprintSection:
    return BlueprintSection(
        section=section,
        title=title,
        summary=summary,
        markdown=(
            f"## {title}\n\n_{summary}_\n\n{body or '_None recorded._'}"
        ),
    )


def _optional_specialist_summary(
    section: BlueprintSectionType,
    selected_specialists: set[SpecialistType],
) -> str:
    label = {
        BlueprintSectionType.AI_ARCHITECTURE: "AI Architecture",
        BlueprintSectionType.SECURITY_ARCHITECTURE: "Security Architecture",
        BlueprintSectionType.QA_AND_EVALUATION: "QA and Evaluation",
    }[section]
    if section.value in {selected.value for selected in selected_specialists}:
        return (
            f"{label} was selected but its analysis was unavailable. "
            "The blueprint continued with an explicit limitation."
        )
    return f"{label} was not selected for this consultation."


def _paragraphs(*items: tuple[str, str]) -> str:
    return "\n\n".join(f"### {title}\n\n{body}" for title, body in items if body)


def _bullets(items: Iterable[object]) -> str:
    values = [str(item) for item in items if str(item).strip()]
    return "\n".join(f"- {item}" for item in values) if values else "_None recorded._"


def _names(items: Iterable[object]) -> str:
    return _bullets(
        getattr(item, "name", getattr(item, "title", getattr(item, "key", str(item))))
        for item in items
    )


def _named_items(items: Iterable[object], name: str, description: str) -> str:
    return "\n".join(f"### {getattr(item, name)}\n\n{getattr(item, description)}" for item in items)


def _feature_markdown(features: Iterable[ProductFeature]) -> str:
    return "\n".join(
        f"- **{item.name}** ({'MVP' if item.included_in_mvp else 'Later'}): {item.description}"
        for item in features
    )


def _requirements_markdown(requirements: RequirementsSpecification) -> str:
    functional = requirements.functional_requirements
    non_functional = requirements.non_functional_requirements
    return _paragraphs(
        ("Functional requirements", _named_items(functional, "title", "description")),
        ("Non-functional requirements", _named_items(non_functional, "title", "description")),
    )


def _journeys_markdown(journeys: Iterable[UserJourney]) -> str:
    return "\n\n".join(
        _paragraphs(
            (journey.name, journey.description),
            ("Steps", _bullets(f"{step.sequence}. {step.title}" for step in journey.steps)),
            ("Expected outcome", journey.expected_outcome),
        )
        for journey in journeys
    )


def _roadmap_markdown(items: Iterable[ProductRoadmapItem]) -> str:
    return "\n".join(
        f"- **{item.title}** ({item.horizon}): {item.outcome}"
        + (f" — {item.estimated_duration}" if item.estimated_duration else "")
        for item in items
    )


def _cost_markdown(
    cost_summary: CostSummary,
    usage: UsageSummary,
) -> str:
    lines = [_format_project_cost(item) for item in cost_summary.estimates]
    if cost_summary.totals:
        lines.extend(["", "### Totals by currency and frequency"])
        lines.extend(
            (
                f"- {total.currency} {total.frequency.value}: "
                f"{total.minimum:,.2f}-{total.maximum:,.2f} "
                f"(expected {total.expected:,.2f}; "
                f"{total.estimate_count} estimates)"
            )
            for total in cost_summary.totals
        )
    if usage.estimated_cost_usd is None:
        lines.extend(["", "- BuildWise LLM execution: cost unavailable"])
    else:
        lines.extend(["", f"- BuildWise LLM execution: ${usage.estimated_cost_usd:,.2f}"])
    return "\n".join(lines)


def _model_usage(usage: UsageSummary) -> dict[str, int]:
    result: dict[str, int] = {}
    for record in usage.records:
        if record.model:
            result[record.model] = result.get(record.model, 0) + 1
    return result


def _format_project_cost(item: ProjectCostEstimate) -> str:
    optional = "; optional" if item.optional else ""
    return (
        f"- **{item.name}** [{item.source.value}]: "
        f"{item.currency} {item.minimum:,.2f}-{item.maximum:,.2f} "
        f"(expected {item.expected:,.2f}; {item.frequency.value}{optional})"
    )


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value.strip()))
