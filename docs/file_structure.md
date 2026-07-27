# BuildWise AI — File Structure

Snapshot as of the current codebase. Status legend: **Built** (implemented and
validated), **Partial** (some real logic, but incomplete), **Stub** (empty
package, placeholder only), **N/A** (not code — docs, config, assets).

```
BuildWise-AI/
├── src/buildwise/
│   ├── main.py                          Built   — FastAPI app factory, lifespan, middleware wiring
│   │
│   ├── domain/                          Built   — framework-independent Pydantic v2 models (canonical source of truth)
│   │   ├── __init__.py                  Built   — wildcard-imports every submodule into `buildwise.domain`
│   │   ├── common.py                    Built   — BuildWiseModel base, scalar types (Slug, ShortText…), MoneyAmount, CostEstimate
│   │   ├── enums.py                     Built   — every StrEnum (SessionStatus, AgentType, SpecialistType, RevisionTarget…)
│   │   ├── errors.py                    Built   — FastAPI exception handlers + ErrorResponse
│   │   ├── health.py                    Built   — HealthResponse
│   │   ├── api.py                       Built   — ApiRootResponse
│   │   ├── usage.py                     Built   — UsageRecord / UsageSummary
│   │   ├── agent.py                     Built   — framework-independent AgentContract/AgentRegistry (superseded in practice by agents/base.py + agents/registry.py)
│   │   ├── session.py                   Built   — ConsultingSession lifecycle record, SessionError
│   │   ├── intake.py                    Built   — ProductIdeaRequest, ValidatedProductIdea, ProductIdeaContext, ClarificationAnswer
│   │   ├── discovery.py                 Built   — DiscoveryResult, KnownFact, Assumption, Unknown, CompletenessResult, CapabilityClassification
│   │   ├── product.py                   Built   — ProductDefinition, ProductGoal, UserPersona, ProductFeature, ProductRoadmapItem
│   │   ├── requirements.py              Built   — RequirementsSpecification, FunctionalRequirement, UserJourney, UserStory…
│   │   ├── market_and_gtm.py            Built   — MarketAndGTMStrategy, MarketSegment, CompetitorProfile, PricingHypothesis…
│   │   ├── architecture.py              Built   — SolutionArchitecture, ArchitectureComponent, DeploymentUnit, TechnologyChoice…
│   │   ├── ai_architecture.py           Built   — AIArchitecture, AICapability, ModelSelection, RAGDesign, AIGuardrail, AIEvaluationMetric…
│   │   ├── security.py                  Built   — SecurityArchitecture, ThreatModel, SecurityControl, IncidentResponsePlan
│   │   ├── qa.py                        Built   — QAEvaluationPlan, TestStrategy, ReleaseGate, QualityRisk
│   │   ├── review.py                    Built   — LeadReview, RevisionRequest, ReviewFinding, ConsistencyCheck
│   │   ├── specialist_planning.py       Built   — SpecialistExecutionPlan, SpecialistRecommendation, BudgetDecision
│   │   ├── product_planning.py          Built   — ProductPlanningResult (aggregate: ProductDefinition + Requirements + optional MarketAndGTM)
│   │   ├── technical_planning.py        Built   — TechnicalPlanningResult (aggregate: SolutionArchitecture + optional AI/Security/QA)
│   │   └── blueprint.py                 Built   — ProductBlueprint, BlueprintSection, SourceReference, UsageSummary (models only — no assembler yet)
│   │
│   ├── agents/                          Built   — CrewAI agent contracts + factory
│   │   ├── base.py                      Built   — AgentContract, AgentCapabilityPolicy, AgentRuntimeSettings (the contract actually used)
│   │   ├── registry.py                  Built   — AgentContractRegistry + validated DEFAULT_AGENT_CONTRACTS for all 9 agents
│   │   ├── factory.py                   Built   — AgentFactory: contract → native crewai.Agent (resolves LLM, tools, skills)
│   │   ├── product_discovery_analyst.py Built
│   │   ├── product_manager.py           Built
│   │   ├── business_analyst.py          Built
│   │   ├── market_and_gtm_strategist.py Built
│   │   ├── solution_architect.py        Built
│   │   ├── ai_architect.py              Built
│   │   ├── security_architect.py        Built
│   │   ├── qa_evaluation_architect.py   Built
│   │   └── lead_reviewer.py             Built
│   │
│   ├── skills/                          Built   — one SKILL.md per agent, attached by AgentFactory
│   │   └── <agent_name>/SKILL.md        Built   (×9)
│   │
│   ├── tools/                           Built   — official CrewAI tools only, lazily resolved
│   │   └── registry.py                  Built   — ToolRegistry: web_search (Serper), web_scraper, github_search
│   │
│   ├── tasks/                           Built   — native crewai.Task factories, one business capability per file
│   │   ├── guardrails.py                Built   — shared deterministic guardrails (require_pydantic_output, run_domain_validator…)
│   │   ├── revisions.py                 Built   — format_revision_instructions() shared by every specialist task
│   │   ├── discovery.py                 Built   — create_discovery_task → DiscoveryResult
│   │   ├── product_definition.py        Built   — create_product_definition_task → ProductDefinition
│   │   ├── requirements.py              Built   — create_requirements_task → RequirementsSpecification
│   │   ├── market_and_gtm.py            Built   — create_market_and_gtm_task → MarketAndGTMStrategy (dual same/cross-Crew context)
│   │   ├── solution_architecture.py     Built   — create_solution_architecture_task → SolutionArchitecture
│   │   ├── ai_architecture.py           Built   — create_ai_architecture_task → AIArchitecture (dual-mode)
│   │   ├── security_architecture.py     Built   — create_security_architecture_task → SecurityArchitecture (dual-mode)
│   │   ├── qa_evaluation.py             Built   — create_qa_evaluation_task → QAEvaluationPlan (dual-mode)
│   │   └── lead_review.py               Built   — create_lead_review_task → LeadReview
│   │
│   ├── crews/                           Built   — 4 business Crews (no registry, explicit imports)
│   │   ├── discovery.py                 Built   — create_discovery_crew (1 agent, 1 task)
│   │   ├── product_planning.py          Built   — create_product_planning_crew + assemble_product_planning_result
│   │   ├── technical_planning.py        Built   — create_technical_planning_crew + assemble_technical_planning_result
│   │   └── lead_review.py               Built   — create_lead_review_crew (1 agent, 1 task)
│   │
│   ├── flows/                           Partial — building blocks exist; the actual orchestrating Flow does not
│   │   ├── state.py                     Built   — BuildWiseFlowState (the full session state machine)
│   │   ├── routing.py                   Built   — pure deterministic routing functions (route_after_discovery, build_specialist_routing_plan…)
│   │   └── smoke.py                     Built   — trivial demo Flow proving CrewAI Flow imports work; not the real Flow
│   │   └── consulting_flow.py           MISSING — the actual orchestrator; does not exist yet
│   │
│   ├── planning/                        MISSING — deterministic specialist planner package does not exist yet
│   │
│   ├── api/                             Partial — operational endpoints only, no consultation endpoints
│   │   ├── router.py                    Built   — /health, /ready, mounts v1 router
│   │   └── v1/router.py                 Built   — GET /api/v1 root only
│   │
│   ├── config/                          Built
│   │   ├── settings.py                  Built   — pydantic-settings Settings (env-driven)
│   │   └── logging.py                   Built   — structlog configuration
│   │
│   ├── observability/                   Built
│   │   ├── middleware.py                Built   — RequestContextMiddleware (request ID propagation)
│   │   └── context.py                   Built   — contextvar accessors
│   │
│   ├── persistence/                     Partial — connectivity only, no schema or repositories
│   │   └── database.py                  Built   — SQLAlchemy engine + check_database_connection(); no ORM models, no tables, no repositories
│   │
│   ├── reporting/__init__.py            Stub    — empty; blueprint assembly/rendering not started
│   └── validation/__init__.py           Stub    — empty; output validation not started
│
├── tests/                               Stub    — fixtures/unit/integration dirs exist, no tests written yet
│
├── prds/                                N/A     — planning documents (tasks + crews architecture/specs/roadmaps, refactor plan)
├── docs/                                N/A     — architecture reference docs, this file, and its two companions
├── pyproject.toml, uv.lock              N/A     — dependencies (crewai==1.15.5, fastapi, sqlalchemy, structlog…)
├── Dockerfile, docker-compose.yml       N/A     — container build + Postgres compose service
└── README.md                            N/A
```

## Package dependency direction

```
domain/  (no internal dependencies — framework-independent)
   ↑
agents/ , tools/ , skills/   (depend on domain + crewai)
   ↑
tasks/   (depend on domain + agents' Agent objects + crewai.Task)
   ↑
crews/   (depend on domain + agents/factory.AgentFactory + tasks/* + crewai.Crew)
   ↑
flows/   (depend on domain + crews/* + crewai.Flow)   ← the orchestrator, not yet built
   ↑
api/     (depend on flows/* + FastAPI)                 ← not yet wired to flows/

config/, observability/, persistence/  are cross-cutting (used by main.py, api/, and — once built — flows/)
```

No layer imports "downward" (e.g. `domain/` never imports `crewai`; `tasks/`
never constructs an `Agent` or a `Crew`), matching every PRD in `prds/`.
