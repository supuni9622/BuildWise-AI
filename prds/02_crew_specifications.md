# BuildWise AI
# CrewAI Crew Technical Specifications

**Version:** 1.0  
**Status:** Approved  
**Scope:** Crew implementation specifications  
**Framework:** CrewAI 1.15.6  
**Project:** BuildWise AI  

---

# 1. Purpose

This document defines the implementation-ready specifications for every
BuildWise CrewAI Crew.

It should be used together with:

```text
docs/architecture/crews/01_crews_architecture_prd.md
docs/architecture/tasks/01_tasks_architecture_prd.md
docs/architecture/tasks/02_task_specifications.md
docs/architecture/tasks/03_implementation_roadmap.md
```

The Crews layer must compose:

- native CrewAI Agents
- native CrewAI Tasks
- native CrewAI Processes
- bounded execution configuration
- structured Pydantic outputs

The Crews layer must remain thin.

It must not become a second orchestration framework.

---

# 2. Target Package

```text
src/buildwise/crews/
├── __init__.py
├── discovery.py
├── product_definition.py
├── requirements.py
├── market_and_gtm.py
├── solution_architecture.py
├── ai_architecture.py
├── security_architecture.py
├── qa_evaluation.py
├── lead_review.py
└── registry.py
```

Do not add:

```text
base.py
factory.py
manager.py
runtime.py
executor.py
scheduler.py
```

unless repeated implementation logic creates a concrete need.

The initial implementation should favor explicit Crew factory functions over
premature abstractions.

---

# 3. Common Crew Factory Contract

Every Crew module should expose one main Crew factory.

Example:

```python
def create_solution_architecture_crew(
    *,
    requirements: RequirementsSpecification,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_request: RevisionRequest | None = None,
) -> Crew:
    ...
```

Factories must return a native:

```python
crewai.Crew
```

Factories must not call:

```python
crew.kickoff(...)
```

Execution belongs to the CrewAI Flow or application service invoking the Crew.

---

# 4. Common Dependencies

Crew factories may depend on:

```python
from crewai import Crew, Process
```

BuildWise dependencies may include:

```text
AgentFactory
Settings
Task factory functions
Structured domain input models
RevisionRequest
```

Crew factories must not depend on:

```text
FastAPI routers
HTTP requests
database sessions
ORM entities
Flow state classes
API response models
websocket connections
streaming response objects
repositories
session services
```

The Flow converts its state into the structured arguments required by Crew
factories.

---

# 5. Common Construction Pattern

The standard Crew factory pattern is:

```python
def create_example_crew(
    *,
    input_artifact: InputArtifact,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_request: RevisionRequest | None = None,
) -> Crew:
    agent = agent_factory.create(AgentType.EXAMPLE)

    task = create_example_task(
        agent=agent,
        input_artifact=input_artifact,
        revision_request=revision_request,
        guardrail_max_retries=settings.max_retries_per_operation,
    )

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=settings.crewai_verbose,
        cache=True,
        memory=False,
    )
```

Use the exact arguments supported by the installed CrewAI version.

Do not copy arguments from old or deprecated CrewAI versions without
verification.

---

# 6. Shared Crew Configuration

Unless a Crew has a documented reason to differ, use:

```python
process=Process.sequential
memory=False
cache=True
verbose=settings.crewai_verbose
```

The initial BuildWise implementation should not enable:

```text
hierarchical process
planning
persistent Crew memory
delegation
manager agents
automatic task reassignment
```

These features may be introduced later only when a validated requirement
justifies them.

---

# 7. Crew Output Contract

Each Crew has one canonical output artifact.

The final Task in the Crew must use:

```python
output_pydantic=<ExpectedDomainModel>
```

The Flow should consume the structured output after kickoff.

Conceptual execution:

```python
crew = create_solution_architecture_crew(...)

crew_output = crew.kickoff(inputs=crew_inputs)

artifact = crew_output.pydantic
```

If the installed CrewAI version exposes structured output through a different
documented field, use the official field.

The application must not treat `crew_output.raw` as the canonical artifact.

---

# 8. Revision Support

Every specialist Crew must support targeted revisions.

A Crew factory may accept:

```python
revision_request: RevisionRequest | None = None
```

The Task factory should receive the revision request and add bounded revision
instructions.

Revision instructions must:

- identify the specific issue
- preserve unaffected sections
- preserve existing valid decisions
- stay within the specialist’s ownership
- request the same root output model
- avoid complete regeneration unless explicitly required

The Crew itself must not decide whether a revision is necessary.

The Flow owns revision routing.

---

# 9. Discovery Crew

## 9.1 Module

```text
src/buildwise/crews/discovery.py
```

## 9.2 Public factory

```python
def create_discovery_crew(
    *,
    product_idea: ProductIdeaRequest,
    agent_factory: AgentFactory,
    settings: Settings,
    clarification_context: ProductIdeaContext | None = None,
) -> Crew:
    ...
```

Use the exact intake-domain models available in the repository.

## 9.3 Agent

```python
AgentType.PRODUCT_DISCOVERY_ANALYST
```

## 9.4 Task factory

```python
create_discovery_task(...)
```

## 9.5 Output

```python
DiscoveryResult
```

## 9.6 Process

```python
Process.sequential
```

## 9.7 Crew composition

```text
Agents: 1
Tasks: 1
```

## 9.8 Inputs

Required:

```text
ProductIdeaRequest
```

Optional:

```text
ProductIdeaContext
previous clarification answers
```

Clarification answers should be represented through structured domain models.

Do not pass raw conversation history.

## 9.9 Responsibilities

The Crew must produce:

- interpreted product idea
- known facts
- assumptions
- unknowns
- early risks
- capability classifications
- completeness assessment
- clarification questions when required
- discovery decision
- limitations
- confidence

## 9.10 Flow handoff

The Flow consumes the `DiscoveryResult`.

The Flow decides whether to:

```text
continue to product definition
pause for clarification
continue with limitations
fail the session
```

The Crew must not perform those actions directly.

## 9.11 Restrictions

The Crew must not:

- use web research by default
- define product features
- define MVP scope
- define architecture
- select specialists
- interact directly with the user
- persist clarification state
- resume the session

## 9.12 Acceptance criteria

The implementation is accepted when:

- it returns native `Crew`
- it contains one Product Discovery Analyst
- it contains one Discovery Task
- it uses `Process.sequential`
- memory is disabled
- the Task outputs `DiscoveryResult`
- clarification context is optional
- the Crew does not call `kickoff`
- no persistence or Flow logic exists

---

# 10. Product Definition Crew

## 10.1 Module

```text
src/buildwise/crews/product_definition.py
```

## 10.2 Public factory

```python
def create_product_definition_crew(
    *,
    discovery_result: DiscoveryResult,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_request: RevisionRequest | None = None,
) -> Crew:
    ...
```

## 10.3 Agent

```python
AgentType.PRODUCT_MANAGER
```

## 10.4 Task factory

```python
create_product_definition_task(...)
```

## 10.5 Output

```python
ProductDefinition
```

## 10.6 Process

```python
Process.sequential
```

## 10.7 Crew composition

```text
Agents: 1
Tasks: 1
```

## 10.8 Required input

```python
DiscoveryResult
```

The discovery result must be approved or approved with documented limitations
before the Flow invokes this Crew.

The Crew must not independently override the Discovery decision.

## 10.9 Responsibilities

The Crew must produce:

- product vision
- value proposition
- product goals
- personas
- product features
- priorities
- MVP scope
- explicit exclusions
- roadmap
- success metrics
- product risks
- assumptions
- limitations
- product-definition decision

## 10.10 Revision behavior

When `revision_request` is supplied:

- revise only Product Definition concerns
- preserve valid discovery facts
- preserve unaffected sections
- do not add technical architecture
- return a full schema-valid `ProductDefinition`

## 10.11 Restrictions

The Crew must not:

- create detailed requirements
- perform competitor research
- choose technologies
- select AI models
- define security controls
- define test strategy
- alter discovery facts silently

## 10.12 Acceptance criteria

- native `Crew`
- one Product Manager
- one Product Definition Task
- structured `ProductDefinition`
- deterministic process
- revision support
- no Business Analyst in this Crew
- no direct Flow or persistence access

---

# 11. Requirements Crew

## 11.1 Module

```text
src/buildwise/crews/requirements.py
```

## 11.2 Public factory

```python
def create_requirements_crew(
    *,
    product_definition: ProductDefinition,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_request: RevisionRequest | None = None,
) -> Crew:
    ...
```

## 11.3 Agent

```python
AgentType.BUSINESS_ANALYST
```

## 11.4 Task factory

```python
create_requirements_task(...)
```

## 11.5 Output

```python
RequirementsSpecification
```

## 11.6 Process

```python
Process.sequential
```

## 11.7 Crew composition

```text
Agents: 1
Tasks: 1
```

## 11.8 Required input

```python
ProductDefinition
```

## 11.9 Responsibilities

The Crew must produce:

- functional requirements
- non-functional requirements
- business rules
- data requirements
- integration requirements
- user journeys
- user stories where supported
- acceptance criteria
- edge cases
- traceability links
- assumptions
- requirement risks
- requirements decision

## 11.10 Revision behavior

A revision request may target:

- missing functional behavior
- vague non-functional requirements
- incomplete acceptance criteria
- missing traceability
- contradictory business rules
- incomplete edge cases
- unsupported requirements

The Crew must not revise product scope to solve a requirements issue.

## 11.11 Restrictions

The Crew must not:

- define service boundaries
- choose databases
- choose cloud services
- define prompts
- design RAG
- perform threat modeling
- create release gates
- select specialists

## 11.12 Acceptance criteria

- one Business Analyst
- one Requirements Task
- output is `RequirementsSpecification`
- no Product Manager task is duplicated
- requirements remain implementation-independent
- revisions preserve ProductDefinition boundaries

---

# 12. Market & GTM Crew

## 12.1 Module

```text
src/buildwise/crews/market_and_gtm.py
```

## 12.2 Public factory

```python
def create_market_and_gtm_crew(
    *,
    product_definition: ProductDefinition,
    requirements: RequirementsSpecification,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_request: RevisionRequest | None = None,
) -> Crew:
    ...
```

The exact required inputs should match the real Task factory.

Do not pass RequirementsSpecification if the task does not use it.

## 12.3 Agent

```python
AgentType.MARKET_AND_GTM_STRATEGIST
```

## 12.4 Task factory

```python
create_market_and_gtm_task(...)
```

## 12.5 Output

Use the actual root model from:

```text
src/buildwise/domain/market_and_gtm.py
```

Expected conceptual name:

```python
MarketAndGTMStrategy
```

## 12.6 Process

```python
Process.sequential
```

## 12.7 Crew composition

```text
Agents: 1
Tasks: 1
```

## 12.8 Agent capabilities

The Agent Factory may attach:

```text
web_search
web_scraper
```

through official CrewAI tools.

The Crew factory must not instantiate tools.

## 12.9 Responsibilities

The Crew must produce:

- market segments
- primary market segment
- users and buyers
- competitor and substitute analysis
- market opportunities
- positioning
- messaging pillars
- pricing hypotheses
- acquisition channels
- launch experiments
- launch strategy
- GTM risks
- evidence references
- evidence gaps
- cost estimates
- confidence
- strategy decision

## 12.10 Tool restrictions

The Crew must not broaden tool access.

If a Task narrows tools, the narrowed list must be a subset of the Agent’s
allowed tools.

The Crew must not add GitHub search unless the specific market investigation
requires repository evidence.

## 12.11 Revision behavior

Revision requests may target:

- weak evidence
- unclear primary segment
- unsupported competitor claims
- vague positioning
- pricing presented as fact
- unprioritized channels
- experiments without decision criteria

The Crew must preserve product scope.

## 12.12 Execution relationship

This Crew may run independently after Product Definition or Requirements are
available.

The Flow may execute it concurrently with technical specialist work if
application concurrency and cost policies permit.

## 12.13 Acceptance criteria

- official tools remain Agent-owned
- Crew returns the correct structured GTM model
- evidence-sensitive behavior is described in the Task
- no unsupported tool is attached
- no product-scope modification occurs
- no architecture work is requested

---

# 13. Solution Architecture Crew

## 13.1 Module

```text
src/buildwise/crews/solution_architecture.py
```

## 13.2 Public factory

```python
def create_solution_architecture_crew(
    *,
    requirements: RequirementsSpecification,
    product_definition: ProductDefinition | None = None,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_request: RevisionRequest | None = None,
) -> Crew:
    ...
```

Only include `ProductDefinition` if architecture decisions require product
context not already represented in RequirementsSpecification.

Avoid unnecessary duplicated context.

## 13.3 Agent

```python
AgentType.SOLUTION_ARCHITECT
```

## 13.4 Task factory

```python
create_solution_architecture_task(...)
```

## 13.5 Output

```python
SolutionArchitecture
```

## 13.6 Process

```python
Process.sequential
```

## 13.7 Crew composition

```text
Agents: 1
Tasks: 1
```

## 13.8 Responsibilities

The Crew must produce:

- architecture decision
- system context
- component architecture
- component responsibilities
- APIs and service boundaries
- data stores
- data flows
- integrations
- deployment view
- infrastructure recommendations
- scalability strategy
- reliability strategy
- observability approach
- implementation phases
- architecture risks
- cost estimates
- assumptions
- limitations

## 13.9 Dependency

This Crew runs after Requirements.

It normally runs before:

```text
AI Architecture Crew
Security Architecture Crew
QA & Evaluation Crew
```

## 13.10 Revision behavior

Revision requests may target:

- unjustified complexity
- missing components
- unclear ownership
- invalid references
- missing deployment detail
- missing reliability behavior
- missing observability
- requirement-coverage gaps

The Crew must preserve valid requirements and product scope.

## 13.11 Restrictions

The Crew must not:

- select LLMs
- define prompts
- design detailed RAG
- design AI Agents
- perform full threat modeling
- define the complete test strategy
- create market recommendations

## 13.12 Acceptance criteria

- one Solution Architect
- one native architecture Task
- exact `SolutionArchitecture` output
- no AI-specific architecture leakage
- no custom infrastructure research tools by default
- process is sequential
- memory is disabled

---

# 14. AI Architecture Crew

## 14.1 Module

```text
src/buildwise/crews/ai_architecture.py
```

## 14.2 Public factory

```python
def create_ai_architecture_crew(
    *,
    requirements: RequirementsSpecification,
    solution_architecture: SolutionArchitecture,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_request: RevisionRequest | None = None,
) -> Crew:
    ...
```

## 14.3 Agent

```python
AgentType.AI_ARCHITECT
```

## 14.4 Task factory

```python
create_ai_architecture_task(...)
```

## 14.5 Output

```python
AIArchitecture
```

## 14.6 Process

```python
Process.sequential
```

## 14.7 Crew composition

```text
Agents: 1
Tasks: 1
```

## 14.8 Required inputs

```text
RequirementsSpecification
SolutionArchitecture
```

The Flow must not invoke this Crew without an approved or usable
SolutionArchitecture unless the architecture explicitly allows otherwise.

## 14.9 Responsibilities

The Crew must produce:

- AI architecture decision
- AI capabilities
- deterministic alternatives
- model requirements
- model roles
- model strategy
- model selections
- routing rules
- prompt contracts
- tool-use policies
- AI Agent definitions
- AI workflow definitions
- RAG architecture
- ingestion and retrieval design
- AI guardrails
- evaluation strategy
- AI observability
- human oversight
- fallback behavior
- AI risks
- cost controls
- assumptions
- limitations

## 14.10 Conditional execution

The Flow invokes this Crew only when:

- AI capabilities are validated
- the specialist plan selects AI Architecture
- a targeted AI revision is requested

## 14.11 Revision behavior

Revision requests may target:

- unjustified AI usage
- incorrect deterministic/AI boundary
- incomplete model strategy
- missing fallback
- unsupported agentic complexity
- incomplete RAG design
- incomplete guardrails
- incomplete evaluation
- missing observability
- uncontrolled cost
- overlap with SolutionArchitecture

The Crew must preserve valid general architecture decisions.

## 14.12 Restrictions

The Crew must not:

- redesign the entire application
- grant unrestricted tools
- add multi-agent systems by default
- claim deterministic model behavior
- replace Security Architecture
- replace QA Architecture
- approve the final blueprint

## 14.13 Acceptance criteria

- exact `AIArchitecture` output
- one AI Architect
- Task receives SolutionArchitecture
- conditional execution remains Flow-owned
- no external tools are attached without an Agent contract requirement
- structured output and guardrails are configured

---

# 15. Security Architecture Crew

## 15.1 Module

```text
src/buildwise/crews/security_architecture.py
```

## 15.2 Public factory

```python
def create_security_architecture_crew(
    *,
    requirements: RequirementsSpecification,
    solution_architecture: SolutionArchitecture,
    ai_architecture: AIArchitecture | None,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_request: RevisionRequest | None = None,
) -> Crew:
    ...
```

Use:

```python
ai_architecture: AIArchitecture | None = None
```

when AI is optional.

## 15.3 Agent

```python
AgentType.SECURITY_ARCHITECT
```

## 15.4 Task factory

```python
create_security_architecture_task(...)
```

## 15.5 Output

```python
SecurityArchitecture
```

## 15.6 Process

```python
Process.sequential
```

## 15.7 Crew composition

```text
Agents: 1
Tasks: 1
```

## 15.8 Responsibilities

The Crew must produce:

- identity architecture
- authentication strategy
- authorization strategy
- privileged access design
- secrets-management strategy
- encryption strategy
- key-management expectations
- data classifications
- PII handling
- retention policies
- secure storage
- trust boundaries
- attack surfaces
- threat model
- security controls
- security requirements
- audit requirements
- compliance considerations
- validation methods
- residual risks
- incident-response readiness
- implementation phases
- security cost estimates

## 15.9 Dependency

Required:

```text
RequirementsSpecification
SolutionArchitecture
```

Optional:

```text
AIArchitecture
```

When AI is present, AI-specific threats and tool boundaries must be reviewed.

## 15.10 Revision behavior

Revision requests may target:

- missing tenant isolation
- weak authentication or authorization
- missing privileged-access controls
- missing secrets strategy
- incomplete data protection
- generic threat model
- threats without controls
- controls without validation
- unsupported compliance claims
- unaddressed AI security
- accepted critical risks

## 15.11 Restrictions

The Crew must not:

- provide legal certification
- redesign software components
- redesign AI workflows
- select product features
- approve organizational risk
- approve the final blueprint

## 15.12 Acceptance criteria

- optional AI context works
- exact `SecurityArchitecture` output
- one Security Architect
- threats and controls remain structured
- no custom security tool framework
- no legal claims beyond applicability considerations
- process is sequential

---

# 16. QA & Evaluation Crew

## 16.1 Module

```text
src/buildwise/crews/qa_evaluation.py
```

## 16.2 Public factory

```python
def create_qa_evaluation_crew(
    *,
    requirements: RequirementsSpecification,
    solution_architecture: SolutionArchitecture,
    ai_architecture: AIArchitecture | None,
    security_architecture: SecurityArchitecture | None,
    agent_factory: AgentFactory,
    settings: Settings,
    revision_request: RevisionRequest | None = None,
) -> Crew:
    ...
```

## 16.3 Agent

```python
AgentType.QA_AND_EVALUATION_ARCHITECT
```

## 16.4 Task factory

```python
create_qa_evaluation_task(...)
```

## 16.5 Output

```python
QAEvaluationPlan
```

## 16.6 Process

```python
Process.sequential
```

## 16.7 Crew composition

```text
Agents: 1
Tasks: 1
```

## 16.8 Responsibilities

The Crew must produce:

- quality objectives
- test strategy
- test suites
- critical scenarios
- acceptance tests
- performance requirements
- performance-validation strategy
- reliability requirements
- recovery validation
- security-control validation
- AI evaluation where applicable
- evaluation metrics
- release gates
- production quality signals
- quality risks
- implementation phases
- QA cost estimates
- assumptions
- limitations

## 16.9 Dependency

Required:

```text
RequirementsSpecification
SolutionArchitecture
```

Optional:

```text
AIArchitecture
SecurityArchitecture
```

When AI exists, the QA plan must include AI evaluation.

When Security exists, the QA plan must include control validation.

## 16.10 Execution timing

The Flow should run this Crew after all selected architectures that the QA plan
must validate.

Do not run QA in parallel with Security when Security output is required as QA
input.

## 16.11 Revision behavior

Revision requests may target:

- missing critical journeys
- insufficient negative testing
- vague performance validation
- missing reliability tests
- missing fallback tests
- missing AI evaluation
- missing security-control validation
- unenforceable release gates
- weak production quality signals
- excessive or insufficient test complexity

## 16.12 Restrictions

The Crew must not:

- redesign architecture
- change requirements
- select models
- redesign security controls
- claim testing eliminates all risk
- approve the final blueprint

## 16.13 Acceptance criteria

- exact `QAEvaluationPlan` output
- optional artifacts are handled correctly
- one QA & Evaluation Architect
- no custom evaluation platform
- release gates are structured
- QA remains proportional to product scope

---

# 17. Lead Review Crew

## 17.1 Module

```text
src/buildwise/crews/lead_review.py
```

## 17.2 Public factory

```python
def create_lead_review_crew(
    *,
    discovery_result: DiscoveryResult,
    product_definition: ProductDefinition,
    requirements: RequirementsSpecification,
    specialist_plan: SpecialistExecutionPlan,
    market_and_gtm: MarketAndGTMStrategy | None,
    solution_architecture: SolutionArchitecture | None,
    ai_architecture: AIArchitecture | None,
    security_architecture: SecurityArchitecture | None,
    qa_evaluation: QAEvaluationPlan | None,
    revision_history: list[RevisionRequest],
    agent_factory: AgentFactory,
    settings: Settings,
) -> Crew:
    ...
```

Adjust model names to the actual domain package.

## 17.3 Agent

```python
AgentType.LEAD_REVIEWER
```

## 17.4 Task factory

```python
create_lead_review_task(...)
```

## 17.5 Output

```python
LeadReview
```

## 17.6 Process

```python
Process.sequential
```

## 17.7 Crew composition

```text
Agents: 1
Tasks: 1
```

## 17.8 Responsibilities

The Crew must:

- account for required artifacts
- account for selected conditional artifacts
- ignore correctly unselected optional artifacts
- verify discovery consistency
- verify product consistency
- verify requirements traceability
- review specialist selection
- review architecture feasibility
- review AI design
- review security coverage
- review QA coverage
- review market evidence
- detect contradictions
- review assumptions
- review risks
- review cost consistency
- assess implementation readiness
- produce findings
- produce consistency checks
- produce bounded revision requests
- determine approval decision
- determine blueprint readiness

## 17.9 Input minimization

The Lead Review Crew may receive many artifacts.

Use structured serialization.

Do not pass:

- full chat history
- raw trace data
- repeated markdown copies of artifacts
- unrelated API metadata
- database objects

Preserve:

- identifiers
- decisions
- requirements
- traceability
- assumptions
- risks
- limitations
- costs
- implementation phases
- evidence references
- prior revision requests

## 17.10 Revision behavior

The Lead Review Crew does not revise specialist artifacts.

It returns:

```python
revision_requests: list[RevisionRequest]
```

The Flow routes these requests.

## 17.11 Decision consistency

The Task guardrails must enforce:

```text
APPROVED
    → approved_for_blueprint=True
    → no blocking revision requests

APPROVED_WITH_LIMITATIONS
    → approved_for_blueprint=True
    → limitations must exist

REVISION_REQUIRED
    → approved_for_blueprint=False
    → at least one revision request

REJECTED
    → approved_for_blueprint=False
    → rejection rationale must exist
```

Use the actual `ReviewDecision` enum values.

## 17.12 Restrictions

The Crew must not:

- rewrite specialist outputs
- construct the ProductBlueprint
- invoke specialist Crews
- mutate revision history
- enforce revision limits
- communicate directly with the user
- persist the review

## 17.13 Acceptance criteria

- exact `LeadReview` output
- one Lead Reviewer
- all selected artifacts are included
- unselected artifacts are not considered failures
- decision guardrail exists
- revision requests are bounded
- no specialist Agent is included in the Crew
- no hierarchical manager process is used

---

# 18. Crew Registry

## 18.1 Module

```text
src/buildwise/crews/registry.py
```

## 18.2 Purpose

Provide stable Crew identifiers and Crew factory discovery.

The registry must not hold mutable Crew instances.

Crews must be created per execution.

## 18.3 Suggested identifiers

```python
class CrewKey(StrEnum):
    DISCOVERY = "discovery"
    PRODUCT_DEFINITION = "product_definition"
    REQUIREMENTS = "requirements"
    MARKET_AND_GTM = "market_and_gtm"
    SOLUTION_ARCHITECTURE = "solution_architecture"
    AI_ARCHITECTURE = "ai_architecture"
    SECURITY_ARCHITECTURE = "security_architecture"
    QA_EVALUATION = "qa_evaluation"
    LEAD_REVIEW = "lead_review"
```

Use an existing enum if the repository already defines equivalent values.

Do not duplicate enums unnecessarily.

## 18.4 Registry responsibilities

The registry may:

- map stable Crew keys to factory functions
- verify all required factories are registered
- resolve a Crew factory by key
- expose available Crew keys
- support tests
- prevent duplicate registrations

The registry must not:

- construct all Crews eagerly
- execute Crews
- store Flow state
- persist results
- resolve specialist routing
- choose Crew dependencies

## 18.5 Suggested factory type

```python
CrewFactory = Callable[..., Crew]
```

Because Crew factories have different typed arguments, a simple registry may
use a broader callable type.

Avoid destroying useful typing merely to force all factories into one generic
signature.

If a registry creates excessive type complexity, omit it from the MVP.

The Flow may import explicit Crew factories directly.

## 18.6 Acceptance criteria

- no global Crew instances
- duplicate keys rejected
- unknown keys fail clearly
- no execution behavior
- no routing decisions
- registry remains optional for the Flow implementation

---

# 19. Package Exports

## 19.1 Module

```text
src/buildwise/crews/__init__.py
```

## 19.2 Export

Export:

- all public Crew factory functions
- Crew registry types only if implemented
- stable Crew identifiers only if implemented

Example:

```python
from buildwise.crews.discovery import create_discovery_crew
from buildwise.crews.product_definition import (
    create_product_definition_crew,
)

__all__ = [
    "create_discovery_crew",
    "create_product_definition_crew",
]
```

Do not export:

- internal formatting helpers
- private validation functions
- module-level mutable state
- preconstructed Crew instances

---

# 20. Crew Inputs and Kickoff Inputs

Crew construction inputs and Crew kickoff inputs are separate concepts.

## Construction inputs

Used to create:

- Agent
- Task
- Crew configuration

Example:

```python
crew = create_solution_architecture_crew(
    requirements=requirements,
    agent_factory=agent_factory,
    settings=settings,
)
```

## Kickoff inputs

Used to resolve placeholders in Task descriptions and Agent configuration.

Example:

```python
crew_output = crew.kickoff(
    inputs={
        "requirements": requirements.model_dump_json(),
    }
)
```

Choose one consistent pattern.

Do not inject the same large artifact both:

- directly into the Task description during construction
- and again through kickoff inputs

Prefer kickoff placeholders for large structured artifacts.

---

# 21. Input Placeholder Standards

Use stable input names.

Recommended examples:

```text
product_idea
clarification_context
discovery_result
product_definition
requirements
specialist_plan
market_and_gtm
solution_architecture
ai_architecture
security_architecture
qa_evaluation
revision_request
revision_history
```

Task descriptions should reference these placeholders consistently.

Example:

```text
Review the following approved RequirementsSpecification:

{requirements}
```

Do not use ambiguous placeholders such as:

```text
data
input
context
result
previous
```

---

# 22. Crew Execution Metadata

The Crew itself should remain native.

BuildWise execution metadata should be collected around Crew execution by the
Flow or application service.

Useful metadata includes:

```text
session_id
flow_id
crew_key
agent_type
task_name
started_at
completed_at
duration
status
retry_count
token_usage
estimated_cost
tool_calls
artifact_type
limitation_count
error_type
```

Do not add arbitrary metadata fields to CrewAI Crew objects when the framework
does not support them.

---

# 23. Logging Boundary

Crew factories may log construction failures when useful.

They should not produce verbose business logs.

The Flow should log:

```text
crew_execution_started
crew_execution_completed
crew_execution_failed
crew_execution_limited
```

Do not log full artifacts at INFO level.

Do not log:

- secrets
- full prompts
- confidential files
- raw user PII
- full LLM responses
- unredacted tool inputs

---

# 24. Tracing Boundary

Use CrewAI tracing for AI execution detail.

The Crews layer should not create a competing tracing abstraction.

Tracing should provide visibility into:

- Crew execution
- Task execution
- Agent execution
- LLM calls
- tool calls
- failures
- retries

BuildWise logs remain useful for application-level events.

---

# 25. Usage Metrics

After execution, the Flow should collect Crew usage information.

Do not calculate tokens inside Crew factories.

Potential usage fields include:

```text
prompt tokens
completion tokens
total tokens
cached tokens
successful model requests
tool usage
execution duration
estimated cost
```

The Flow aggregates all Crew executions into the session usage summary.

---

# 26. Error Propagation

Crew factories should fail during construction when:

- required input is absent
- Agent construction fails
- Skill loading fails
- tool configuration fails
- Task construction fails
- invalid revision input is supplied

Crew execution errors should propagate to the Flow.

The Flow applies:

```text
AgentFailureBehavior
session retry policy
fallback policy
continue-with-limitation policy
session failure policy
```

Do not swallow Crew execution exceptions.

---

# 27. Retry Boundaries

Crew factories must not implement manual retry loops.

Retries may exist at:

```text
LLM layer
Task guardrail layer
Flow operation layer
```

Keep all limits bounded.

Avoid multiplying retry layers unintentionally.

The Flow should record retry counts for each Crew execution.

---

# 28. Concurrency Boundary

Crew factories do not create application-level concurrency.

The Flow decides whether separate Crew executions run:

- sequentially
- concurrently
- conditionally

Task-level asynchronous execution should be used only inside a Crew when that
Crew contains independent tasks.

The initial one-Task Crews do not need:

```python
async_execution=True
```

for task coordination.

Flow-level concurrency is the appropriate mechanism for independent Crews.

---

# 29. Memory Boundary

All initial Crew factories should configure:

```python
memory=False
```

Canonical consultation context remains in Flow state.

Do not rely on hidden Crew memory for:

- artifact passing
- revision history
- user clarification
- specialist decisions
- session recovery

Memory may be evaluated later as a separate feature.

---

# 30. Crew Validation Checklist

Before returning any Crew from a factory, verify:

- the Agent was created successfully
- the Task was created successfully
- the Task is assigned to the expected Agent
- the expected root output model is configured
- the process is explicit
- memory policy is explicit
- cache policy is explicit
- verbose policy uses Settings
- no unexpected Agent is present
- no unexpected Task is present
- no Crew execution has started
- no global mutable state was modified

---

# 31. Unit Test Requirements

## Main tests

For each Crew factory, verify:

- return type is `Crew`
- correct Agent count
- correct Task count
- correct Agent role
- correct Task name
- correct process
- correct output Pydantic model
- guardrails configured
- memory disabled
- verbose setting respected
- revision request passed to Task when supplied

## Edge tests

Verify:

- missing required input
- invalid revision target
- disabled Agent contract
- missing Skill package
- missing Serper credentials for a tool-enabled Agent
- optional AI architecture omitted
- optional Security architecture omitted
- wrong domain artifact type
- settings iteration limit below contract limit
- duplicate Task insertion
- Crew registry unknown key
- revision request supplied to wrong specialist

No unit test should perform a live model call.

---

# 32. Integration Test Expectations

A small integration suite may later verify:

- native Agent construction
- Skill attachment
- official tool attachment
- native Task construction
- native Crew construction
- structured kickoff output using a controlled test model or mocked provider
- guardrail correction behavior
- one end-to-end specialist Crew execution

Live external services should not be required for the default test suite.

---

# 33. Security Checklist

Every Crew implementation must preserve:

- Agent tool allowlists
- no task-level permission broadening
- no raw secrets in inputs
- no unrestricted file access
- no unrestricted code execution
- no unrestricted database access
- bounded Agent iterations
- bounded Task retries
- structured outputs
- tenant/session identifiers where required
- redacted logging
- safe handling of untrusted web content
- Flow-level approval for consequential actions

---

# 34. Performance Checklist

Crew construction should be lightweight.

Avoid:

- loading all Skill files repeatedly in custom code
- constructing all Agents for every Crew
- constructing unused tools
- constructing unused specialist Crews
- serializing every prior artifact
- enabling persistent memory without need
- creating duplicate LLM objects unnecessarily where safe reuse is available

Tool and Agent construction should remain lazy.

---

# 35. Cost Checklist

Each Crew should use:

- only one required specialist Agent
- the contract-selected model tier
- bounded iteration count
- bounded retries
- only required context
- only required tools
- one focused Task where practical

Do not add:

- manager models
- planning models
- secondary reviewer Agents
- unnecessary parallel Tasks
- generic synthesis Agents

without demonstrated value.

---

# 36. Implementation Order

Implement Crews in this order:

```text
1. discovery.py
2. product_definition.py
3. requirements.py
4. solution_architecture.py
5. market_and_gtm.py
6. ai_architecture.py
7. security_architecture.py
8. qa_evaluation.py
9. lead_review.py
10. registry.py, only if still useful
11. __init__.py
```

This order follows dependency depth.

---

# 37. Definition of Done

The Crew specifications are complete when every Crew has:

- a clear module
- a clear factory signature
- one primary output
- one owning Agent
- one owning Task
- explicit required inputs
- explicit optional inputs
- explicit process selection
- explicit dependency rules
- revision behavior
- restrictions
- acceptance criteria
- no Flow ownership
- no persistence ownership
- no tool reimplementation
- no custom Crew runtime
- no hidden context propagation

---

# 38. Next Document

The next document is:

```text
docs/architecture/crews/03_crew_implementation_roadmap.md
```

It should define:

- implementation phases
- file dependencies
- exact build order
- validation commands
- integration with the Task layer
- integration with AgentFactory
- Flow handoff contracts
- testing expectations
- final Crew-layer Definition of Done