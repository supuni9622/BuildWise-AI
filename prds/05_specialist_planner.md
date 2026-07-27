# BuildWise AI — Deterministic Specialist Planner PRD

**Document:** `specialist_planner.md`  
**Status:** Approved for implementation  
**Priority:** Immediate next phase  
**Target package:** `src/buildwise/planning/`  
**Framework dependency:** None  
**Runtime style:** Deterministic Python policy code  
**Primary output:** `SpecialistExecutionPlan`

---

## 1. Overview

BuildWise AI already has:

- structured discovery output;
- product planning output;
- specialist domain contracts;
- native CrewAI Agents;
- native CrewAI Tasks;
- four business-facing Crews;
- typed Flow state;
- deterministic Flow routing primitives.

The missing component is the deterministic planner that converts validated
product signals into a specialist execution plan.

The planner sits between the Product Planning Crew and the Technical Planning
Crew.

```text
DiscoveryResult
        +
ProductPlanningResult
        +
Runtime limits
        +
Explicit user requests
        +
Budget constraints
        ↓
Deterministic Specialist Planner
        ↓
SpecialistExecutionPlan
        ↓
Technical Planning Crew
```

The planner must remain ordinary Python.

It must not be implemented as:

- a CrewAI Agent;
- a CrewAI Task;
- a Crew;
- an LLM classifier;
- a tool;
- a generic rule-engine platform;
- a general DAG framework.

The planner exists to make specialist selection predictable, testable,
explainable, and inexpensive.

---

## 2. Problem

BuildWise has several optional specialist capabilities:

- Market & GTM;
- Solution Architecture;
- AI Architecture;
- Security Architecture;
- QA & Evaluation.

Not every consultation should execute every specialist.

Executing all specialists unconditionally would:

- increase model cost;
- increase latency;
- reduce clarity;
- create unnecessary architecture;
- weaken proportionality;
- make revision routing harder;
- produce irrelevant blueprint sections.

Letting an LLM decide specialist execution would make routing:

- non-deterministic;
- harder to test;
- harder to audit;
- more expensive;
- vulnerable to prompt variability;
- less reliable under budget pressure.

BuildWise therefore requires a deterministic planning layer that evaluates
structured domain signals and emits one canonical `SpecialistExecutionPlan`.

---

## 3. Goals

The planner must:

1. consume validated BuildWise domain artifacts;
2. produce the existing `SpecialistExecutionPlan`;
3. select only justified specialists;
4. preserve mandatory technical coverage;
5. record a reason for every selected specialist;
6. build a valid dependency graph;
7. build ordered execution groups;
8. identify work that may run independently;
9. apply runtime and budget constraints;
10. preserve critical specialist work whenever possible;
11. record limitations introduced by reduced scope;
12. remain framework-independent;
13. remain free of side effects;
14. remain easy to unit test;
15. provide stable behavior across repeated calls with identical input;
16. avoid duplicating Flow routing logic;
17. avoid duplicating specialist output models;
18. avoid inspecting raw prompts or model output text;
19. avoid keyword-only product classification;
20. remain small enough to implement and review in one focused phase.

---

## 4. Non-Goals

The planner must not:

- execute any Crew;
- construct any Agent;
- construct any Task;
- invoke an LLM;
- access the database;
- mutate Flow state;
- pause or resume a Flow;
- persist artifacts;
- aggregate actual model usage;
- calculate provider token prices;
- generate the final blueprint;
- perform lead review;
- revise specialist outputs;
- choose LLM model tiers;
- attach tools;
- enforce API rate limits;
- replace domain validation;
- replace CrewAI tracing;
- become a generic business-rules framework.

---

## 5. Architectural Position

```text
FastAPI
   ↓
CrewAI Consulting Flow
   ↓
Discovery Crew
   ↓
DiscoveryResult
   ↓
Early Market Policy
   ↓
Product Planning Crew
   ↓
ProductPlanningResult
   ↓
Deterministic Specialist Planner
   ↓
SpecialistExecutionPlan
   ↓
Technical Planning Crew
   ↓
TechnicalPlanningResult
   ↓
Lead Review Crew
```

The Flow owns orchestration.

The planner owns specialist planning policy.

The Technical Planning Crew owns specialist reasoning.

---

## 6. Target Package

```text
src/buildwise/planning/
├── __init__.py
├── policies.py
├── execution_graph.py
└── planner.py
```

No additional files should be introduced unless implementation reveals a real
need.

Do not add:

```text
models.py
engine.py
runtime.py
registry.py
rules/
plugins/
adapters/
```

The domain models already exist.

---

## 7. Existing Canonical Output

The planner must return:

```python
SpecialistExecutionPlan
```

from:

```text
src/buildwise/domain/specialist_planning.py
```

The current model contains:

```python
class SpecialistExecutionPlan(BuildWiseModel):
    recommendations: list[SpecialistRecommendation]
    execution_groups: list[SpecialistExecutionGroup]
    dependencies: list[SpecialistDependency]
    budget: BudgetDecision
    execution_summary: str
```

Supporting models:

```python
class SpecialistRecommendation(BuildWiseModel):
    specialist: SpecialistType
    required: bool
    reason: SpecialistSelectionReason
    explanation: str
    estimated_effort: str
```

```python
class SpecialistDependency(BuildWiseModel):
    source: SpecialistType
    target: SpecialistType
    dependency: DependencyType
    description: str
```

```python
class SpecialistExecutionGroup(BuildWiseModel):
    name: str
    execution_mode: ExecutionMode
    specialists: list[SpecialistType]
    rationale: str
```

```python
class BudgetDecision(BuildWiseModel):
    decision: BudgetDecisionType
    explanation: str
    excluded_specialists: list[SpecialistType]
    limitations: list[str]
```

These models are the canonical planning contract.

Do not create another routing-plan model.

---

## 8. Planner Inputs

The main planning operation consumes:

```text
DiscoveryResult
ProductPlanningResult
FlowRuntimeLimits
Explicit specialist requests
Optional current usage snapshot
```

The minimal required inputs are:

```python
DiscoveryResult
ProductPlanningResult
```

The planner may additionally receive:

```python
FlowRuntimeLimits
set[SpecialistType]
set[SpecialistType]
```

representing:

- explicitly requested specialists;
- explicitly excluded optional specialists.

Do not introduce duplicate intake or session models.

Use existing fields from:

```text
ProductIdeaRequest
ValidatedProductIdea
ProductIdeaContext
DiscoveryResult
ProductPlanningResult
FlowRuntimeLimits
```

---

## 9. Input Signals

### 9.1 Discovery signals

Use:

```python
discovery.capability_classification.capabilities
discovery.capability_classification.ai_required
discovery.capability_classification.rag_required
discovery.capability_classification.agents_required
discovery.capability_classification.automation_required
discovery.capability_classification.sensitive_data_detected
discovery.capability_classification.regulated_domain_detected
discovery.capability_classification.real_time_processing_required
discovery.capability_classification.external_integrations_expected
discovery.capability_classification.specialist_signals
discovery.risks
discovery.unknowns
discovery.limitations
discovery.completeness
```

### 9.2 Product Planning signals

Use:

```python
product_planning.product_definition
product_planning.requirements
product_planning.market_and_gtm
```

Relevant ProductDefinition signals include:

```python
features
mvp_feature_ids
risks
constraints
open_questions
AI-enabled features
```

Relevant RequirementsSpecification signals include:

```python
functional_requirements
non_functional_requirements
data_requirements
integration_requirements
edge_cases
business_rules
user_journeys
decision
limitations
```

### 9.3 Runtime-limit signals

Use:

```python
maximum_session_tokens
maximum_estimated_cost_usd
maximum_agent_executions
maximum_tool_calls
maximum_specialist_revisions
maximum_execution_seconds
```

The planner may use these as coarse policy constraints.

It must not pretend to know exact future token or dollar usage.

---

## 10. Two Planning Moments

BuildWise has two distinct deterministic decisions.

### 10.1 Early Market decision

This occurs before Product Planning Crew construction.

```text
DiscoveryResult
    ↓
Early Market Policy
    ↓
include_market_and_gtm: bool
```

This decision determines whether the Product Planning Crew includes the Market
& GTM Strategist.

It cannot depend on `ProductPlanningResult`, because that aggregate does not
exist yet.

### 10.2 Technical specialist planning

This occurs after Product Planning completes.

```text
DiscoveryResult
        +
ProductPlanningResult
        +
Limits
        +
Explicit requests
        ↓
SpecialistExecutionPlan
```

This plan is consumed by the Technical Planning Crew.

The two decisions may be exposed by the same planner service, but they must
remain separate methods.

---

## 11. Public API

Recommended public API:

```python
class SpecialistPlanner:
    def should_include_early_market_context(
        self,
        *,
        discovery: DiscoveryResult,
        explicitly_requested: bool = False,
    ) -> bool:
        ...

    def create_execution_plan(
        self,
        *,
        discovery: DiscoveryResult,
        product_planning: ProductPlanningResult,
        limits: FlowRuntimeLimits,
        explicitly_requested: set[SpecialistType] | None = None,
        explicitly_excluded: set[SpecialistType] | None = None,
    ) -> SpecialistExecutionPlan:
        ...
```

The implementation may use module-level pure functions internally.

The public API should remain small.

---

## 12. Specialist Selection Policy

### 12.1 Market & GTM

Market & GTM belongs primarily to the Product Planning Crew.

Select early Market & GTM when one or more of these are true:

- the user explicitly requests market analysis;
- the user explicitly requests competitor analysis;
- pricing strategy is required;
- launch strategy is required;
- the target market is unknown or weakly defined;
- the product depends on unvalidated commercial assumptions;
- discovery contains material market risk;
- the Product Definition requires evidence-backed positioning;
- the proposed product enters an existing competitive category;
- the user requests a business or investor-ready blueprint.

Do not select early Market & GTM only because every product exists in a market.

Do not select it when:

- the consultation is technical-only;
- the user has already provided sufficient current market evidence;
- the product is an internal tool with no commercial launch requirement;
- the budget is constrained and commercial analysis is explicitly optional;
- the user explicitly excludes market analysis.

If Market & GTM was already included in `ProductPlanningResult`, it must not be
reselected as a Technical Planning specialist.

### 12.2 Solution Architecture

Solution Architecture is required when:

- a build-ready blueprint is requested;
- implementation guidance is required;
- technical architecture is part of the final deliverable;
- integrations must be designed;
- deployment must be designed;
- data stores or system boundaries must be defined;
- the product is expected to reach MVP or production.

For the normal BuildWise consultation, Solution Architecture is required.

It may be omitted only for a narrowly scoped product-only consultation.

In the current MVP, the recommended default is:

```text
Solution Architecture = required
```

### 12.3 AI Architecture

Select AI Architecture when any validated signal indicates meaningful AI
design work.

Strong signals:

```text
CapabilityType.AI_ASSISTED
CapabilityType.AI_CORE
CapabilityType.RAG
CapabilityType.AGENTIC_WORKFLOW
```

Additional signals:

- `ai_required=True`;
- `rag_required=True`;
- `agents_required=True`;
- an MVP feature has `ai_enabled=True`;
- a functional requirement has category `ai`;
- an integration requirement uses an LLM provider;
- AI-generated outputs are user-visible;
- model routing, retrieval, evaluation, guardrails, or tool use requires design.

Do not select AI Architecture when:

- AI is only speculative;
- the user mentions AI without a concrete product capability;
- deterministic software fully satisfies the requirement;
- AI is explicitly out of scope;
- AI is deferred beyond the requested planning horizon.

### 12.4 Security Architecture

Select Security Architecture when any material security signal exists.

Strong signals:

- sensitive data detected;
- regulated domain detected;
- restricted, sensitive-personal, or regulated data;
- authentication or authorization requirements;
- multi-tenant data;
- payment or privileged integrations;
- public-facing APIs;
- external system actions;
- AI agents with side effects;
- tool execution against external systems;
- high or critical security, privacy, or compliance risk;
- explicit user request.

Security selection reasons should be prioritized:

1. `SENSITIVE_DATA`
2. `REGULATED_DOMAIN`
3. `EXTERNAL_INTEGRATIONS`
4. `HIGH_RISK`
5. `EXPLICIT_USER_REQUEST`
6. `PRODUCT_COMPLEXITY`

Do not select a full Security Architecture solely because standard login exists
in a low-risk prototype unless the requested output depth justifies it.

When omitted, baseline security requirements remain part of Solution
Architecture and Requirements, but the final blueprint must record that no
dedicated security architecture was performed.

### 12.5 QA & Evaluation

Select QA & Evaluation when one or more of these are true:

- AI Architecture is selected;
- user-visible AI outputs require evaluation;
- must-have performance, availability, reliability, security, accessibility,
  recoverability, data-integrity, or compliance requirements exist;
- blocking edge cases exist;
- complex integrations exist;
- concurrency, partial failure, dependency failure, state transition, or data
  consistency risks exist;
- high or critical risks exist;
- production readiness is requested;
- release gates are required;
- explicit user request.

For a normal build-ready blueprint, QA & Evaluation should usually be selected.

It may be omitted for:

- a lightweight concept consultation;
- a prototype-only scope;
- severely constrained budget;
- an explicit user decision accepting reduced validation coverage.

Omission must create a limitation.

---

## 13. Explicit User Requests

Explicit user requests must be represented separately from inferred signals.

Rules:

- a request to include an optional specialist should normally select it;
- a request to exclude an optional specialist may exclude it when safe;
- a request may not remove mandatory Solution Architecture in a build-ready
  technical blueprint;
- a request may not remove Security Architecture when regulated or highly
  sensitive data creates a critical requirement;
- a request may not remove QA when AI-generated or safety-critical behavior
  requires evaluation without creating a blocking limitation;
- conflicts must be recorded in the budget decision or execution summary.

Use:

```python
SpecialistSelectionReason.EXPLICIT_USER_REQUEST
```

when the explicit request is the primary reason.

---

## 14. Missing Information Policy

### 14.1 Blocking unknowns

If Discovery still contains blocking unknowns, the Flow should normally not
invoke the planner.

The planner should fail fast if:

```python
discovery.completeness.can_continue is False
```

or if unresolved blocking unknowns remain.

### 14.2 Non-blocking unknowns

Non-blocking unknowns may allow planning with limitations.

Examples:

- unknown production traffic;
- undecided cloud provider;
- incomplete pricing evidence;
- unknown exact compliance framework;
- uncertain AI model provider.

The planner must:

- continue only when safe;
- preserve selected specialists that help resolve the uncertainty;
- add a limitation through `BudgetDecision.limitations`;
- explain uncertainty in `execution_summary`.

### 14.3 Unknowns affecting specialist selection

If an unknown materially affects AI, Security, or QA need, prefer selecting the
specialist when omission could produce unsafe or incomplete advice.

Use conservative selection for:

- sensitive data uncertainty;
- regulatory uncertainty;
- autonomous action uncertainty;
- high-impact AI uncertainty.

Use conservative omission for:

- speculative market expansion;
- optional future integrations;
- future-phase AI ideas outside MVP scope.

---

## 15. Budget Policy

The planner applies coarse budget policy.

It must not estimate exact tokens or provider cost.

### 15.1 Budget priority order

Preserve specialist work in this order:

1. Solution Architecture
2. Security Architecture when mandatory
3. AI Architecture when AI is core
4. QA & Evaluation when AI, safety, or high-risk behavior exists
5. Market & GTM when explicitly required
6. Optional QA depth
7. Optional market depth

Lead Review is outside the specialist plan and must remain preserved by the
Flow whenever possible.

### 15.2 Budget decision values

Use:

```python
BudgetDecisionType.APPROVED
```

when all justified specialists may run.

Use:

```python
BudgetDecisionType.APPROVED_WITH_LIMITS
```

when execution may proceed but optional specialist coverage or depth is
reduced.

Use:

```python
BudgetDecisionType.DEFERRED
```

when planning cannot safely continue under the current budget but may continue
later.

Use:

```python
BudgetDecisionType.REJECTED
```

when the requested consultation cannot be delivered safely within constraints.

### 15.3 Exclusion rules

Budget may exclude only optional specialists.

Do not exclude a specialist when its absence would make the blueprint
materially unsafe or invalid.

Examples:

- do not exclude Security for regulated sensitive data;
- do not exclude AI Architecture for an AI-core product;
- do not exclude QA for safety-critical AI behavior;
- do not exclude Solution Architecture for a build-ready technical blueprint.

### 15.4 Limitations

Every budget-caused exclusion must add a limitation.

Examples:

```text
Market validation was omitted because of the constrained consultation budget.
Competitor, pricing, and launch recommendations are therefore not evidence-backed.
```

```text
Dedicated QA planning was omitted. The blueprint includes requirements and
architecture but does not provide a complete release-gate or regression strategy.
```

```text
Security architecture depth was reduced. Formal compliance applicability and
control validation require a separate specialist review.
```

---

## 16. Effort Classification

`SpecialistRecommendation.estimated_effort` is currently a string.

Use a stable value set:

```text
low
medium
high
```

Recommended mapping:

### Solution Architecture

- `medium` for straightforward MVP;
- `high` for integration-heavy, real-time, multi-platform, or regulated systems.

### AI Architecture

- `medium` for one bounded AI capability;
- `high` for RAG, agentic workflows, model routing, multimodal, or multiple AI
  capabilities.

### Security Architecture

- `medium` for standard authenticated applications;
- `high` for sensitive data, regulated workflows, payments, multi-tenancy, or
  autonomous actions.

### QA & Evaluation

- `medium` for normal production readiness;
- `high` for AI evaluation, safety-critical behavior, complex integrations, or
  adversarial testing.

### Market & GTM

- `medium` for bounded market analysis;
- `high` for broad competitor, pricing, geography, or multi-segment research.

The planner must emit only normalized lowercase values.

---

## 17. Dependency Graph

The planner builds a small fixed specialist graph.

It must not implement a general DAG engine.

### 17.1 Core dependencies

```text
Solution Architecture
    ↓
AI Architecture
```

AI Architecture requires the general solution context.

```text
Solution Architecture
    ↓
Security Architecture
```

Security Architecture requires system components, boundaries, integrations,
and deployment context.

```text
AI Architecture
    ↓
Security Architecture
```

This dependency exists only when AI Architecture is selected.

```text
Solution Architecture
    ↓
QA & Evaluation
```

QA requires architecture and requirements.

```text
AI Architecture
    ↓
QA & Evaluation
```

This dependency exists only when AI Architecture is selected.

```text
Security Architecture
    ↓
QA & Evaluation
```

This dependency exists only when Security Architecture is selected and QA must
validate its controls.

### 17.2 Market dependency

Market & GTM normally runs in Product Planning and is not part of the Technical
Planning graph.

Do not add Market & GTM dependencies to `TechnicalPlanningResult`.

### 17.3 Dependency type

Use:

```python
DependencyType.REQUIRES_OUTPUT
```

when the target needs the source artifact before execution.

Use:

```python
DependencyType.PROVIDES_CONTEXT
```

when the source improves the target but is not a hard prerequisite.

Use:

```python
DependencyType.REQUIRES_APPROVAL
```

only when the Flow introduces an explicit approval gate.

The MVP should primarily use `REQUIRES_OUTPUT`.

---

## 18. Execution Groups

Execution groups are ordered.

Specialists inside a parallel group may run together only when they have no
dependency on one another.

### 18.1 Typical AI product

```text
Group 1 — sequential
- Solution Architecture

Group 2 — sequential
- AI Architecture

Group 3 — sequential
- Security Architecture

Group 4 — sequential
- QA & Evaluation
```

### 18.2 Standard non-AI product

```text
Group 1 — sequential
- Solution Architecture

Group 2 — sequential
- Security Architecture, when selected

Group 3 — sequential
- QA & Evaluation, when selected
```

### 18.3 Independent specialist example

Where Security does not depend on AI and QA does not require Security output:

```text
Group 1 — sequential
- Solution Architecture

Group 2 — parallel
- Security Architecture
- QA & Evaluation
```

This should be used only when the Task input contracts genuinely allow it.

### 18.4 Current Crew implementation constraint

The current Technical Planning Crew uses `Process.sequential`.

Therefore, the initial planner may still describe logical parallel eligibility,
but the execution groups must remain compatible with the Crew implementation.

The initial implementation should prefer valid sequential groups over
theoretical parallelism.

Flow-level concurrency may be introduced later.

---

## 19. Execution Graph Builder

`execution_graph.py` owns:

- dependency construction;
- dependency validation;
- cycle detection;
- execution-group construction;
- group-order validation;
- selected-specialist coverage validation.

Recommended public functions:

```python
def build_dependencies(
    *,
    selected_specialists: set[SpecialistType],
) -> list[SpecialistDependency]:
    ...
```

```python
def build_execution_groups(
    *,
    selected_specialists: set[SpecialistType],
    dependencies: list[SpecialistDependency],
) -> list[SpecialistExecutionGroup]:
    ...
```

```python
def validate_execution_graph(
    *,
    selected_specialists: set[SpecialistType],
    dependencies: list[SpecialistDependency],
    execution_groups: list[SpecialistExecutionGroup],
) -> None:
    ...
```

The graph builder must be deterministic.

---

## 20. Policies Module

`policies.py` owns pure specialist-selection rules.

Recommended functions:

```python
def should_include_early_market_context(
    discovery: DiscoveryResult,
    *,
    explicitly_requested: bool,
) -> bool:
    ...
```

```python
def evaluate_solution_architecture(
    discovery: DiscoveryResult,
    product_planning: ProductPlanningResult,
) -> SpecialistRecommendation:
    ...
```

```python
def evaluate_ai_architecture(
    discovery: DiscoveryResult,
    product_planning: ProductPlanningResult,
) -> SpecialistRecommendation | None:
    ...
```

```python
def evaluate_security_architecture(
    discovery: DiscoveryResult,
    product_planning: ProductPlanningResult,
) -> SpecialistRecommendation | None:
    ...
```

```python
def evaluate_qa_and_evaluation(
    discovery: DiscoveryResult,
    product_planning: ProductPlanningResult,
    *,
    ai_selected: bool,
    security_selected: bool,
) -> SpecialistRecommendation | None:
    ...
```

```python
def apply_budget_policy(
    recommendations: list[SpecialistRecommendation],
    *,
    limits: FlowRuntimeLimits,
    explicitly_requested: set[SpecialistType],
) -> tuple[list[SpecialistRecommendation], BudgetDecision]:
    ...
```

Policies must not mutate input models.

---

## 21. Planner Module

`planner.py` is the public application service.

Responsibilities:

1. validate input ownership;
2. verify Discovery can continue;
3. collect explicit requests;
4. call selection policies;
5. apply budget policy;
6. build the dependency graph;
7. build execution groups;
8. validate the graph;
9. construct `SpecialistExecutionPlan`;
10. return the plan.

Recommended class:

```python
class SpecialistPlanner:
    def should_include_early_market_context(...):
        ...

    def create_execution_plan(...):
        ...
```

Recommended module-level default:

```python
SPECIALIST_PLANNER = SpecialistPlanner()
```

Only add a singleton if it remains stateless and immutable.

---

## 22. Ownership Validation

Before planning:

```python
discovery.session_id
```

must match:

```python
product_planning.session_id
```

The Product Planning aggregate already validates its internal artifact
ownership.

The planner should fail fast on cross-session input.

The planner should not repeat every internal Product Planning validation.

---

## 23. Plan Validation Rules

A valid `SpecialistExecutionPlan` must satisfy all of the following:

- each selected specialist appears once in recommendations;
- each dependency references selected specialists;
- no specialist depends on itself;
- no dependency cycle exists;
- every selected specialist appears in exactly one execution group;
- no excluded specialist appears in execution groups;
- no excluded specialist appears in dependencies;
- Solution Architecture precedes every selected technical dependent;
- AI Architecture precedes AI-dependent Security or QA work;
- Security precedes QA when QA validates security controls;
- execution groups are ordered;
- parallel groups contain no internal dependency;
- every budget-excluded specialist appears in `excluded_specialists`;
- every budget exclusion produces at least one limitation;
- `APPROVED` has no budget exclusions;
- `APPROVED_WITH_LIMITS` includes at least one limitation;
- `DEFERRED` or `REJECTED` does not produce an executable graph unless the
  domain model explicitly allows one;
- `execution_summary` explains selection, ordering, and limitations.

---

## 24. Error Handling

Raise clear application errors for:

- mismatched session ownership;
- incomplete Discovery;
- missing Product Planning artifacts;
- unsupported specialist type;
- contradictory explicit request and exclusion;
- impossible mandatory-specialist exclusion;
- invalid dependency;
- cycle detected;
- duplicate specialist recommendation;
- execution group missing a selected specialist;
- budget decision inconsistent with recommendations.

Do not silently repair invalid input.

Do not return a partial plan when the plan is unsafe.

---

## 25. Logging and Tracing

The planner must not depend on CrewAI tracing.

The Flow may emit structured application events around planner execution:

```text
specialist_planning_started
specialist_selected
specialist_excluded
specialist_planning_limited
specialist_planning_completed
specialist_planning_failed
```

Recommended safe fields:

```text
session_id
specialist
selected
reason
required
estimated_effort
budget_decision
dependency_count
execution_group_count
limitation_count
```

Do not log full product artifacts.

---

## 26. Performance

The planner should complete in memory in negligible time.

Target:

```text
< 50 ms for normal inputs
```

No network calls.

No database calls.

No LLM calls.

No file I/O.

---

## 27. Security

The planner must:

- use only validated domain artifacts;
- avoid raw prompt inspection;
- avoid dynamic code evaluation;
- avoid user-supplied executable rules;
- avoid arbitrary plugin loading;
- bound all collection processing;
- treat explicit user requests as input, not authority over mandatory safety
  rules;
- never remove required security coverage solely because the user asks.

---

## 28. Examples

### 28.1 Standard SaaS MVP

Signals:

```text
standard software
public API
authentication
no AI
no regulated data
production_v1
```

Plan:

```text
Solution Architecture — required
Security Architecture — selected
QA & Evaluation — selected
AI Architecture — not selected
```

Execution:

```text
Solution
    ↓
Security
    ↓
QA
```

Budget:

```text
APPROVED
```

### 28.2 AI RAG assistant

Signals:

```text
AI_CORE
RAG
user-visible generation
external model provider
document retrieval
```

Plan:

```text
Solution Architecture — required
AI Architecture — required
Security Architecture — selected
QA & Evaluation — selected
```

Execution:

```text
Solution
    ↓
AI
    ↓
Security
    ↓
QA
```

Budget:

```text
APPROVED
```

### 28.3 Internal prototype under constrained budget

Signals:

```text
prototype
internal tool
no sensitive data
no AI
low-risk workflow
```

Plan:

```text
Solution Architecture — required
AI Architecture — not selected
Security Architecture — not selected
QA & Evaluation — excluded due to budget
```

Budget:

```text
APPROVED_WITH_LIMITS
```

Limitation:

```text
Dedicated QA planning was omitted. The prototype blueprint does not include
full release gates, regression coverage, or production-readiness validation.
```

### 28.4 Regulated AI workflow under insufficient budget

Signals:

```text
AI_CORE
regulated domain
sensitive data
high-risk user impact
budget below required specialist coverage
```

Required:

```text
Solution
AI
Security
QA
```

Result:

```text
BudgetDecisionType.DEFERRED
```

The planner must not silently remove Security or QA.

---

## 29. Unit Test Requirements

### 29.1 Early Market policy

Test:

- explicit request selects Market & GTM;
- internal technical-only tool does not;
- commercial launch request selects it;
- competitor/pricing need selects it;
- constrained optional scope may omit it;
- explicit exclusion works when safe.

### 29.2 Solution Architecture

Test:

- normal BuildWise blueprint selects it;
- technical-only consultation selects it;
- product-only lightweight consultation may omit it only when policy allows;
- explicit exclusion is rejected when build-ready output requires it.

### 29.3 AI Architecture

Test:

- AI_ASSISTED selects AI;
- AI_CORE selects AI;
- RAG selects AI;
- AGENTIC_WORKFLOW selects AI;
- AI-enabled MVP feature selects AI;
- AI requirement selects AI;
- speculative future AI does not automatically select AI;
- AI explicitly excluded but mandatory raises an error or produces a deferred
  plan.

### 29.4 Security Architecture

Test:

- sensitive data selects Security;
- regulated domain selects Security;
- restricted classification selects Security;
- privileged integration selects Security;
- high security risk selects Security;
- ordinary low-risk prototype may omit Security;
- required Security cannot be removed by budget.

### 29.5 QA & Evaluation

Test:

- AI selection selects QA;
- critical quality NFR selects QA;
- high-risk workflow selects QA;
- blocking failure path selects QA;
- lightweight prototype may omit QA with limitation;
- safety-critical QA cannot be removed by budget.

### 29.6 Graph construction

Test:

- correct dependencies for Solution only;
- correct dependencies for Solution + AI;
- correct dependencies for Solution + Security;
- correct dependencies for Solution + AI + Security + QA;
- no self-dependencies;
- no cycles;
- every selected specialist appears once;
- excluded specialists never appear;
- parallel groups contain no internal dependency.

### 29.7 Budget policy

Test:

- approved full plan;
- approved with optional exclusions;
- deferred mandatory-coverage plan;
- rejected impossible plan;
- every exclusion has a limitation;
- Lead Review is not part of specialist exclusion policy.

### 29.8 Determinism

Call the planner twice with identical inputs.

Assert:

```text
same recommendations
same reasons
same dependencies
same groups
same budget decision
same execution summary
```

The current planning domain model has no timestamp fields, so complete equality
should be possible.

---

## 30. Integration Test Requirements

Integration tests should verify:

```text
DiscoveryResult
        +
ProductPlanningResult
        ↓
SpecialistPlanner
        ↓
SpecialistExecutionPlan
        ↓
create_technical_planning_crew(...)
```

No live LLM call is required.

Test that the Technical Planning Crew:

- accepts the plan;
- includes only selected specialists;
- rejects unsupported dependencies;
- produces a composition matching the plan.

---

## 31. Implementation Order

Implement in this order:

```text
1. policies.py
2. execution_graph.py
3. planner.py
4. __init__.py
5. unit tests
6. Technical Planning Crew integration test
7. remove remaining specialist-selection logic from flows/routing.py
8. wire planner into consulting_flow.py later
```

---

## 32. File-by-File Deliverables

### `src/buildwise/planning/policies.py`

Must contain:

- early Market policy;
- Solution policy;
- AI policy;
- Security policy;
- QA policy;
- effort classification;
- budget policy;
- explicit-request handling.

### `src/buildwise/planning/execution_graph.py`

Must contain:

- dependency builder;
- execution-group builder;
- cycle detection;
- graph validation.

### `src/buildwise/planning/planner.py`

Must contain:

- `SpecialistPlanner`;
- input ownership validation;
- plan construction;
- execution summary generation;
- no side effects.

### `src/buildwise/planning/__init__.py`

Must export:

- `SpecialistPlanner`;
- optional stateless default instance;
- selected public policy helpers only when useful.

---

## 33. Acceptance Criteria

The phase is complete when:

- `src/buildwise/planning/` exists;
- the package contains exactly the agreed files;
- no CrewAI imports exist in the package;
- no LLM calls exist;
- no database calls exist;
- the planner consumes `DiscoveryResult`;
- the planner consumes `ProductPlanningResult`;
- the planner accepts runtime limits;
- explicit requests are supported;
- early Market selection is deterministic;
- Solution selection is deterministic;
- AI selection is deterministic;
- Security selection is deterministic;
- QA selection is deterministic;
- budget limitations are recorded;
- the output is `SpecialistExecutionPlan`;
- no second routing-plan model exists;
- execution dependencies are valid;
- execution groups are valid;
- the Technical Planning Crew accepts the output;
- repeated identical input produces identical output;
- Ruff passes;
- mypy passes;
- unit tests pass;
- no live model calls are required by tests.

---

## 34. Validation Commands

```bash
uv run ruff format src/buildwise/planning tests/unit/planning
```

```bash
uv run ruff check src/buildwise/planning tests/unit/planning
```

```bash
uv run mypy src/buildwise/planning
```

```bash
uv run pytest tests/unit/planning -q
```

Import check:

```bash
uv run python -c "
from buildwise.planning import SpecialistPlanner

planner = SpecialistPlanner()
print(type(planner).__name__)
"
```

---

## 35. Definition of Done

The deterministic planner is done when it becomes the only component that
answers:

```text
Which technical specialists should run?
Why should they run?
Which specialists are mandatory?
Which specialists are optional?
What order must they follow?
Which work can run independently?
What must be omitted under budget pressure?
What limitations result from omission?
```

The Flow should then only do this:

```python
plan = specialist_planner.create_execution_plan(
    discovery=state.discovery_result,
    product_planning=state.product_planning_result,
    limits=state.limits,
    explicitly_requested=requested_specialists,
    explicitly_excluded=excluded_specialists,
)
```

The Flow stores the plan and passes it to the Technical Planning Crew.

The planner makes policy decisions.

The Flow orchestrates.

The Crew reasons.

The Agents remain specialists.
