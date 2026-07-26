# BuildWise AI
# CrewAI Crews Architecture PRD

**Version:** 1.0  
**Status:** Approved  
**Scope:** Crew architecture only  
**Framework:** CrewAI 1.15.6  
**Project:** BuildWise AI  

---

# 1. Purpose

This document defines the architecture and design rules for the BuildWise
CrewAI Crews layer.

The Crews layer provides focused execution units that combine:

- native CrewAI Agents
- native CrewAI Tasks
- an appropriate CrewAI Process
- bounded execution settings
- structured outputs
- tracing and usage information

The Crews layer does not own the overall BuildWise workflow.

The CrewAI Flow owns:

- state
- routing
- branching
- execution order between Crews
- specialist selection
- pause and resume
- human clarification
- human approval
- revision routing
- persistence
- final completion

Crews provide controlled pockets of specialist reasoning inside that
deterministic Flow.

---

# 2. Architecture Position

```text
FastAPI
   ↓
API Router
   ↓
CrewAI Consulting Flow
   ↓
Focused Crew
   ↓
Native CrewAI Tasks
   ↓
Native CrewAI Agents
   ├── Skills
   ├── Tools
   ├── MCP Servers
   ├── Apps
   └── Knowledge
   ↓
Structured Pydantic Output
   ↓
Flow State
   ↓
Persistence / Reporting / API Response
```

The BuildWise architecture must remain Flow-first.

```text
Flow
   owns orchestration

Crew
   owns a focused reasoning unit

Task
   owns a concrete assignment

Agent
   owns specialist reasoning

Skill
   owns reusable methodology

Tool / MCP / App
   owns external action capability

Knowledge
   owns retrieved factual context
```

---

# 3. Goals

The Crews layer must:

1. Use native CrewAI `Crew` objects.
2. Compose native CrewAI Agents and Tasks.
3. Keep every Crew focused on one business outcome.
4. Return structured specialist artifacts.
5. Remain reusable from the CrewAI Flow.
6. Support bounded retries and execution limits.
7. Preserve agent specialization.
8. Avoid duplicating Flow responsibilities.
9. Avoid rebuilding CrewAI runtime capabilities.
10. Remain lean enough for the BuildWise MVP.
11. Support conditional specialist execution.
12. Support targeted revision runs.
13. Preserve traceability between Crew input and output.
14. Expose execution results in a form the Flow can validate and persist.
15. Use CrewAI tracing rather than implementing a separate AI tracing system.

---

# 4. Non-Goals

The Crews layer must not implement:

- API endpoints
- HTTP request handling
- session persistence
- database repositories
- Flow state
- Flow routing
- pause and resume
- human clarification
- specialist-selection rules
- application-level retries
- model routing
- cost-budget enforcement
- final blueprint assembly
- custom task scheduling
- custom agent runtimes
- custom tool execution engines
- custom tracing platforms
- custom memory platforms
- custom structured-output parsers
- custom delegation systems
- custom context-window management
- direct user interaction

These concerns belong to CrewAI itself or to another BuildWise layer.

---

# 5. Official CrewAI Components

BuildWise Crews must use native CrewAI components.

```python
from crewai import Agent, Crew, Process, Task
```

The Crews layer may configure:

- `agents`
- `tasks`
- `process`
- `verbose`
- `memory`, only when justified
- `cache`
- `max_rpm`
- `planning`, only when justified
- callbacks supported by the selected CrewAI version
- tracing through CrewAI configuration

The Crews layer must not wrap `Crew` in a custom execution framework.

A small factory function or class may create a native CrewAI `Crew`, but the
returned execution object must remain a native CrewAI object.

---

# 6. Crew Design Principles

## 6.1 One Crew, one focused outcome

Every Crew must produce one primary business artifact.

Good:

```text
Solution Architecture Crew
    → SolutionArchitecture
```

Bad:

```text
Complete Consulting Crew
    → ProductDefinition
    → RequirementsSpecification
    → SolutionArchitecture
    → AIArchitecture
    → SecurityArchitecture
    → LeadReview
```

A giant Crew would weaken:

- execution control
- error isolation
- retry targeting
- specialist selection
- state persistence
- revision routing
- cost attribution
- observability

The Flow must coordinate multiple focused Crews.

---

## 6.2 Crews are reasoning units, not workflow engines

A Crew may coordinate multiple related Tasks.

A Crew must not decide:

- which later Crew runs
- whether the session pauses
- whether the user must clarify
- whether AI Architecture is selected
- whether Security is required
- whether a revision loop begins
- whether blueprint assembly proceeds

Those decisions belong to the Flow.

---

## 6.3 Use the smallest useful Crew

A Crew may contain:

- one Agent and one Task
- multiple Agents and sequential Tasks
- multiple Agents collaborating on one focused artifact

A one-Agent Crew is valid when it provides a clear native CrewAI execution
boundary.

Do not add additional Agents merely to make a Crew appear more agentic.

---

## 6.4 Preserve specialization

Each Agent must operate within its contract.

Agents must not duplicate another specialist’s ownership.

Examples:

- Product Manager owns product definition.
- Business Analyst owns implementation-ready requirements.
- Solution Architect owns general software architecture.
- AI Architect owns AI-specific architecture.
- Security Architect owns security architecture.
- QA & Evaluation Architect owns quality and evaluation planning.
- Lead Reviewer evaluates specialist outputs but does not redesign them.

---

## 6.5 Prefer sequential processes initially

Use `Process.sequential` by default.

Sequential execution is appropriate when:

- one Task depends on another
- outputs must be reviewed in order
- artifact ownership is explicit
- deterministic task order improves reliability
- the MVP does not require autonomous management

Do not use hierarchical execution by default.

A hierarchical process may be considered later only when:

- a real manager Agent is required
- delegation creates clear value
- task assignment must be dynamic inside one Crew
- the additional cost and unpredictability are justified

The Lead Reviewer does not automatically justify a hierarchical Crew.

The BuildWise Flow already controls higher-level execution.

---

## 6.6 Do not use delegation without a validated need

Most BuildWise Agents should use:

```python
allow_delegation=False
```

Delegation may be enabled only when:

- the Agent contract permits it
- the Crew design requires it
- delegated roles are explicit
- tool and cost limits remain bounded
- ownership does not become ambiguous

The initial BuildWise MVP should not depend on delegation.

---

## 6.7 Structured output is mandatory

Every reasoning Crew must produce a known Pydantic artifact through its final
Task.

Examples:

```text
DiscoveryResult
ProductDefinition
RequirementsSpecification
MarketAndGTMStrategy
SolutionArchitecture
AIArchitecture
SecurityArchitecture
QAEvaluationPlan
LeadReview
```

The Flow must consume:

```python
crew_output.pydantic
```

or the structured Pydantic output provided by the final CrewAI Task.

Do not manually parse JSON from:

```python
crew_output.raw
```

Raw output may be retained for debugging or narrative display but must not be
the canonical application artifact.

---

# 7. Proposed Crew Topology

The initial BuildWise Crew topology is:

```text
Discovery Crew
   ↓
Product Definition Crew
   ↓
Requirements Crew
   ↓
Deterministic Specialist Planner
   ↓
Selected Specialist Crews
   ├── Market & GTM Crew
   ├── Solution Architecture Crew
   ├── AI Architecture Crew
   ├── Security Architecture Crew
   └── QA & Evaluation Crew
   ↓
Lead Review Crew
   ↓
Deterministic Blueprint Assembly
```

Specialist planning is not necessarily a Crew.

Blueprint assembly is not necessarily a Crew.

They should remain deterministic when no meaningful LLM reasoning is required.

---

# 8. Crew Inventory

## 8.1 Discovery Crew

### Purpose

Interpret the submitted product idea and produce a structured discovery
assessment.

### Agent

```text
Product Discovery Analyst
```

### Primary Task

```text
Product Discovery Task
```

### Output

```text
DiscoveryResult
```

### Process

```python
Process.sequential
```

### Expected Crew Size

```text
1 Agent
1 Task
```

### Responsibilities

- interpret the product idea
- preserve user intent
- identify known facts
- identify assumptions
- identify unknowns
- identify early risks
- classify capabilities
- assess completeness
- determine whether clarification is needed

### Exclusions

The Crew must not:

- ask the user directly
- pause execution
- resume execution
- define the final product
- create requirements
- select specialists
- design architecture
- persist state

The Flow receives `DiscoveryResult` and decides whether to continue or pause.

---

## 8.2 Product Definition Crew

### Purpose

Convert approved discovery context into a structured product definition.

### Agent

```text
Product Manager
```

### Primary Task

```text
Product Definition Task
```

### Output

```text
ProductDefinition
```

### Process

```python
Process.sequential
```

### Expected Crew Size

```text
1 Agent
1 Task
```

### Responsibilities

- define product vision
- define goals
- define personas
- define features
- prioritize scope
- define MVP
- define exclusions
- define roadmap
- define success metrics
- define product risks

### Input

The Flow supplies the approved structured `DiscoveryResult`.

### Exclusions

The Crew must not:

- create detailed requirements
- select technology
- create architecture
- perform market research
- choose AI models
- define security controls
- define the QA plan

---

## 8.3 Requirements Crew

### Purpose

Convert the approved ProductDefinition into implementation-ready business
requirements.

### Agent

```text
Business Analyst
```

### Primary Task

```text
Requirements Definition Task
```

### Output

```text
RequirementsSpecification
```

### Process

```python
Process.sequential
```

### Expected Crew Size

```text
1 Agent
1 Task
```

### Responsibilities

- define functional requirements
- define non-functional requirements
- define business rules
- define data requirements
- define integrations
- define user journeys
- define acceptance criteria
- define edge cases
- preserve traceability

### Input

The Flow supplies the approved structured `ProductDefinition`.

### Exclusions

The Crew must not:

- redesign the ProductDefinition
- choose technologies
- define service boundaries
- select AI models
- define security architecture
- define the complete test strategy

---

## 8.4 Market & GTM Crew

### Purpose

Produce evidence-aware market and go-to-market recommendations.

### Agent

```text
Market & GTM Strategist
```

### Primary Task

```text
Market & GTM Strategy Task
```

### Output

Use the exact root output model from:

```text
src/buildwise/domain/market_and_gtm.py
```

Expected conceptual output:

```text
MarketAndGTMStrategy
```

### Process

```python
Process.sequential
```

### Expected Crew Size

```text
1 Agent
1 Task
```

### Tools

The Agent may receive official CrewAI tools through the Agent Factory:

- SerperDevTool
- ScrapeWebsiteTool

GitHub search should be attached only when the specific research task requires
repository evidence.

### Responsibilities

- analyze market segments
- choose a primary segment
- research competitors and substitutes
- define positioning
- define pricing hypotheses
- select channels
- propose launch experiments
- identify GTM risks
- preserve evidence provenance

### Execution

Conditional.

The Flow runs this Crew only when:

- market analysis is selected
- GTM planning is required
- explicit user request requires it
- product-commercial decisions justify the cost

### Exclusions

The Crew must not:

- change product scope
- make unsupported market claims
- select implementation technology
- estimate engineering effort
- modify architecture

---

## 8.5 Solution Architecture Crew

### Purpose

Produce the general software solution architecture.

### Agent

```text
Solution Architect
```

### Primary Task

```text
Solution Architecture Task
```

### Output

```text
SolutionArchitecture
```

### Process

```python
Process.sequential
```

### Expected Crew Size

```text
1 Agent
1 Task
```

### Responsibilities

- define system boundaries
- define components
- define component responsibilities
- define integrations
- define data flows
- recommend technologies
- define deployment view
- define scalability strategy
- define reliability strategy
- define observability requirements
- identify architectural risks
- define implementation phases
- estimate architecture-related costs

### Execution

Normally required for a complete BuildWise technical blueprint.

### Exclusions

The Crew must not:

- redefine product scope
- rewrite requirements
- select LLMs
- define RAG
- design AI Agents
- perform the complete threat model
- define the complete QA strategy

---

## 8.6 AI Architecture Crew

### Purpose

Produce the AI-specific architecture when validated AI capabilities exist.

### Agent

```text
AI Architect
```

### Primary Task

```text
AI Architecture Task
```

### Output

```text
AIArchitecture
```

### Process

```python
Process.sequential
```

### Expected Crew Size

```text
1 Agent
1 Task
```

### Inputs

The Flow supplies:

- RequirementsSpecification
- SolutionArchitecture
- relevant capability classifications
- relevant product constraints

### Responsibilities

- justify AI use
- identify deterministic alternatives
- define AI capabilities
- define model requirements
- define model strategy
- define model selections
- define prompt contracts
- define tool policies
- define Agent designs
- define AI workflows
- define RAG where required
- define AI guardrails
- define AI evaluation
- define AI observability
- define human oversight
- define fallback behavior
- define AI risks
- define cost controls

### Execution

Conditional.

The Flow runs this Crew only when the specialist plan selects AI Architecture.

### Dependency

Normally depends on `SolutionArchitecture`.

The AI design must fit into the approved general architecture rather than
redesigning it.

### Exclusions

The Crew must not:

- add AI without a validated need
- redesign the general application
- perform the complete security architecture
- perform the complete QA plan
- approve the final blueprint

---

## 8.7 Security Architecture Crew

### Purpose

Produce the security architecture required by the proposed system.

### Agent

```text
Security Architect
```

### Primary Task

```text
Security Architecture Task
```

### Output

```text
SecurityArchitecture
```

### Process

```python
Process.sequential
```

### Expected Crew Size

```text
1 Agent
1 Task
```

### Inputs

The Flow supplies:

- RequirementsSpecification
- SolutionArchitecture
- AIArchitecture when present
- relevant sensitive-data signals
- relevant regulatory signals

### Responsibilities

- define identity architecture
- define authentication
- define authorization
- define privileged access
- define secrets management
- define encryption
- define data classification
- define retention and deletion
- identify trust boundaries
- identify attack surfaces
- perform threat modeling
- define security controls
- define audit requirements
- identify compliance considerations
- define control validation
- identify residual risk
- define incident-response readiness
- define implementation phases
- estimate security costs

### Execution

Conditional.

The Flow should select this Crew when one or more of the following apply:

- sensitive data
- regulated domain
- multi-tenancy
- privileged integrations
- external actions
- AI tool use
- public-facing APIs
- high-impact business operations
- explicit user request
- high security risk

### Dependency

Depends on `SolutionArchitecture`.

Consumes `AIArchitecture` when AI is present.

### Exclusions

The Crew must not:

- issue formal legal approval
- claim certification
- redesign application architecture
- redesign AI workflows
- accept organizational risk
- approve the blueprint

---

## 8.8 QA & Evaluation Crew

### Purpose

Produce the software-quality and AI-evaluation plan.

### Agent

```text
QA & Evaluation Architect
```

### Primary Task

```text
QA & Evaluation Task
```

### Output

```text
QAEvaluationPlan
```

### Process

```python
Process.sequential
```

### Expected Crew Size

```text
1 Agent
1 Task
```

### Inputs

The Flow supplies:

- RequirementsSpecification
- SolutionArchitecture
- AIArchitecture when present
- SecurityArchitecture when present

### Responsibilities

- define quality objectives
- define the test strategy
- define test suites
- define critical scenarios
- define acceptance tests
- define performance validation
- define reliability validation
- define recovery validation
- define security-control validation
- define AI evaluation
- define evaluation datasets
- define release gates
- define production quality signals
- identify quality risks
- estimate QA costs
- define QA implementation phases

### Execution

Conditional or required depending on BuildWise product policy.

For a build-ready blueprint, QA should normally be selected.

A lightweight product consultation may omit it with an explicit limitation.

### Dependency

QA should run after the specialist artifacts it must validate.

If the QA plan validates Security Architecture, it must run after Security.

If the QA plan validates AI Architecture, it must run after AI.

### Exclusions

The Crew must not:

- redesign requirements
- redesign architecture
- select models
- rewrite security controls
- approve the blueprint

---

## 8.9 Lead Review Crew

### Purpose

Perform the final cross-specialist review.

### Agent

```text
Lead Reviewer
```

### Primary Task

```text
Lead Review Task
```

### Output

```text
LeadReview
```

### Process

```python
Process.sequential
```

### Expected Crew Size

```text
1 Agent
1 Task
```

### Inputs

The Flow supplies:

- DiscoveryResult
- ProductDefinition
- RequirementsSpecification
- SpecialistExecutionPlan
- selected specialist outputs
- current revision history
- session limitations
- cost summary when available

### Responsibilities

- verify artifact completeness
- verify cross-artifact consistency
- verify traceability
- identify contradictions
- identify unsupported assumptions
- identify missing items
- detect unnecessary complexity
- review risks
- review cost consistency
- assess implementation readiness
- request bounded revisions
- decide blueprint readiness

### Execution

Required.

### Exclusions

The Crew must not:

- rewrite specialist outputs
- call specialists directly
- bypass Flow routing
- assemble the final blueprint
- interact with the user directly
- create infinite revision loops

The Flow consumes `LeadReview` and decides whether to:

- assemble the blueprint
- execute targeted revisions
- complete with limitations
- fail the session

---

# 9. Combined Crews Versus Separate Crews

## 9.1 Product Manager and Business Analyst

The initial architecture should keep:

```text
Product Definition Crew
Requirements Crew
```

separate.

Reasons:

- they produce separate artifacts
- they have separate ownership
- requirements may need targeted revisions without regenerating the product
- Flow state should persist each result independently
- failures should be isolated
- cost should be attributable
- review routing should remain bounded

A combined Product Crew may be evaluated later if execution overhead becomes
material.

---

## 9.2 Architect specialists

Do not place Solution, AI, Security, and QA Agents into one large Crew.

They have dependency relationships:

```text
Solution Architecture
   ↓
AI Architecture
   ↓
Security Architecture
   ↓
QA & Evaluation
```

The Flow should coordinate these focused Crews.

This provides better:

- routing
- conditional execution
- failure isolation
- persistence
- retry targeting
- revision targeting
- cost control
- observability

---

## 9.3 Review

The Lead Reviewer should remain in its own Crew.

Do not add every specialist Agent to the Review Crew.

The Lead Reviewer evaluates persisted structured outputs.

Specialists are reinvoked through the Flow only when revisions are requested.

---

# 10. Specialist Planning

Specialist planning should initially be deterministic.

The Flow or an application service should derive the execution plan from
structured signals such as:

- capability classifications
- AI-required flags
- sensitive-data flags
- regulated-domain flags
- integration complexity
- risk severity
- explicit user request
- consultation scope
- execution budget

Example conceptual rules:

```python
if has_ai_capability:
    select(AI_ARCHITECTURE)

if contains_sensitive_data or regulated_domain:
    select(SECURITY_ARCHITECTURE)

if implementation_blueprint_requested:
    select(SOLUTION_ARCHITECTURE)
    select(QA_AND_EVALUATION)

if market_analysis_requested:
    select(MARKET_AND_GTM)
```

The planner may produce the existing `SpecialistExecutionPlan` domain model.

Do not use an LLM Crew for routing when deterministic policy is sufficient.

An LLM planning Task may be introduced later only when specialist selection
requires material ambiguity resolution that cannot be expressed safely through
rules.

---

# 11. Blueprint Assembly

Blueprint assembly should initially be deterministic.

The assembler should:

- consume approved structured artifacts
- create ordered blueprint sections
- preserve references
- include limitations
- include risks
- include recommendations
- include usage information
- render the final Markdown artifact

Do not create a Blueprint Crew solely to concatenate approved outputs.

An LLM narrative-refinement Task may be introduced later only when:

- deterministic assembly produces poor readability
- specialist facts remain unchanged
- no new decisions are introduced
- final output remains validated

---

# 12. Crew Inputs

Crew factories should accept structured domain models.

Example:

```python
def create_solution_architecture_crew(
    *,
    requirements: RequirementsSpecification,
    agent_factory: AgentFactory,
    settings: Settings,
) -> Crew:
    ...
```

For kickoff, structured inputs may be serialized using:

```python
model.model_dump(mode="json")
```

or:

```python
model.model_dump_json()
```

according to the chosen task input contract.

Do not use:

```python
str(model)
```

Do not pass raw Python object representations into prompts.

---

# 13. Crew Outputs

Every Crew execution must have one expected root artifact.

Example:

```python
crew_output = crew.kickoff(inputs=inputs)
```

The Flow should validate:

```python
crew_output.pydantic
```

The Flow must reject a successful-looking execution when:

- no Pydantic output exists
- the output model is wrong
- domain validation fails
- artifact ownership is inconsistent
- required identifiers do not match the session
- the Crew returned only raw Markdown

The Crew layer should not persist the output.

The Flow or application layer persists validated artifacts.

---

# 14. Context Strategy

## 14.1 Within one Crew

Use native CrewAI Task context when multiple Tasks exist in the same Crew:

```python
second_task = Task(
    ...,
    context=[first_task],
)
```

## 14.2 Between Crews

Use Flow state and structured Crew inputs.

Do not pass completed Task objects across independent Crew executions.

```text
Crew A
   ↓
Structured artifact
   ↓
Flow state
   ↓
Crew B inputs
```

## 14.3 Context minimization

Each Crew should receive only the artifacts needed for its responsibility.

Avoid passing:

- full conversation history
- every prior specialist artifact
- unrelated implementation metadata
- API request objects
- database entities
- raw log history

Preserve:

- IDs used for traceability
- relevant requirements
- assumptions
- constraints
- risks
- decisions
- limitations
- relevant evidence references

---

# 15. Process Selection

The default process is:

```python
Process.sequential
```

Use sequential when:

- Task ordering matters
- one output feeds another
- the Crew contains one Task
- deterministic behavior is preferable

Do not use hierarchical process in the initial MVP.

Before adopting hierarchical execution, document:

- manager role
- delegation policy
- task assignment behavior
- cost impact
- termination conditions
- failure behavior
- why the Flow cannot perform the coordination

---

# 16. Memory Policy

Crew memory should be disabled by default unless a specific Crew has a validated
cross-task memory need.

Reasons:

- Flow state already carries canonical artifacts
- hidden memory may reduce reproducibility
- persistent memory can introduce stale context
- memory increases operational complexity
- session isolation must remain clear

Do not enable Crew memory merely because CrewAI supports it.

Potential future use cases include:

- repeated consultations for the same organization
- reusable customer preferences
- long-term domain context
- controlled organizational standards

These should be designed explicitly rather than enabled globally.

---

# 17. Knowledge Policy

Knowledge is optional.

Use CrewAI Knowledge only when an Agent requires semantically retrieved factual
material that is not already present in Flow state.

Potential future examples:

- organization architecture standards
- approved security policies
- domain regulations
- company product guidelines
- reference requirement templates
- internal engineering principles

Do not create empty Knowledge packages.

Do not use Knowledge as a replacement for:

- Task context
- Flow state
- Skills
- tools
- web research

---

# 18. Tool Policy

Tools are attached to Agents through the Agent Factory.

Crew factories must not instantiate official tools directly.

```text
AgentContract.tool_keys
   ↓
ToolRegistry
   ↓
AgentFactory
   ↓
Native Agent
   ↓
Crew
```

Task-level tools may only narrow an Agent's permissions when supported.

Task-level configuration must never broaden the Agent contract’s tool policy.

The initial tool-enabled Crew is:

```text
Market & GTM Crew
```

with controlled access to:

- web search
- website scraping

GitHub search is optional and should be used only for a relevant task.

---

# 19. Skills Policy

Skills are attached through the Agent Factory.

Crew factories must not:

- read `SKILL.md`
- copy Skill content into Task descriptions
- concatenate Skill files into inputs
- duplicate methodology in Crew configuration

The native Agent receives the Skill package.

Task descriptions should remain focused on the current assignment.

---

# 20. Error Handling

## 20.1 Crew construction errors

Fail immediately when:

- required Agent cannot be created
- required Task cannot be created
- Skill is missing
- requested tool cannot be configured
- model provider is unavailable
- required structured input is missing
- Crew configuration is invalid

Do not create partially configured Crews.

## 20.2 Crew execution errors

Crew execution errors should propagate to the Flow.

The Flow applies the Agent contract’s failure policy:

- fail session
- retry then fail
- retry then fallback
- continue with limitation
- request user input

Do not implement separate hidden retry loops inside Crew factories.

## 20.3 Guardrail failures

Allow CrewAI Task guardrails to perform bounded retries.

After retry exhaustion, return or raise a clear failure to the Flow.

---

# 21. Retry Policy

Retries should remain bounded.

Use:

- Task `guardrail_max_retries`
- LLM retry configuration
- Flow-level operation retry only where required

Avoid nested retry multiplication.

Example of a dangerous configuration:

```text
LLM retries: 5
Task guardrail retries: 5
Crew retries: 5
Flow retries: 5
```

The effective number of model calls could become excessive.

Use application settings to keep retry limits consistent.

---

# 22. Execution Limits

Crew construction must respect global settings such as:

- maximum Agent iterations
- maximum execution duration
- maximum model requests
- maximum tool calls
- maximum session token budget
- maximum estimated session cost

CrewAI owns execution behavior.

BuildWise owns policy and enforcement boundaries.

Do not allow one Crew to bypass session-level limits.

---

# 23. Async and Parallel Execution

Parallelism should be controlled by the Flow.

Do not place unrelated specialist Crews into one Crew merely to obtain async
execution.

Potential parallelism must respect dependencies.

A safe conceptual dependency graph is:

```text
Market & GTM ──────────────────────────────┐
                                           │
Solution Architecture                      │
   ↓                                       │
AI Architecture                            │
   ↓                                       │
Security Architecture                      │
   ↓                                       │
QA & Evaluation                            │
                                           │
All selected outputs ──────────────────────┘
                     ↓
                Lead Review
```

Market & GTM may run independently after sufficient product context exists.

Solution Architecture usually precedes AI Architecture.

Security consumes Solution and optionally AI.

QA consumes the selected architectures it must validate.

Correctness is more important than maximum concurrency.

---

# 24. Human-in-the-Loop Boundary

Crews should not use terminal input or directly block for human responses.

Human interaction belongs to the CrewAI Flow.

The Flow may pause for:

- product clarification
- approval
- revision feedback
- consequential action approval
- final acceptance

The Crew receives structured input after the Flow resumes.

Do not use direct human input in a Task unless the API architecture is formally
changed to support it.

---

# 25. Revision Architecture

The Lead Review Crew may return bounded revision requests.

The Flow owns revision routing.

```text
LeadReview
   ↓
Flow reads revision_requests
   ↓
Flow groups requests by RevisionTarget
   ↓
Flow reruns only affected Crew
   ↓
Flow updates artifact
   ↓
Flow reruns Lead Review
```

Do not regenerate all artifacts for one local issue.

Revision limits must be enforced by the Flow.

Crews must remain reusable for both:

- initial generation
- targeted revision

Task factories may accept optional revision instructions.

Revision instructions must be bounded and must not override specialist
ownership.

---

# 26. Observability

Use CrewAI tracing for:

- Crew execution
- Task execution
- Agent reasoning steps
- model calls
- tool calls
- failures

Use structured BuildWise logs for:

- Crew start
- Crew completion
- Crew failure
- session ID
- Flow ID
- Crew key
- artifact type
- duration
- final status
- retry count
- limitations

Do not log:

- secrets
- API keys
- unrestricted prompts
- full sensitive documents
- raw PII
- unredacted tool arguments

The Flow should collect full-run usage metrics after execution.

---

# 27. Crew Naming

Use stable, explicit identifiers.

Recommended Crew keys:

```text
discovery
product_definition
requirements
market_and_gtm
solution_architecture
ai_architecture
security_architecture
qa_evaluation
lead_review
```

Recommended display names:

```text
Product Discovery Crew
Product Definition Crew
Requirements Crew
Market & GTM Crew
Solution Architecture Crew
AI Architecture Crew
Security Architecture Crew
QA & Evaluation Crew
Lead Review Crew
```

Avoid ambiguous names such as:

- Main Crew
- Agent Crew
- Consulting Crew
- Expert Crew
- Final Crew

---

# 28. Proposed Package Structure

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

A shared `base.py` or `factory.py` should be added only when repeated,
meaningful construction behavior appears.

Do not create abstractions preemptively.

The initial implementation may expose one factory function per file.

Example:

```python
def create_discovery_crew(...) -> Crew:
    ...
```

---

# 29. Crew Factory Rules

Every Crew factory must:

- return native `crewai.Crew`
- receive required structured inputs
- receive or use an injected AgentFactory
- create only required Agents
- create only tasks owned by the Crew
- use the appropriate process
- configure bounded execution
- remain free of Flow orchestration
- remain free of persistence
- remain free of API logic
- remain free of blueprint assembly
- contain no manual structured-output parsing

Every Crew factory should be testable without executing a real LLM.

---

# 30. Dependency Injection

Prefer:

```python
def create_solution_architecture_crew(
    *,
    requirements: RequirementsSpecification,
    agent_factory: AgentFactory,
    settings: Settings,
) -> Crew:
    ...
```

Avoid hidden construction through scattered global imports when practical.

Module-level defaults may be provided for application convenience, but test
code must be able to supply:

- fake AgentFactory
- test Settings
- controlled Task factories

Do not mutate global Crew objects.

Create a new Crew for each execution.

---

# 31. Security Requirements

Crew construction must ensure:

- only allowed tools are attached
- Skill paths remain inside the project
- session data is scoped correctly
- tenant identifiers are preserved
- sensitive inputs are minimized
- secrets are never added to prompts
- tool authorization is enforced outside the model
- retries and iterations are bounded
- untrusted web content is treated as data
- retrieved content cannot override system instructions
- consequential actions require Flow-level approval

CrewAI functionality does not replace application security.

---

# 32. Cost Requirements

Each Crew should be attributable by:

- Crew key
- Agent type
- model tier
- task count
- token usage
- tool usage
- execution duration
- estimated cost

The Crew layer should not implement a second cost calculator.

Use CrewAI usage data and the BuildWise session usage ledger.

The Flow aggregates costs across all Crew executions.

---

# 33. Testing Expectations

Crew factories should support unit tests without real model calls.

## Main tests

Test that each Crew:

- returns native `Crew`
- contains the expected Agent
- contains the expected Task
- uses the expected Process
- assigns the correct structured-output model
- uses the expected guardrails
- uses the expected Crew name
- respects verbose settings
- contains no unexpected Agents
- contains no unexpected tools

## Edge cases

Test:

- missing structured input
- disabled Agent contract
- missing Skill
- missing tool credentials
- optional AI artifact absent
- optional Security artifact absent
- wrong Agent supplied
- invalid task configuration
- unsupported process
- duplicate tasks
- revision input without revision target
- selected specialist without required dependency

Do not call live LLMs in unit tests.

---

# 34. Definition of Done

The Crews architecture is approved when:

- Crew boundaries are focused
- the Flow remains the orchestrator
- every Crew has one primary structured output
- every Crew uses native CrewAI components
- no custom Crew runtime is introduced
- no giant all-purpose Crew exists
- process selection is explicit
- hierarchical execution is not used without justification
- delegation is controlled
- tool access remains agent-controlled
- Skills remain agent-controlled
- Knowledge remains optional
- cross-Crew context flows through structured Flow state
- revision routing remains Flow-owned
- blueprint assembly remains deterministic initially
- specialist planning remains deterministic initially
- retries are bounded
- observability uses CrewAI tracing
- cost attribution is possible
- all Crew factories can be tested without live LLM calls
- the architecture is ready for detailed Crew specifications

---

# 35. Next Document

The next document is:

```text
docs/architecture/crews/02_crew_specifications.md
```

It must define each Crew in implementation-ready detail:

- factory signature
- Agent type
- Task factory
- input artifacts
- output model
- process
- dependencies
- optional context
- revision behavior
- execution configuration
- acceptance criteria