"""Deterministic blueprint assembly.

Consumes already-approved structured artifacts from Flow state and renders
a ``ProductBlueprint``. No LLM call happens here — this is a rendering
step, not a reasoning step, per ``06_consulting_flow_prd.md`` ("Deterministic
Blueprint Generator") and ``04_crews_refactor_plan.md`` section 19.
"""

from __future__ import annotations

from buildwisev2.domain.ai_architecture import AIArchitecture
from buildwisev2.domain.architecture import SolutionArchitecture
from buildwisev2.domain.blueprint import BlueprintSection, ProductBlueprint
from buildwisev2.domain.discovery import DiscoveryResult
from buildwisev2.domain.market_and_gtm import MarketAndGTMStrategy
from buildwisev2.domain.product import ProductDefinition
from buildwisev2.domain.qa import QAEvaluationPlan
from buildwisev2.domain.requirements import RequirementsSpecification
from buildwisev2.domain.review import LeadReview
from buildwisev2.domain.security_architecture import SecurityArchitecture
from buildwisev2.domain.specialist_planning import SpecialistExecutionPlan

_MAX_TITLE_LENGTH = 90


def _bullets(items: list[str]) -> str:
    if not items:
        return "- None recorded."
    return "\n".join(f"- {item}" for item in items)


def _derive_title(vision: str) -> str:
    """Derive a short blueprint title from the product vision's first sentence.

    Defensive against a vision that has no early sentence break (e.g. an
    agent that echoed a long, unpunctuated brief back verbatim instead of
    synthesizing a short vision statement) — always caps to a bounded,
    word-safe length rather than emitting the raw text as-is.
    """

    first_sentence = vision.split(".")[0].strip() or "Product Blueprint"
    if len(first_sentence) <= _MAX_TITLE_LENGTH:
        return first_sentence
    truncated = first_sentence[:_MAX_TITLE_LENGTH].rsplit(" ", 1)[0].rstrip()
    return f"{truncated}…"


def _render_discovery(discovery: DiscoveryResult) -> BlueprintSection:
    markdown = (
        f"### Interpreted idea\n{discovery.interpreted_idea}\n\n"
        f"### Known facts\n{_bullets(discovery.known_facts)}\n\n"
        f"### Assumptions\n{_bullets(discovery.assumptions)}\n\n"
        f"### Risks identified during discovery\n{_bullets(discovery.risks)}"
    )
    return BlueprintSection(
        section="discovery",
        title="Discovery",
        summary=f"Confidence {discovery.confidence:.0%}. {len(discovery.known_facts)} known facts, "
        f"{len(discovery.assumptions)} assumptions.",
        markdown=markdown,
    )


def _render_product_definition(product_definition: ProductDefinition) -> BlueprintSection:
    mvp_features = [
        f for f in product_definition.features if f.id in product_definition.mvp_feature_ids
    ]
    feature_lines = [f"{f.name} — {f.description}" for f in mvp_features] or ["None recorded."]
    persona_lines = [f"{p.name}: {p.description}" for p in product_definition.personas] or [
        "None recorded."
    ]
    markdown = (
        f"### Vision\n{product_definition.vision}\n\n"
        f"### Value proposition\n{product_definition.value_proposition}\n\n"
        f"### Personas\n{_bullets(persona_lines)}\n\n"
        f"### MVP features\n{_bullets(feature_lines)}\n\n"
        f"### Explicit exclusions\n{_bullets(product_definition.exclusions)}\n\n"
        f"### Success metrics\n{_bullets(product_definition.success_metrics)}"
    )
    return BlueprintSection(
        section="product_definition",
        title="Product Definition",
        summary=(
            f"{len(mvp_features)} MVP features across {len(product_definition.features)} total."
        ),
        markdown=markdown,
    )


def _render_requirements(requirements: RequirementsSpecification) -> BlueprintSection:
    fr_lines = [f"{r.id}: {r.description}" for r in requirements.functional_requirements] or [
        "None recorded."
    ]
    nfr_lines = [
        f"{r.id} ({r.category.value}, {r.priority.value}): {r.description}"
        for r in requirements.non_functional_requirements
    ] or ["None recorded."]
    edge_case_lines = [
        f"{e.id}: {e.description}" + (" (blocking)" if e.blocking else "")
        for e in requirements.edge_cases
    ]
    markdown = (
        f"### Functional requirements\n{_bullets(fr_lines)}\n\n"
        f"### Non-functional requirements\n{_bullets(nfr_lines)}\n\n"
        f"### Edge cases\n{_bullets(edge_case_lines)}"
    )
    return BlueprintSection(
        section="requirements",
        title="Requirements",
        summary=f"{len(requirements.functional_requirements)} functional, "
        f"{len(requirements.non_functional_requirements)} non-functional requirements.",
        markdown=markdown,
    )


def _render_market_and_gtm(market: MarketAndGTMStrategy) -> BlueprintSection:
    competitor_lines = [f"{c.name}: {c.description}" for c in market.competitors] or [
        "None recorded."
    ]
    channel_lines = [f"{c.name} ({c.priority}): {c.rationale}" for c in market.channels] or [
        "None recorded."
    ]
    markdown = (
        f"### Primary segment\n{market.primary_segment or 'Not specified.'}\n\n"
        f"### Positioning\n{market.positioning}\n\n"
        f"### Competitors\n{_bullets(competitor_lines)}\n\n"
        f"### Channels\n{_bullets(channel_lines)}\n\n"
        f"### Evidence gaps\n{_bullets(market.evidence_gaps)}"
    )
    return BlueprintSection(
        section="market_and_gtm",
        title="Market & Go-to-Market",
        summary=f"Primary segment: {market.primary_segment or 'not specified'}. "
        f"Confidence {market.confidence:.0%}.",
        markdown=markdown,
    )


def _render_solution_architecture(architecture: SolutionArchitecture) -> BlueprintSection:
    component_lines = [
        f"{c.name} ({c.id}): {c.responsibility}" for c in architecture.components
    ] or ["None recorded."]
    markdown = (
        f"### System context\n{architecture.system_context}\n\n"
        f"### Components\n{_bullets(component_lines)}\n\n"
        f"### Deployment\n{architecture.deployment.description}\n\n"
        f"### Scalability strategy\n{architecture.scalability_strategy}\n\n"
        f"### Reliability strategy\n{architecture.reliability_strategy}\n\n"
        f"### Observability strategy\n{architecture.observability_strategy}\n\n"
        f"### Risks\n{_bullets(architecture.risks)}"
    )
    return BlueprintSection(
        section="solution_architecture",
        title="Solution Architecture",
        summary=(
            f"{len(architecture.components)} components, "
            f"{len(architecture.integrations)} integrations, "
            f"{len(architecture.data_stores)} data stores."
        ),
        markdown=markdown,
    )


def _render_ai_architecture(ai_architecture: AIArchitecture) -> BlueprintSection:
    capability_lines = [
        f"{c.name} ({c.capability_type.value}): {c.justification}"
        for c in ai_architecture.capabilities
    ] or ["None recorded."]
    model_lines = [
        f"{m.role}: {m.provider}/{m.model} — {m.rationale}"
        for m in ai_architecture.model_selections
    ] or ["None recorded."]
    markdown = (
        f"### AI capabilities\n{_bullets(capability_lines)}\n\n"
        f"### Model selections\n{_bullets(model_lines)}\n\n"
        f"### Human oversight\n{ai_architecture.human_oversight}\n\n"
        f"### Fallback behavior\n{ai_architecture.fallback_behavior}\n\n"
        f"### AI risks\n{_bullets(ai_architecture.risks)}"
    )
    return BlueprintSection(
        section="ai_architecture",
        title="AI Architecture",
        summary=f"{len(ai_architecture.capabilities)} AI capabilities designed.",
        markdown=markdown,
    )


def _render_security_architecture(security: SecurityArchitecture) -> BlueprintSection:
    threat_lines = [f"{t.id} ({t.severity}): {t.description}" for t in security.threats] or [
        "None recorded."
    ]
    control_lines = [f"{c.id}: {c.name}" for c in security.controls] or ["None recorded."]
    markdown = (
        f"### Identity architecture\n{security.identity_architecture}\n\n"
        f"### Authentication strategy\n{security.authentication_strategy}\n\n"
        f"### Authorization strategy\n{security.authorization_strategy}\n\n"
        f"### Threats\n{_bullets(threat_lines)}\n\n"
        f"### Controls\n{_bullets(control_lines)}\n\n"
        f"### Residual risks\n"
        f"{_bullets([f'{r.description} ({r.severity})' for r in security.residual_risks])}"
    )
    return BlueprintSection(
        section="security_architecture",
        title="Security Architecture",
        summary=(
            f"{len(security.threats)} threats identified, "
            f"{len(security.controls)} controls defined."
        ),
        markdown=markdown,
    )


def _render_qa_evaluation(qa: QAEvaluationPlan) -> BlueprintSection:
    gate_lines = [
        f"{g.name}{' (blocking)' if g.blocking else ''}: {g.criteria}" for g in qa.release_gates
    ] or ["None recorded."]
    markdown = (
        f"### Test strategy\n{qa.test_strategy}\n\n"
        f"### Quality objectives\n{_bullets(qa.quality_objectives)}\n\n"
        f"### Release gates\n{_bullets(gate_lines)}\n\n"
        f"### Quality risks\n{_bullets(qa.risks)}"
    )
    return BlueprintSection(
        section="qa_evaluation",
        title="QA & Evaluation",
        summary=f"{len(qa.test_suites)} test suites, {len(qa.release_gates)} release gates.",
        markdown=markdown,
    )


def _render_lead_review(review: LeadReview) -> BlueprintSection:
    finding_lines = [f"[{f.severity}] {f.area}: {f.description}" for f in review.findings] or [
        "No findings recorded."
    ]
    markdown = (
        f"### Decision\n{review.decision.value}\n\n"
        f"### Implementation readiness\n{review.implementation_readiness_score:.0%}\n\n"
        f"### Findings\n{_bullets(finding_lines)}\n\n"
        f"### Limitations\n{_bullets(review.limitations)}"
    )
    return BlueprintSection(
        section="lead_review",
        title="Lead Review",
        summary=(
            f"Decision: {review.decision.value}. "
            f"Readiness: {review.implementation_readiness_score:.0%}."
        ),
        markdown=markdown,
    )


def build_blueprint(
    *,
    discovery: DiscoveryResult,
    product_definition: ProductDefinition,
    requirements: RequirementsSpecification,
    specialist_plan: SpecialistExecutionPlan,
    solution_architecture: SolutionArchitecture,
    lead_review: LeadReview,
    market_and_gtm: MarketAndGTMStrategy | None = None,
    ai_architecture: AIArchitecture | None = None,
    security_architecture: SecurityArchitecture | None = None,
    qa_evaluation: QAEvaluationPlan | None = None,
) -> ProductBlueprint:
    """Deterministically assemble the final ``ProductBlueprint``.

    Only selected specialist artifacts produce a section — a specialist
    that was not selected by ``specialist_plan`` is correctly absent, not
    rendered as an empty placeholder section.
    """

    sections = [
        _render_discovery(discovery),
        _render_product_definition(product_definition),
        _render_requirements(requirements),
    ]
    if market_and_gtm is not None:
        sections.append(_render_market_and_gtm(market_and_gtm))
    sections.append(_render_solution_architecture(solution_architecture))
    if ai_architecture is not None:
        sections.append(_render_ai_architecture(ai_architecture))
    if security_architecture is not None:
        sections.append(_render_security_architecture(security_architecture))
    if qa_evaluation is not None:
        sections.append(_render_qa_evaluation(qa_evaluation))
    sections.append(_render_lead_review(lead_review))

    raw_limitations = [
        *discovery.limitations,
        *product_definition.limitations,
        *requirements.limitations,
        *(market_and_gtm.limitations if market_and_gtm else []),
        *solution_architecture.limitations,
        *(ai_architecture.limitations if ai_architecture else []),
        *(security_architecture.limitations if security_architecture else []),
        *(qa_evaluation.limitations if qa_evaluation else []),
        *specialist_plan.budget.limitations,
        *lead_review.limitations,
    ]
    # Specialists often independently restate the same upstream limitation
    # (e.g. "does not define architecture") — de-duplicate while preserving
    # the order specialists produced them in.
    limitations = list(dict.fromkeys(raw_limitations))
    open_questions = list(product_definition.open_questions)

    title = _derive_title(product_definition.vision)
    executive_summary = (
        f"{discovery.interpreted_idea} {product_definition.value_proposition} "
        f"Lead review decision: {lead_review.decision.value} "
        f"(readiness {lead_review.implementation_readiness_score:.0%})."
    ).strip()

    generated_markdown = "\n\n".join(
        f"## {section.title}\n\n{section.markdown}" for section in sections
    )
    generated_markdown = f"# {title}\n\n{executive_summary}\n\n{generated_markdown}"

    return ProductBlueprint(
        session_id=discovery.session_id,
        title=title,
        executive_summary=executive_summary,
        sections=sections,
        open_questions=open_questions,
        limitations=limitations,
        generated_markdown=generated_markdown,
    )
