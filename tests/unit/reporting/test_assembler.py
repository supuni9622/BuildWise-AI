from __future__ import annotations

from pathlib import Path

from buildwise.domain.architecture import SolutionArchitecture
from buildwise.domain.enums import BlueprintSectionType, ReviewDecision
from buildwise.domain.review import LeadReview
from buildwise.domain.specialist_planning import SpecialistExecutionPlan
from buildwise.domain.technical_planning import TechnicalPlanningResult
from buildwise.domain.usage import UsageRecord, UsageSummary
from buildwise.reporting import assemble_blueprint, write_blueprint_markdown
from fixtures.planning import build_product_planning_inputs


def test_assemble_blueprint_keeps_open_questions_distinct_from_limitations(
    tmp_path: Path,
) -> None:
    discovery, product_planning = build_product_planning_inputs()
    product = product_planning.product_definition.model_copy(
        update={
            "open_questions": ["Which region hosts customer data?"],
            "limitations": ["No formal compliance assessment was performed."],
        }
    )
    product_planning = product_planning.model_copy(update={"product_definition": product})
    solution = SolutionArchitecture.model_construct(
        session_id=discovery.session_id,
        requirements_specification_id=product_planning.requirements.id,
        executive_summary="A modular service architecture supports the MVP.",
        architecture_style="modular_monolith",
        architecture_style_rationale="It minimizes early operational complexity.",
        components=[],
        technology_choices=[],
        deployment_summary="Deploy as one independently versioned application.",
        assumptions=[],
        open_questions=[],
        limitations=[],
        risks=[],
        architecture_cost_estimates=[],
    )
    technical = TechnicalPlanningResult.model_construct(
        session_id=discovery.session_id,
        solution_architecture=solution,
        ai_architecture=None,
        security_architecture=None,
        qa_evaluation=None,
    )
    plan = SpecialistExecutionPlan.model_construct(
        recommendations=[],
        execution_groups=[],
        dependencies=[],
        execution_summary="Run the required solution architecture specialist.",
    )
    review = LeadReview(
        executive_summary="The blueprint is ready for implementation.",
        decision=ReviewDecision.APPROVED,
        approved_for_blueprint=True,
    )
    usage = UsageSummary(
        records=[UsageRecord(model="test-model", total_tokens=30)],
        input_tokens=10,
        output_tokens=20,
        total_tokens=30,
        estimated_cost_usd=0.05,
        agent_execution_count=2,
    )

    blueprint = assemble_blueprint(
        discovery=discovery,
        product_planning=product_planning,
        specialist_plan=plan,
        technical_planning=technical,
        lead_review=review,
        usage_summary=usage,
    )

    assert [section.section for section in blueprint.sections] == list(BlueprintSectionType)
    assert blueprint.open_questions == ["Which region hosts customer data?"]
    assert blueprint.limitations == [
        "No formal compliance assessment was performed.",
        "Market research was omitted.",
    ]
    assert "## Open Questions" in blueprint.generated_markdown
    assert "## Limitations" in blueprint.generated_markdown
    assert blueprint.usage_summary.total_tokens == 30
    assert blueprint.usage_summary.model_usage == {"test-model": 1}

    output = write_blueprint_markdown(blueprint, tmp_path / "blueprint.md")
    assert output.read_text(encoding="utf-8") == blueprint.generated_markdown
