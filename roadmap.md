# BuildWise AI Roadmap

## Project Overview

BuildWise AI is a CrewAI-powered product consulting board that transforms vague product ideas into build-ready product blueprints.

The application uses CrewAI to coordinate discovery, product definition, specialist analysis, human clarification, review, and final report generation.

The primary goal is to demonstrate practical CrewAI capabilities through a realistic product workflow while maintaining essential AI engineering practices such as:

- structured inputs and outputs
- input and output validation
- human-in-the-loop execution
- dynamic agent routing
- controlled tool usage
- model routing
- rate limiting
- retries and timeout handling
- token and cost tracking
- structured logging
- CrewAI tracing
- error normalization
- secure handling of user and tool content
- Docker deployment
- automated testing
- GitHub Actions CI

BuildWise AI should remain CrewAI-centric and must not evolve into an unnecessarily large platform.

---

# Core Architecture Principles

## CrewAI Responsibilities

CrewAI Flows own:

- workflow orchestration
- structured Flow state
- conditional routing
- human feedback pauses
- workflow resumption
- specialist selection
- task sequencing
- parallel execution
- targeted refinement
- final workflow completion

CrewAI Crews own:

- product strategy
- business analysis
- market and GTM analysis
- solution architecture
- AI architecture
- security analysis
- QA and evaluation planning
- conflict resolution
- final content review

## Application Responsibilities

FastAPI and supporting services own:

- HTTP request handling
- input validation
- session creation
- state persistence
- rate limiting
- error responses
- tool execution policies
- cost and token tracking
- structured logging
- health checks
- final output delivery

## Agent Handoff Principle

BuildWise AI uses Flow-controlled handoffs.

Agents do not freely create uncontrolled delegation chains.

The preferred handoff pattern is:

```text
Agent completes structured output
        ↓
Output validation
        ↓
Flow stores output in state
        ↓
Flow selects the next agent or task
        ↓
Required fields are passed forward

A limited CrewAI delegation experiment may be introduced inside one bounded Crew only if it adds clear value and does not create unpredictable execution or cost.

Final Agent Set
Required Agents
Discovery Analyst
Product Manager
Business Analyst
Market and GTM Strategist
Solution Architect
Lead Reviewer
Conditional Agents
AI Architect
Security Architect
QA and Evaluation Architect
Non-Agent Components
Input Validator
Input Guardrail Processor
Completeness Evaluator
Clarification Question Generator
Preliminary Capability Classifier
Initial Product Definition Validator
Specialist Planner
Cost Budget Controller
Tool Policy Manager
Tool Output Sanitizer
Agent Output Validator
Output Repair Processor
Cost Aggregator
Lead Review Validator
Blueprint Assembler
Final Output Validator
Markdown Renderer
Session Manager
Usage and Cost Tracker
Error Normalizer
Rate Limiter
Trace Adapter
Structured Logger
Final Workflow
User submits vague product idea
        ↓
FastAPI input validation
        ↓
Input guardrails
        ↓
Session and Flow state creation
        ↓
Discovery Analyst
        ↓
Completeness Evaluator
        ↓
Is enough information available?
        ├── No
        │     ↓
        │ Clarification Question Generator
        │     ↓
        │ Persist Flow state
        │     ↓
        │ Pause Flow
        │     ↓
        │ Human submits answers
        │     ↓
        │ Validate answers
        │     ↓
        │ Resume Flow
        │     └────────────→ Completeness Evaluator
        │
        └── Yes
              ↓
Preliminary Capability Classifier
              ↓
Is early market context required?
        ├── Yes → Early market research task
        └── No
              ↓
Product Manager
              ↓
Business Analyst
              ↓
Initial Product Definition Validator
              ↓
Specialist Planner
              ↓
Cost and token budget check
              ↓
Execute required and conditional specialists
        ├── Market and GTM Strategist
        ├── Solution Architect
        ├── AI Architect, when required
        ├── Security Architect, when required
        └── QA and Evaluation Architect, when required
              ↓
Validate specialist outputs
              ↓
Cost Aggregator
              ↓
Lead Reviewer
              ↓
Are critical conflicts or gaps present?
        ├── Yes
        │     ↓
        │ Targeted specialist refinement
        │     ↓
        │ Output validation
        │     ↓
        │ Lead Reviewer final check
        │
        └── No
              ↓
Approved structured content
              ↓
Blueprint Assembler
              ↓
Final Output Validator
              ↓
Markdown Renderer
              ↓
Persist final result
              ↓
Return build-ready Product Blueprint
Phase 0 — Foundation and CrewAI Setup

Status: 🔵 Not Started

Objective

Create the project foundation required to build, run, test, trace, and deploy the CrewAI application.

The foundation should remain lightweight while supporting production-quality execution.

Scope
Project Setup
Python 3.12
uv project management
source-based package layout
FastAPI application
Pydantic v2
Pydantic Settings
CrewAI
CrewAI Flows
SQLAlchemy
SQLite for local development
PostgreSQL-compatible configuration
Structlog
Tenacity
HTTPX
Pytest
Ruff
Mypy
Initial Repository Structure
buildwise-ai/
├── .github/
│   └── workflows/
├── docs/
├── src/
│   └── buildwise/
│       ├── api/
│       ├── config/
│       ├── domain/
│       ├── agents/
│       ├── crews/
│       ├── flows/
│       ├── tasks/
│       ├── tools/
│       ├── validation/
│       ├── persistence/
│       ├── reporting/
│       ├── observability/
│       └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── roadmap.md
FastAPI Foundation

Build:

application factory
API versioning
request ID middleware
canonical error responses
settings validation
startup and shutdown lifecycle
health endpoint
readiness endpoint
API root endpoint

Initial endpoints:

GET /health
GET /ready
GET /api/v1
CrewAI Foundation

Configure:

CrewAI LLM definitions
CrewAI Flow base configuration
CrewAI tracing
shared agent configuration
environment-based model selection
verbose mode configuration
retry configuration
maximum execution limits
Model Configuration

Support configurable model tiers:

PRIMARY_AGENT_MODEL=
ARCHITECT_MODEL=
LEAD_REVIEWER_MODEL=
FAST_MODEL=

Model tiers:

fast model for classifiers, repair, and question generation
balanced model for most agents
architecture model for complex technical reasoning
strongest model for Lead Reviewer
Structured Logging

Every relevant log should support:

request ID
session ID
Flow ID
trace ID
stage
agent name
task name
tool name
status
duration
retry count
error code
Usage and Cost Skeleton

Create initial models and interfaces for:

input tokens
output tokens
total tokens
estimated cost
agent execution count
tool-call count
retry count
execution duration

The first phase only needs the tracking foundation. Full aggregation is completed later.

Docker Foundation

Add:

multi-stage Dockerfile
non-root runtime user
environment configuration
health check
production ASGI server
.dockerignore
CI Foundation

Add GitHub Actions for:

dependency installation
Ruff lint
Ruff format check
Mypy
Pytest
application import smoke test
Docker image build
Deliverables
runnable FastAPI application
configured CrewAI installation
CrewAI tracing enabled
validated settings
structured logging
initial usage tracking interfaces
health and readiness endpoints
working Docker image
initial CI workflow
complete setup and run instructions
Acceptance Criteria
application starts locally
application starts in Docker
/health returns success
/ready confirms required configuration
Ruff passes
Mypy passes
Pytest passes
CrewAI can execute a minimal smoke-test Flow
logs contain request correlation fields
secrets are not logged

Phase 1 — Domain Models and Agent Contracts

Status: 🔵 Not Started

Objective

Define all canonical structured inputs and outputs before implementing agent behavior.

Every agent, task, classifier, validator, and Flow stage must use strongly typed Pydantic models.

Scope
Session Models

Create:

ConsultingSession
SessionStatus
SessionStage
SessionMetadata
SessionError

Suggested session statuses:

CREATED
PROCESSING
AWAITING_USER_INPUT
RESUMING
REVIEWING
COMPLETED
COMPLETED_WITH_LIMITATIONS
FAILED
Intake Models

Create:

ProductIdeaRequest
ValidatedProductIdea
ClarificationAnswerRequest
ProductIdeaContext
Discovery Models

Create:

DiscoveryResult
KnownFact
Assumption
Unknown
DiscoveryRisk
CompletenessResult
ClarificationQuestion
ClarificationQuestionSet
ClarificationAnswer
CapabilityClassification
Product Models

Create:

ProductDefinition
ProductGoal
UserPersona
ProductFeature
ProductRoadmapItem
ProductRisk
RequirementsSpecification
UserJourney
FunctionalRequirement
NonFunctionalRequirement
BusinessRule
UserStory
AcceptanceCriterion
EdgeCase
IntegrationRequirement
DataRequirement
Specialist Planning Models

Create:

SpecialistType
SpecialistSelection
ExecutionGroup
SpecialistDependency
SpecialistPlan
BudgetDecision
Specialist Output Models

Create:

MarketAndGTMReport
MarketCompetitor
MarketTrend
PositioningRecommendation
GTMPlan
SolutionArchitecture
ArchitectureComponent
ArchitectureDecision
TechnologyRecommendation
TechnicalCostEstimate
AIArchitecture
AIUseCase
ModelStrategy
RAGStrategy
AgentStrategy
AIEvaluationRequirement
SecurityArchitecture
Threat
SecurityControl
TrustBoundary
QAEvaluationPlan
TestStrategy
EvaluationMetric
ReleaseGate
Review and Reporting Models

Create:

CostSummary
LeadReview
RevisionRequest
ProductBlueprint
BlueprintSection
SourceReference
UsageSummary
Canonical Flow State

Create a structured CrewAI Flow state containing:

identifiers
original idea
discovery result
clarification state
capability classification
product definition
requirements
specialist plan
specialist outputs
cost summary
review result
final blueprint
usage metadata
retry counters
clarification round
refinement round
warnings
errors
Agent Contract Definitions

Define for every agent:

role
mission
goal
capabilities
skills
responsibilities
input model
output model
invocation conditions
allowed tools
forbidden actions
model tier
failure behavior
downstream handoff targets
Deliverables
complete Pydantic domain layer
canonical Flow state
agent contract registry
model serialization tests
validation tests
example fixtures for each major model
Acceptance Criteria
all models pass Mypy
invalid inputs produce clear validation errors
all agent outputs can be serialized
every agent has a distinct contract
no agent has undefined or overlapping ownership
the removed Engineering Lead role does not exist
cost-related fields are distributed across Product, Architecture, AI, QA, Security, and GTM outputs

Phase 2 — Discovery Flow

Status: 🔵 Not Started

Objective

Build the first complete CrewAI Flow that converts vague user input into structured discovery context and decides whether clarification is required.

Scope
Discovery Analyst Agent

Implement:

CrewAI Agent configuration
discovery task
structured DiscoveryResult output
prompt instructions
output validation
one repair attempt

The agent should:

interpret the idea
identify the problem
classify the domain
identify target users
extract known facts
generate assumptions
identify unknowns
identify risk signals
avoid premature architecture recommendations
Completeness Evaluator

Implement as a focused classifier rather than a full specialist agent.

Evaluate:

product goal
primary users
core workflow
business objective
AI expectation
data requirements
integrations
security sensitivity
expected scale
timeline
budget
critical constraints

Return:

completeness score
blocking unknowns
non-blocking unknowns
proceed decision
clarification decision
decision rationale
Clarification Question Generator

Implement as a focused LLM task using the fast model.

Rules:

ask three to five questions
prioritize high-impact unknowns
avoid previously answered questions
avoid technical questions the user should not need to answer
support text, choice, boolean, number, and multi-select answers
explain why each question matters
identify required and optional questions
Preliminary Capability Classifier

Implement:

market research flag
AI relevance flag
security sensitivity flag
regulated-domain flag
external-integration flag
autonomous-action flag
QA complexity flag
initial risk level

Use deterministic rules where possible and a fast model only for semantic classification.

Discovery Output Validation

Validate:

required fields
assumption labeling
unknown completeness
confidence bounds
no architecture recommendations
no invented confirmed facts
no empty question text
no duplicated clarification questions
CrewAI Flow Routes

Implement routes:

start_discovery
    ↓
validate_discovery
    ↓
evaluate_completeness
    ├── proceed
    ├── request_clarification
    └── continue_with_assumptions
Deliverables
Discovery Analyst agent
Discovery task
Completeness Evaluator
Clarification Question Generator
Preliminary Capability Classifier
structured Discovery Flow
validation and repair behavior
unit and integration tests
Acceptance Criteria
vague ideas produce meaningful discovery results
incomplete ideas produce targeted clarification questions
sufficiently clear ideas proceed automatically
assumptions remain explicit
no more than the configured question limit is generated
repeated questions are prevented
Flow routing is visible in CrewAI tracing
invalid discovery output receives at most one repair attempt
Phase 3 — Human Clarification and Persistence

Status: 🔵 Not Started

Objective

Support real human-in-the-loop execution by pausing the CrewAI Flow, persisting state, accepting user answers, and resuming from the saved state.

Scope
Session Persistence

Persist:

session identifiers
session status
current Flow stage
original idea
discovery result
questions
answers
clarification round
assumptions
capability classification
usage metadata
errors

Use:

SQLite for local development
PostgreSQL-compatible SQLAlchemy models
Human Feedback Lifecycle

Implement:

Clarification required
        ↓
Persist questions and Flow state
        ↓
Mark session AWAITING_USER_INPUT
        ↓
Return questions through API
        ↓
User submits answers
        ↓
Validate answers
        ↓
Update confirmed facts and assumptions
        ↓
Resume Flow
        ↓
Re-run completeness evaluation
Clarification Limits

Implement:

maximum clarification rounds
maximum questions per round
duplicate-answer protection
stale-answer protection
session-state conflict detection
continue-with-assumptions fallback
API Endpoints

Implement:

POST /api/v1/consultations
GET /api/v1/consultations/{session_id}
POST /api/v1/consultations/{session_id}/answers
API Responses

The consultation API should return:

session ID
status
current stage
pending questions
warnings
progress summary
created timestamp
updated timestamp
State Conflict Handling

Return normalized errors for:

invalid session
already-completed session
answers submitted in the wrong stage
duplicated answer submission
expired or invalid question IDs
malformed answer values
Deliverables
session database models
session repository
session service
persisted CrewAI Flow state
pause and resume behavior
clarification APIs
session status API
human-feedback tests
Acceptance Criteria
Flow can pause safely
session state survives application restart
answers can resume the correct Flow
invalid answer submissions are rejected
clarification rounds cannot exceed the configured limit
unresolved values become explicit assumptions
session transitions are traced and logged
repeated answer submission does not duplicate execution
Phase 4 — Product Definition Crew

Status: 🔵 Not Started

Objective

Build the Product Manager and Business Analyst Crew that converts validated discovery context into an initial buildable product definition.

Scope
Optional Early Market Context

Before the Product Manager executes:

inspect CapabilityClassification
run an early market research task only when needed
provide a short validated context document
do not generate the full GTM report yet

Early research may include:

common market expectations
notable current competitors
current category trends
critical differentiation pressures
Product Manager Agent

Implement:

product strategy task
structured ProductDefinition output
explicit MVP and future scope
product roadmap
success metrics
delivery assumptions
product risks
team capability assumptions
business dependencies

The Product Manager should not:

select detailed technologies
define technical architecture
invent market evidence
produce unsupported delivery estimates
Business Analyst Agent

Implement:

requirements task
structured RequirementsSpecification
user journeys
functional requirements
non-functional requirements
business rules
user stories
acceptance criteria
edge cases
data requirements
integration requirements
Crew Execution

The Product Crew should demonstrate meaningful CrewAI collaboration.

Recommended initial process:

Product Manager task
        ↓
Business Analyst task receives ProductDefinition as context
        ↓
Aggregate Initial Product Definition

Use explicit task context rather than unrestricted delegation.

Initial Product Definition Validation

Validate:

Product Manager and Business Analyst consistency
MVP scope
requirement traceability
acceptance-criteria quality
assumptions
duplicate or conflicting requirements
untestable requirements
unsupported market claims

Allow:

one targeted repair attempt
partial completion only when non-critical sections fail
Deliverables
Product Manager agent
Business Analyst agent
Product Crew
structured tasks
Initial Product Definition
Product Definition Validator
validation and repair tests
Acceptance Criteria
output clearly defines what should be built
MVP is separated from future scope
requirements are specific and testable
acceptance criteria map to requirements
assumptions remain visible
Product Manager and Business Analyst outputs do not conflict
Crew execution is visible in tracing
invalid structured outputs receive bounded repair
Phase 5 — Specialist Planning and Routing

Status: 🔵 Not Started

Objective

Dynamically select only the specialists required for the product and create a cost-aware execution plan after the initial product definition exists.

Scope
Specialist Planner

Use:

DiscoveryResult
CapabilityClassification
ProductDefinition
RequirementsSpecification
session cost budget
session token budget

Determine:

selected specialists
skipped specialists
selection reasons
execution dependencies
parallel execution groups
required tool access
estimated execution depth
cost category
degraded-mode behavior
Required Specialist Execution

Always include:

Market and GTM Strategist
Solution Architect
Lead Reviewer

The Product Manager and Business Analyst have already executed before the planner.

Conditional Specialist Selection

Select AI Architect when:

AI is central to the product
AI may materially improve the product
RAG, agents, model selection, or generative features require design
AI-generated outputs affect users

Select Security Architect when:

sensitive data is processed
regulated workflows exist
external integrations exist
autonomous actions exist
abuse risks are significant
AI tool execution affects external systems

Select QA and Evaluation Architect when:

AI outputs require evaluation
reliability expectations are significant
complex integrations exist
safety or adversarial testing is required
acceptance criteria require deeper test design
Execution Graph

Example:

Initial Product Definition
        ↓
Specialist Planner
        ↓
Parallel Group 1
├── Market and GTM Strategist
├── Solution Architect
└── AI Architect, if selected
        ↓
Parallel Group 2
├── Security Architect, if selected
└── QA and Evaluation Architect, if selected

Security and QA may require outputs from Architecture or AI analysis.

Cost Budget Controller

Implement:

maximum session tokens
maximum estimated cost
maximum agent executions
maximum tool calls
maximum retries
optional specialist reduction
reduced research depth
degraded execution mode

The final review must remain preserved whenever possible.

Model Routing

Route models based on:

agent role
product complexity
reasoning complexity
cost budget
repair versus primary execution

Example:

Fast model:
- classification
- routing support
- output repair

Balanced model:
- Product Manager
- Business Analyst
- Market and GTM
- Security
- QA

Architecture model:
- Solution Architect
- AI Architect

Strongest model:
- Lead Reviewer
Deliverables
Specialist Planner
Specialist Plan model
model router
cost budget controller
conditional routes
parallel execution groups
routing tests
Acceptance Criteria
planner runs after Initial Product Definition
unnecessary specialists are skipped
selection reasons are recorded
dependencies are respected
parallel groups are valid
cost constraints can reduce optional work
model selection is configuration-driven
routing decisions appear in CrewAI tracing
mandatory review cannot be accidentally skipped
Phase 6 — Specialist Crews and Controlled Tools

Status: 🔵 Not Started

Objective

Implement the required and conditional specialist agents, controlled tools, structured outputs, and parallel CrewAI execution.

Scope
Market and GTM Strategist

Produce:

market context
competitors
trends
market expectations
target segment
ideal customer profile
positioning
differentiation
messaging
pricing options
acquisition channels
launch strategy
early-adopter strategy
sales motion
activation strategy
retention considerations
GTM milestones
GTM metrics
GTM risks
GTM cost assumptions
sources
evidence limitations
Solution Architect

Produce:

architecture overview
components
component responsibilities
API boundaries
data flows
integrations
persistence design
deployment architecture
reliability strategy
technology recommendations
trade-offs
technical feasibility
technical dependencies
build-versus-buy decisions
technical debt risks
implementation phases
infrastructure requirements
technical cost estimate
scaling cost drivers
operational cost drivers
AI Architect

When selected, produce:

AI suitability assessment
AI use cases
deterministic versus AI boundaries
model requirements
model strategy
RAG strategy
agent strategy
prompt strategy
structured output strategy
tool strategy
AI guardrails
human review points
evaluation requirements
fallback strategy
AI cost estimate
AI cost controls
AI risks
AI observability requirements
Security Architect

When selected, produce:

threat model
trust boundaries
sensitive data inventory
attack surfaces
product-security controls
AI-security controls
prompt-injection controls
indirect prompt-injection controls
tool security
privacy considerations
abuse scenarios
security testing requirements
residual risks
QA and Evaluation Architect

When selected, produce:

test strategy
unit test scope
integration test scope
end-to-end test scope
contract testing
AI evaluation dimensions
evaluation datasets
quality metrics
safety tests
prompt-injection tests
tool-failure tests
fallback tests
regression strategy
release gates
acceptance traceability
Tool Layer

Provide controlled tools for:

current market web search
webpage retrieval
competitor research
official technical documentation lookup
current provider capability lookup
current pricing lookup
approved security references

Every tool must include:

typed input schema
agent-specific allowlist
timeout
bounded retries
maximum result count
maximum output size
source metadata
error normalization
tool-call logging
usage tracking
output sanitization
Tool Security

Treat all retrieved content as untrusted data.

Implement:

prompt-injection detection
instruction stripping
output size limits
source preservation
secret redaction
content sanitization
no arbitrary code execution
no unrestricted filesystem access
no uncontrolled network access
Parallel Execution

Use CrewAI capabilities to run independent specialist tasks in parallel.

Do not run tasks in parallel when one depends on another output.

Structured Output Validation

Every specialist result must pass:

Pydantic validation
required field validation
assumption checks
evidence checks
source checks
placeholder detection
risk and mitigation checks
requirement alignment checks

Allow one targeted repair attempt.

Deliverables
Market and GTM Strategist
Solution Architect
AI Architect
Security Architect
QA and Evaluation Architect
specialist tasks
specialist Crews
tool implementations
tool policies
parallel execution
structured output validation
tool and specialist tests
Acceptance Criteria
required specialists always execute
conditional specialists execute only when selected
external research includes sources
agents cannot access unauthorized tools
tool content cannot override instructions
parallel execution respects dependencies
specialist output validation is enforced
partial specialist failure can be recorded safely
CrewAI tracing shows task, agent, and tool execution
cost and token usage are tracked per specialist
Phase 7 — Review, Refinement, Cost Synthesis, and Blueprint Generation

Status: 🔵 Not Started

Objective

Aggregate cost information, resolve conflicts across all specialist outputs, perform one bounded refinement cycle, and create the final build-ready Product Blueprint.

Scope
Cost Aggregator

Aggregate structured cost inputs from:

Product Manager
Market and GTM Strategist
Solution Architect
AI Architect
Security Architect
QA and Evaluation Architect

Produce:

estimate confidence
one-time cost categories
recurring cost categories
engineering effort category
infrastructure costs
AI usage costs
third-party service costs
security costs
testing and evaluation costs
GTM costs
scaling cost drivers
cost optimization opportunities
cost assumptions
limitations

The Cost Aggregator should be deterministic.

It must not invent exact cost numbers unsupported by specialist evidence.

Lead Reviewer

Use the strongest configured reasoning model.

Review:

requirement coverage
requirement traceability
Product Manager and Business Analyst consistency
architecture alignment
AI suitability
AI evaluation coverage
security coverage
market and GTM coverage
cost coverage
unsupported assumptions
unrealistic recommendations
overengineering
missing risks
unresolved specialist conflicts
MVP feasibility

Produce:

approval status
contradictions
missing requirements
unsupported assumptions
product issues
architecture issues
AI issues
security issues
GTM issues
cost issues
overengineering findings
revision requests
responsible specialist
unresolved risks
limitations
final recommendation
Controlled Refinement

When refinement is required:

select only the responsible specialist
send a targeted revision request
do not restart the full Crew
validate the revised output
update Flow state
re-run Lead Reviewer final check
allow a maximum of one refinement round

If issues remain after the maximum refinement:

approve with limitations when safe
clearly expose unresolved risks
fail only when the final artifact would be unusable or unsafe
Blueprint Assembler

Implement as a deterministic processor.

Assemble:

executive summary
original idea
confirmed facts
assumptions
open questions
market analysis
product vision
target users
MVP scope
future scope
user journeys
functional requirements
non-functional requirements
architecture
AI design
security design
QA and evaluation plan
GTM plan
cost analysis
feasibility summary
implementation roadmap
risks
trade-offs
final recommendation
sources
limitations
usage metadata
trace metadata

The assembler must not create new recommendations.

Final Output Validator

Validate:

all required sections exist
no unresolved placeholders remain
confirmed facts are preserved
assumptions are visible
architecture supports requirements
AI design includes evaluation and fallback
security risks include controls
GTM plan exists
costs are labeled as estimates
failed specialist analyses are disclosed
sources exist for researched claims
Lead Reviewer approval exists
Markdown Renderer

Render:

structured JSON blueprint
formatted Markdown report
cost summary tables
roadmap
risk tables
source references
warnings and limitations
Final APIs

Implement:

GET /api/v1/consultations/{session_id}/blueprint
GET /api/v1/consultations/{session_id}/report
GET /api/v1/consultations/{session_id}/usage
Deliverables
Cost Aggregator
Lead Reviewer agent
review task
targeted refinement Flow
Lead Review Validator
Blueprint Assembler
Final Output Validator
Markdown Renderer
final report APIs
review and reporting tests
Acceptance Criteria
cost inputs are aggregated from appropriate specialists
Lead Reviewer uses structured outputs rather than raw transcripts
conflicts are clearly reported
no more than one refinement round occurs
targeted refinement executes only the responsible specialist
final blueprint includes all required sections
final report can be returned as JSON and Markdown
partial failures and limitations are visible
final session usage and trace metadata are available
Phase 8 — Deployment, CI, Testing, and Frontend Contract

Status: 🔵 Not Started

Objective

Complete production hardening, automated testing, deployment packaging, and the backend contract required by the separately developed frontend.

Scope
API Rate Limiting

Implement lightweight public API protection:

per-IP request limit
consultation creation limit
answer submission limit
active-session limit
tool-call limit
provider retry limit
maximum request size
configurable limits

Use an in-memory limiter for the initial single-instance deployment.

Do not introduce Redis unless multi-instance deployment requires it.

Retry and Timeout Policies

Configure:

Operation	Policy
Temporary LLM failure	Bounded retry with backoff
LLM rate limit	Bounded retry with backoff
Tool timeout	One retry
Invalid structured output	One repair attempt
Unsafe input	No retry
Invalid configuration	No retry
Session conflict	No retry
Refinement	Maximum one round
Error Handling

Normalize:

request validation errors
guardrail rejection
rate limits
session not found
session state conflict
provider errors
tool errors
tool timeouts
output validation errors
persistence errors
internal errors

Canonical error response:

{
  "code": "SPECIALIST_EXECUTION_FAILED",
  "message": "The requested specialist analysis could not be completed.",
  "recoverable": true,
  "stage": "specialist_execution",
  "session_id": "session-id",
  "request_id": "request-id"
}
Usage and Cost Tracking

Complete tracking for:

model
provider
agent
task
tool
input tokens
output tokens
estimated cost
retries
execution duration
session total
degraded-mode decisions
Metrics Summary

Provide a lightweight endpoint:

GET /metrics/summary

Return:

completed consultations
failed consultations
consultations awaiting user input
average duration
average token usage
average estimated cost
tool failure count
validation failure count
model usage summary

No external monitoring platform is required.

Testing
Unit Tests

Cover:

domain models
validators
classifiers
routing rules
cost aggregation
tool policies
report assembly
error normalization
Agent and Task Tests

Cover:

structured output parsing
mocked agent outputs
repair logic
agent contract enforcement
forbidden tool access
conditional specialist selection
Flow Tests

Cover:

complete input path
clarification path
maximum clarification path
early market research path
conditional specialist paths
budget-reduced path
specialist failure path
refinement path
completed-with-limitations path
Integration Tests

Cover:

API to Flow execution
persistence and resume
final report retrieval
usage retrieval
Docker startup
health and readiness checks
Small Quality Scenario Set

Create a compact set of representative scenarios:

vague SaaS idea
clear non-AI product
AI support product
sensitive HR product
regulated healthcare-related idea
marketplace product
internal automation tool

Validate:

clarification relevance
specialist selection
required section completeness
assumption visibility
architecture presence
GTM presence
cost summary presence
no uncontrolled agent execution

This is not a separate evaluation platform.

It is a focused regression suite for the CrewAI workflow.

Docker

Finalize:

multi-stage Dockerfile
non-root user
health check
startup command
environment settings
build cache
minimal runtime dependencies
Docker Compose

Support local development with:

BuildWise API
PostgreSQL

SQLite may remain available for simplified local execution.

GitHub Actions

Create workflows for:

Continuous Integration
install uv
install dependencies
Ruff lint
Ruff format check
Mypy
Pytest
coverage
import smoke test
Docker Validation
build image
start container
call /health
call /ready
stop container
Security Checks
dependency audit
secret scanning where available
Python static security checks
container image scanning
Frontend API Contract

Document:

request schemas
response schemas
error schemas
session states
progress states
clarification question formats
blueprint format
Markdown report behavior
usage summary format
Frontend Integration Requirements

The frontend will need:

Idea Submission
product idea input
optional additional context
submit action
Clarification Workflow
question rendering
answer controls
required and optional questions
answer submission
validation errors
Progress View
session status
current stage
selected specialists
completed specialists
warnings
partial failures
Blueprint Viewer
executive summary
tabbed or sectioned blueprint
architecture
AI strategy
security
QA
GTM
cost analysis
roadmap
risks
sources
limitations
Export
Markdown report retrieval
JSON blueprint retrieval
Deliverables
rate limiting
completed retry policies
timeout policies
normalized errors
complete usage tracking
metrics summary endpoint
unit tests
Flow tests
integration tests
quality scenario suite
production Docker image
Docker Compose
GitHub Actions
frontend API contract
deployment instructions
Acceptance Criteria
all automated checks pass
public endpoints are rate limited
retries are bounded
provider and tool failures are normalized
session costs are visible
Docker health check passes
CI validates code and container
human-feedback state survives restart
frontend contract is complete
representative workflow scenarios pass
no unnecessary distributed infrastructure is introduced
Final API Scope
GET  /health
GET  /ready
GET  /metrics/summary

POST /api/v1/consultations
GET  /api/v1/consultations/{session_id}
POST /api/v1/consultations/{session_id}/answers

GET  /api/v1/consultations/{session_id}/blueprint
GET  /api/v1/consultations/{session_id}/report
GET  /api/v1/consultations/{session_id}/usage
Final Phase Summary
Phase	Name	Primary CrewAI Value
0	Foundation and CrewAI Setup	CrewAI configuration, tracing, model setup
1	Domain Models and Agent Contracts	Structured state and outputs
2	Discovery Flow	Flow routing, classification, adaptive discovery
3	Human Clarification and Persistence	Pause, persist, resume, human feedback
4	Product Definition Crew	Sequential Crew collaboration
5	Specialist Planning and Routing	Dynamic routing, model routing, cost-aware planning
6	Specialist Crews and Controlled Tools	Parallel agents, tools, structured outputs
7	Review, Refinement, Cost Synthesis, and Blueprint Generation	Strong reviewer, bounded reflection, final synthesis
8	Deployment, CI, Testing, and Frontend Contract	Production readiness and integration
Out of Scope

BuildWise AI will not include:

authentication
user account management
organizations
multi-tenancy
RBAC
billing
distributed queues
Kubernetes
microservice decomposition
vector databases
long-term semantic memory
external observability platforms
Prometheus
Grafana
LangSmith
a separate evaluation platform
a separate guardrails platform
a separate validation platform
a plugin system
unlimited autonomous delegation
unlimited refinement loops
unrestricted web access
arbitrary code execution
enterprise compliance automation
Project Completion Criteria

BuildWise AI is complete when:

a user can submit a vague product idea
the Discovery Flow interprets the idea
the system asks clarification questions when required
the Flow pauses and resumes correctly
the Product Crew generates an initial product definition
the Specialist Planner selects relevant specialists
specialist tasks execute with correct dependencies
approved tools are controlled and traceable
all agent outputs use structured schemas
agent failures are handled safely
costs and token usage are tracked
the Lead Reviewer resolves conflicts
one targeted refinement round is supported
a complete Product Blueprint is generated
the report includes product, market, architecture, AI, security, QA, GTM, cost, and roadmap sections
the blueprint is available as JSON and Markdown
the application runs locally and in Docker
CI passes linting, type checking, tests, and container validation
the frontend has a stable API contract