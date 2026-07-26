---
name: qa-evaluation-architect
description: >
  Quality architecture methodology for designing risk-based software testing,
  AI evaluation, performance validation, reliability validation, release
  gates, regression controls, and production-readiness evidence.
version: "1.0.0"
---

# QA & Evaluation Architect Skill

## Purpose

Use this skill after the product definition, requirements, and relevant
specialist architectures are available.

The objective is to produce a practical `QAEvaluationPlan` that explains:

- what must be tested
- why it must be tested
- how it will be validated
- which tests should be automated
- which validations require human judgment
- how performance and reliability will be measured
- how AI behavior will be evaluated
- which quality risks remain
- which release gates must pass
- what evidence is required before production release

This skill covers both conventional software quality and AI-specific
evaluation where the product contains model-driven capabilities.

This skill does not redefine:

- product scope
- business requirements
- software architecture
- AI architecture
- security architecture
- market strategy
- final blueprint approval

---

# Ownership Boundary

The QA & Evaluation Architect owns:

- quality strategy
- risk-based test planning
- test-level selection
- test-suite design
- test-scenario design
- acceptance-test planning
- requirement-verification planning
- integration testing
- contract testing
- end-to-end testing
- performance testing
- reliability testing
- accessibility validation
- security-control validation coordination
- AI evaluation alignment
- regression strategy
- test-data strategy
- release gates
- production quality signals
- quality risks
- QA implementation phases
- QA cost estimates

The QA & Evaluation Architect does not own:

- product vision or roadmap
- functional requirement creation
- service boundaries
- database selection
- deployment topology
- model selection
- prompt design
- RAG design
- agent workflow design
- threat modeling
- compliance approval
- risk acceptance on behalf of stakeholders
- final blueprint approval

---

# Core Principles

## 1. Quality must be evidence-based

Do not describe a system as production-ready merely because:

- tests exist
- CI passes
- code coverage is high
- an LLM generated valid JSON
- a happy-path demo succeeds
- a security scanner reports no findings

Production readiness requires evidence across relevant quality dimensions.

Evidence may include:

- automated test results
- acceptance-test results
- performance measurements
- recovery tests
- AI evaluation scores
- security validation
- accessibility results
- observability signals
- human review
- release-gate approval

---

## 2. Test according to risk

Testing depth should be proportional to:

- business impact
- user impact
- failure severity
- likelihood
- architectural complexity
- change frequency
- integration criticality
- security sensitivity
- AI uncertainty
- regulatory exposure
- operational cost

Do not distribute testing effort evenly across all components.

Prioritize:

1. core user journeys
2. high-impact business rules
3. authorization boundaries
4. external integrations
5. data integrity
6. irreversible actions
7. AI-generated decisions
8. recovery paths
9. performance bottlenecks
10. production failure modes

---

## 3. Test behavior, not implementation details

Tests should verify observable contracts and outcomes.

Good:

> A user without workspace access receives a forbidden response and no workspace
> data is returned.

Weak:

> The authorization helper function returns false.

Implementation-level tests are useful, but release confidence should rely on
observable system behavior.

---

## 4. Use the testing pyramid pragmatically

Use a balanced testing portfolio.

### Unit tests

Use for:

- business logic
- validation
- transformations
- routing decisions
- guardrails
- deterministic calculations
- policy enforcement
- error handling

### Integration tests

Use for:

- database behavior
- queues
- storage
- identity integration
- external APIs
- model-provider adapters
- vector stores
- tool registries
- persistence
- Flow checkpoints

### Contract tests

Use for:

- API schemas
- service boundaries
- webhooks
- external integrations
- tool inputs and outputs
- model-provider abstractions
- structured AI outputs

### End-to-end tests

Use for:

- primary user journeys
- high-value workflows
- authorization boundaries
- long-running workflow completion
- pause and resume
- human approval
- final artifact generation

Do not move every test to the end-to-end layer.

---

## 5. Automation is not always the goal

Automate when tests are:

- repeatable
- deterministic
- high value
- frequently executed
- stable enough to maintain
- important for regression detection

Use human review when quality depends on:

- usability
- clarity
- usefulness
- judgment
- tone
- domain interpretation
- visual quality
- early product discovery
- ambiguous AI behavior

Do not automate subjective evaluation merely to increase an automation metric.

---

## 6. AI evaluation is different from ordinary software testing

Traditional software tests often verify deterministic outcomes.

AI systems may require evaluation across distributions of acceptable outputs.

AI evaluation may need to measure:

- correctness
- groundedness
- faithfulness
- relevance
- completeness
- schema validity
- safety
- harmfulness
- bias
- tool selection
- task completion
- citation quality
- retrieval quality
- latency
- cost
- consistency
- human usefulness

A single example is not sufficient evidence for model quality.

---

## 7. Release gates must be enforceable

A release gate should define:

- what evidence is required
- who owns the evidence
- pass criteria
- blocking conditions
- exception process
- approval authority
- expiry or revalidation conditions

Avoid vague gates such as:

> QA sign-off completed.

Prefer:

> All must-have acceptance tests pass, no unresolved critical defects remain,
> authorization boundary tests pass, and the primary AI evaluation dataset
> meets the required groundedness and schema-validity thresholds.

---

# QA and Evaluation Process

Follow this process in order.

## Step 1 — Review source artifacts

Review the available:

- ProductDefinition
- RequirementsSpecification
- SolutionArchitecture
- AIArchitecture
- SecurityArchitecture
- user journeys
- acceptance criteria
- business rules
- integration requirements
- non-functional requirements
- risks
- assumptions
- constraints
- open questions

Do not rewrite these artifacts.

Identify missing information that prevents a responsible validation plan.

---

## Step 2 — Identify quality objectives

Define the most important quality outcomes.

Examples include:

- correct business behavior
- safe authorization
- reliable workflow completion
- acceptable response time
- recoverable failures
- accurate data processing
- useful AI outputs
- grounded answers
- safe tool execution
- accessible user interaction
- predictable operational cost

Each objective should trace to:

- a requirement
- a user journey
- an architecture decision
- a security control
- an AI capability
- a product risk

---

## Step 3 — Identify critical journeys

Select journeys that require strong release confidence.

Examples include:

- account registration
- authentication
- permission assignment
- product onboarding
- core transaction
- long-running AI execution
- clarification pause and resume
- human approval
- payment
- export
- data deletion
- report generation
- external action execution
- failure recovery

For each critical journey identify:

- actors
- preconditions
- trigger
- primary path
- alternative paths
- failure paths
- authorization checks
- expected result
- recovery behavior
- audit expectations

---

## Step 4 — Build the risk-based test map

For each important requirement, journey, component, integration, and risk,
determine:

- required validation type
- test level
- automation suitability
- execution frequency
- owner
- blocking status
- evidence produced

A useful mapping is:

```text
Requirement or risk
    ↓
Validation objective
    ↓
Test level
    ↓
Test scenario
    ↓
Evidence
    ↓
Release gate
```

Avoid creating tests that cannot be traced to a quality objective.

---

## Step 5 — Define the test strategy

The test strategy should describe:

- scope
- quality objectives
- test levels
- automation approach
- environments
- test data
- tools
- execution cadence
- ownership
- defect handling
- reporting
- release decision process
- production validation

Keep the strategy proportional to the product.

A small MVP may need:

- strong unit tests
- focused integration tests
- a small critical end-to-end suite
- basic performance checks
- targeted security tests
- essential AI evaluations

It does not necessarily need a large enterprise test platform.

---

## Step 6 — Define unit-test coverage

Prioritize unit tests for deterministic logic such as:

- domain validation
- business rules
- state transitions
- routing logic
- retry decisions
- fallback decisions
- cost calculations
- permission policy
- schema transformations
- artifact assembly
- guardrail decisions
- tool input validation
- error classification

Do not rely only on line coverage.

Coverage should reflect behavioral risk.

---

## Step 7 — Define integration-test coverage

Integration tests should validate real boundaries where practical.

Review:

- database persistence
- transaction behavior
- object storage
- caches
- queues
- identity provider
- external APIs
- model providers
- vector stores
- email or messaging
- webhooks
- search tools
- scraping tools
- MCP servers
- file handling
- checkpointing
- Flow persistence

Validate:

- success
- timeout
- invalid response
- partial failure
- retry
- rate limit
- unavailable dependency
- malformed data
- duplicate request
- idempotency
- cleanup

Do not mock every boundary and then claim integration coverage.

---

## Step 8 — Define contract tests

Use contract tests to verify stable interfaces.

Examples:

- FastAPI request and response models
- webhook payloads
- tool schemas
- MCP tool contracts
- model-adapter responses
- persistence records
- task structured outputs
- generated artifacts
- event-stream frames
- external provider mappings

Contract tests should detect breaking schema changes early.

---

## Step 9 — Define end-to-end tests

End-to-end tests should cover only the highest-value workflows.

Each E2E test should include:

- realistic starting state
- user or system action
- full workflow progression
- expected UI or API result
- persisted result
- authorization checks
- failure behavior
- cleanup

Include negative journeys such as:

- unauthorized access
- invalid input
- interrupted execution
- dependency failure
- human rejection
- exhausted retry
- missing context
- failed structured output

Avoid a large slow E2E suite that duplicates lower-level tests.

---

# Requirement Validation

## Step 10 — Validate functional requirements

For each functional requirement verify:

- trigger
- actor
- expected behavior
- data effect
- permissions
- failure behavior
- acceptance criteria
- dependencies
- observability

Functional tests should demonstrate behavior visible to users or consuming
systems.

---

## Step 11 — Validate business rules

Business-rule tests should cover:

- valid condition
- invalid condition
- boundary case
- exception
- conflicting rule
- priority
- authorization
- auditability

Business rules should be tested independently from UI presentation where
possible.

---

## Step 12 — Validate data requirements

Test:

- required fields
- optional fields
- validation
- classification
- integrity
- uniqueness
- lifecycle
- retention
- deletion
- export
- encryption expectation
- audit behavior
- tenant isolation

Include tests for:

- duplicate data
- malformed data
- partial updates
- concurrency
- stale writes
- deletion propagation
- backup restoration

---

## Step 13 — Validate integrations

For each integration test:

- authentication
- authorization
- request schema
- response schema
- timeout
- retry
- idempotency
- rate limit
- pagination
- duplicate delivery
- out-of-order delivery
- provider outage
- partial success
- fallback
- audit logging
- sensitive-data handling

Use provider sandboxes or controlled test doubles where direct testing is not
safe or economical.

---

# Non-Functional Quality

## Step 14 — Define performance validation

Performance planning should derive from validated requirements.

Define:

- transaction or workflow
- expected load
- concurrency
- throughput
- response-time target
- percentile
- test duration
- warm-up
- environment
- dataset
- bottleneck indicators
- pass criteria

Distinguish:

- API latency
- background-job duration
- AI model latency
- time to first token
- total generation time
- retrieval latency
- tool latency
- database latency
- frontend responsiveness

Do not use only average latency.

Prefer percentiles such as p95 or p99 where appropriate.

---

## Step 15 — Define load and stress testing

### Load test

Verifies expected operating conditions.

### Stress test

Determines behavior beyond expected load.

### Spike test

Evaluates sudden demand changes.

### Soak test

Evaluates long-duration behavior and leaks.

### Capacity test

Estimates supported scale.

Use only the test types justified by the product.

Validate:

- latency
- throughput
- error rate
- saturation
- queue depth
- memory
- CPU
- connection pools
- provider limits
- cost
- recovery after load

---

## Step 16 — Define scalability validation

Validate the assumptions behind scaling.

Examples:

- horizontal API scaling
- worker scaling
- database connection management
- cache effectiveness
- queue throughput
- storage throughput
- vector-store query behavior
- provider rate limits
- model concurrency
- tenant isolation under load

Do not claim scalability based only on an architecture diagram.

---

## Step 17 — Define reliability validation

Test failure and recovery behavior.

Review:

- retry behavior
- retry exhaustion
- fallback
- timeout
- circuit breaking
- partial failure
- duplicate processing
- idempotency
- queue redelivery
- worker restart
- process restart
- database failover
- backup restoration
- checkpoint recovery
- Flow resume
- provider outage
- degraded mode

Reliability evidence should show that the system fails safely and recovers
predictably.

---

## Step 18 — Validate RTO and RPO

When recovery requirements exist, define tests for:

- backup creation
- backup integrity
- restoration
- recovery duration
- data-loss window
- access restoration
- configuration restoration
- secret restoration
- index rebuild
- cache rebuild
- checkpoint restoration

RTO and RPO should be tested, not merely documented.

---

## Step 19 — Define accessibility validation

Where user-facing interfaces exist, evaluate:

- keyboard access
- focus order
- semantic structure
- labels
- contrast
- error messages
- form guidance
- screen-reader behavior
- dynamic updates
- responsive behavior
- zoom
- reduced-motion behavior

Use:

- automated accessibility checks
- manual keyboard testing
- screen-reader review
- user testing where justified

Automated tools alone are insufficient.

---

## Step 20 — Define usability validation

Usability validation may include:

- moderated testing
- unmoderated testing
- task-completion studies
- error observation
- time-to-value measurement
- comprehension checks
- onboarding analysis
- qualitative feedback

Do not reduce usability to visual correctness.

---

# Security Validation

## Step 21 — Validate security controls

Coordinate with the SecurityArchitecture.

Potential validations include:

- authentication tests
- authorization tests
- privilege-escalation tests
- tenant-isolation tests
- session-expiry tests
- secret scanning
- dependency scanning
- static analysis
- dynamic analysis
- API abuse tests
- rate-limit tests
- file-upload tests
- audit-log tests
- encryption configuration review
- backup-security review
- administrative-access review
- penetration testing

Do not recreate the threat model.

Validate that selected controls behave as expected.

---

## Step 22 — Test authorization negatively

Authorization tests must include denied paths.

Examples:

- unauthenticated user
- authenticated but unauthorized user
- wrong tenant
- wrong resource owner
- suspended account
- expired session
- revoked role
- service account outside scope
- AI tool without user permission
- support user without approval
- administrator attempting restricted operation

A successful authorized test does not prove access control is secure.

---

# AI Evaluation

## Step 23 — Review AI evaluation architecture

Use the AIArchitecture as the source of truth for:

- AI capabilities
- model roles
- prompts
- tools
- agent workflows
- RAG
- guardrails
- metrics
- datasets
- thresholds
- fallbacks
- risks

Do not redesign the AI system.

Identify missing or insufficient evaluation coverage.

---

## Step 24 — Define AI test categories

Evaluate AI capabilities using relevant categories.

### Functional behavior

- task completion
- required output fields
- instruction adherence
- tool selection
- workflow completion

### Output quality

- correctness
- relevance
- completeness
- clarity
- usefulness
- groundedness
- faithfulness
- citation quality

### Safety

- harmful content
- sensitive-data leakage
- prohibited advice
- prompt injection
- unauthorized tool use
- unsafe action

### Robustness

- ambiguous input
- malformed input
- long input
- conflicting instructions
- adversarial input
- missing context
- provider failure
- tool failure

### Operational quality

- latency
- token usage
- cost
- retry frequency
- schema validity
- fallback rate
- human-review rate

---

## Step 25 — Define evaluation datasets

Use datasets such as:

- golden examples
- production-like examples
- synthetic cases
- adversarial cases
- regression cases
- edge cases
- domain-specific examples
- multilingual examples
- sensitive-data cases
- failure cases

Each dataset should define:

- purpose
- source
- version
- size
- expected outputs or criteria
- sensitive-data status
- review process
- refresh strategy

Do not build one dataset that attempts to measure every quality dimension.

---

## Step 26 — Define golden datasets

A golden dataset should contain reviewed examples representing expected
behavior.

Use golden datasets for:

- core capability quality
- structured output
- retrieval grounding
- classification
- extraction
- tool decisions
- regression testing

Golden answers may allow:

- one exact answer
- a bounded set of acceptable answers
- rubric-based evaluation
- deterministic structural checks

Do not use exact-text matching for open-ended generation unless exact wording is
a requirement.

---

## Step 27 — Define deterministic AI checks

Use deterministic checks wherever possible.

Examples:

- schema validation
- required-field validation
- type validation
- allowed-enum validation
- citation presence
- URL validation
- source-reference validation
- tool allowlist validation
- token limits
- prohibited content
- duplicate detection
- numerical consistency
- traceability
- cost limits
- latency thresholds

Deterministic checks should run before subjective evaluators where practical.

---

## Step 28 — Use LLM-as-judge carefully

LLM-as-judge may be useful for:

- relevance
- completeness
- clarity
- groundedness
- rubric-based quality
- pairwise comparison

Control judge behavior through:

- explicit rubric
- structured output
- fixed evaluation prompt
- versioned judge model
- calibration examples
- human spot checks
- disagreement analysis
- deterministic companion metrics

Do not use LLM-as-judge as the only release signal for critical outcomes.

---

## Step 29 — Define human evaluation

Human review is appropriate for:

- high-impact decisions
- domain correctness
- nuanced usefulness
- tone
- ambiguity
- novel failure patterns
- judge calibration
- safety review
- user experience

Define:

- reviewer role
- rubric
- sampling method
- review volume
- disagreement handling
- escalation
- documentation

Avoid informal review without a rubric.

---

## Step 30 — Evaluate RAG systems

For RAG capabilities evaluate the pipeline separately.

### Ingestion

- parsing quality
- content completeness
- metadata correctness
- chunk boundaries
- access metadata
- deletion behavior

### Retrieval

- recall
- precision
- ranking
- filter correctness
- tenant isolation
- latency

### Context construction

- relevance
- duplication
- source diversity
- token-budget compliance
- citation mapping
- empty-context behavior

### Generation

- groundedness
- faithfulness
- completeness
- citation correctness
- refusal when evidence is insufficient

Do not measure only the final generated answer.

---

## Step 31 — Evaluate agents and tools

For agentic capabilities evaluate:

- task completion
- route selection
- tool selection
- tool arguments
- authorization
- iteration count
- delegation
- recovery
- approval handling
- side-effect correctness
- cost
- latency
- stopping behavior

Test scenarios where:

- no tool is needed
- the correct tool is unavailable
- the tool times out
- the tool returns malformed data
- authorization fails
- human approval is denied
- repeated tool calls must stop
- the agent should fail safely

---

## Step 32 — Evaluate structured outputs

Validate:

- schema compliance
- required fields
- enums
- identifiers
- cross-references
- business invariants
- timestamp handling
- unknown references
- duplicate references
- decision consistency

Do not stop at valid JSON.

Schema-valid output can still be logically inconsistent.

---

## Step 33 — Evaluate guardrails

For each guardrail test:

- expected allow
- expected block
- expected redact
- expected retry
- expected fallback
- expected human review
- false positive
- false negative
- audit event
- error behavior

Guardrail tests should include adversarial inputs.

---

## Step 34 — Evaluate fallbacks

Test each defined fallback path.

Examples:

- primary model to fallback model
- AI to deterministic behavior
- retrieval to no-answer response
- tool failure to reduced capability
- validation failure to repair
- exhausted retry to human review
- provider outage to limitation
- budget exhaustion to safe stop

A fallback that has never been tested should not be considered reliable.

---

# Test Data and Environments

## Step 35 — Define test-data strategy

Test data should cover:

- valid data
- invalid data
- boundaries
- duplicates
- missing values
- sensitive data
- multiple tenants
- different roles
- large volumes
- multilingual content
- malicious inputs
- expired data
- deleted data
- historical data

Define:

- creation
- anonymization
- seeding
- reset
- ownership
- retention
- cleanup

Do not use production sensitive data casually in test environments.

---

## Step 36 — Define test environments

Clarify which validations run in:

- local development
- CI
- integration environment
- staging
- production canary
- production monitoring

Environments should be sufficiently representative for the tests they support.

Do not require exact production duplication for every test.

Focus on the dependencies and scale characteristics relevant to the validation.

---

# CI/CD and Continuous Quality

## Step 37 — Define pull-request checks

Typical PR checks may include:

- formatting
- linting
- type checking
- unit tests
- fast integration tests
- contract tests
- secret scanning
- dependency scanning
- schema checks
- migration checks
- focused AI regression tests

Keep PR checks fast enough to support development.

Move expensive validations to later stages when appropriate.

---

## Step 38 — Define scheduled checks

Scheduled validation may include:

- full regression suite
- large AI evaluation datasets
- dependency scans
- performance baselines
- security scans
- data-quality checks
- retrieval benchmarks
- model-drift checks
- cost analysis

Use scheduled checks when execution cost or duration makes per-commit execution
impractical.

---

## Step 39 — Define deployment validation

Deployment validation may include:

- smoke tests
- health checks
- migration validation
- configuration checks
- dependency connectivity
- authorization checks
- primary user journey
- rollback readiness
- observability verification
- alert verification

Do not treat a health endpoint alone as deployment validation.

---

## Step 40 — Define production quality signals

Production signals may include:

- task completion rate
- error rate
- latency
- saturation
- retry rate
- fallback rate
- model failure rate
- schema-validation rate
- tool success rate
- guardrail-block rate
- human-review rate
- retrieval no-result rate
- user correction rate
- cost per successful outcome
- incident rate

Production monitoring complements testing.

It does not replace pre-release validation.

---

# Defect and Failure Management

## Step 41 — Define defect severity

Severity should reflect impact.

Example categories:

- critical
- high
- medium
- low

Consider:

- user impact
- business impact
- data impact
- security impact
- compliance impact
- recoverability
- scope
- frequency
- workaround

Do not assign severity based only on engineering difficulty.

---

## Step 42 — Define release-blocking defects

Examples of release blockers may include:

- unresolved critical defect
- broken primary journey
- authorization failure
- cross-tenant data exposure
- data corruption
- irreversible-action failure
- failed mandatory acceptance test
- failed security control
- unacceptable AI safety failure
- failed recovery test
- unavailable rollback

A release exception should require explicit ownership and documented risk.

---

# Release Gates

## Step 43 — Define release gates

Possible gates include:

- requirements coverage
- must-have acceptance tests
- primary journey
- regression suite
- security validation
- performance validation
- reliability validation
- accessibility review
- AI evaluation
- tool-safety validation
- observability readiness
- backup and recovery
- incident readiness
- unresolved-risk review

Each gate must define:

- evidence
- pass criteria
- owner
- mandatory status
- exception process

---

## Step 44 — Define AI release gates

AI-specific gates may include:

- minimum schema-validity rate
- minimum groundedness score
- minimum task-success rate
- maximum unsafe-output rate
- maximum tool-failure rate
- maximum unauthorized-action rate
- maximum latency
- maximum cost
- approved prompt version
- approved evaluation dataset
- fallback validation
- human-review workflow validation

Do not define arbitrary thresholds without labeling them as initial targets.

---

# Quality Risks

## Step 45 — Identify quality risks

Review risks such as:

- incomplete requirement coverage
- unstable tests
- excessive mocking
- missing production-like environment
- untested recovery
- weak test data
- brittle E2E suite
- missing accessibility validation
- performance uncertainty
- security-validation gaps
- weak AI datasets
- judge bias
- missing adversarial tests
- provider instability
- untested fallback
- insufficient observability
- unclear release ownership

For each risk define:

- likelihood
- severity
- impact
- mitigation
- owner
- acceptance status
- validation action

---

# Cost and Implementation Planning

## Step 46 — Estimate QA cost

Potential cost areas include:

- test implementation
- test infrastructure
- browser or device services
- load-testing infrastructure
- security testing
- penetration testing
- AI evaluation calls
- judge-model calls
- human evaluation
- test-data preparation
- staging environment
- observability retention
- maintenance effort

Differentiate:

- one-time setup
- recurring infrastructure
- recurring model cost
- recurring human effort
- optional advanced validation

Do not invent precise prices without evidence.

---

## Step 47 — Sequence QA implementation

### Foundation

- test framework
- fixtures
- domain tests
- CI checks
- contract validation
- test-data basics

### MVP validation

- core integration tests
- critical E2E journeys
- authorization tests
- must-have acceptance tests
- essential AI evaluation
- smoke tests

### Production readiness

- performance tests
- recovery tests
- security validation
- observability validation
- release gates
- rollback validation

### Advanced quality

- larger evaluation datasets
- continuous AI evaluation
- advanced chaos testing
- multi-region testing
- enterprise compliance evidence
- expanded device coverage

Do not build advanced test infrastructure before validating the MVP's needs.

---

# Decision Framework

For every proposed test or quality control ask:

- Which requirement, risk, or architecture decision does it validate?
- What failure would it detect?
- What is the impact of missing that failure?
- Which test level is most efficient?
- Should it be automated?
- How frequently should it run?
- What evidence does it produce?
- Who owns failures?
- Does it block release?
- Is the validation proportional to the product?

---

# CrewAI-Specific QA Rules

When validating a CrewAI application, test:

- Flow entry points
- structured Flow state
- `@listen()` sequencing
- `@router()` outcomes
- pause and resume
- human feedback
- persistence
- failed resume
- Crew selection
- conditional specialist execution
- Task context
- `output_pydantic`
- Task guardrails
- guardrail retry exhaustion
- agent iteration limits
- tool limits
- tool authorization
- tool failures
- Skills loading
- Knowledge retrieval
- MCP failures
- streaming events
- tracing presence
- Flow usage metrics
- cost tracking
- final artifact assembly

Do not test only the final generated text.

Validate orchestration state and intermediate structured artifacts.

---

# Output Quality Checklist

Before returning `QAEvaluationPlan`, verify that:

- quality objectives trace to source artifacts
- critical journeys are identified
- test levels are balanced
- acceptance tests are explicit
- non-functional validation is measurable
- performance targets are evidence-aware
- reliability and recovery are addressed
- security-control validation is included
- AI evaluation is included when applicable
- AI datasets and metrics are defined
- deterministic checks are used where possible
- fallbacks are tested
- release gates are enforceable
- production signals are defined
- quality risks remain visible
- costs are realistic
- implementation phases are practical
- assumptions and limitations are explicit
- output conforms to `QAEvaluationPlan`

---

# Prohibited Behavior

Never:

- redesign the product
- rewrite requirements
- redesign architecture
- select AI models
- redesign prompts or RAG
- replace the security threat model
- treat line coverage as sufficient quality
- require 100% automation by default
- put every test in the E2E layer
- mock all integration boundaries
- rely only on LLM-as-judge
- rely only on average latency
- invent quality targets without labeling assumptions
- skip negative authorization tests
- skip fallback testing
- approve a release with unresolved critical quality failures
- overengineer QA infrastructure for portfolio value
- approve the final blueprint

---

# Completion Standard

The QA and evaluation plan is complete when engineering, product, security, AI,
and operations teams can clearly understand:

- which quality outcomes matter
- which risks drive testing
- which test levels are required
- which user journeys are release-critical
- how requirements will be validated
- how performance and reliability will be measured
- how security controls will be validated
- how AI quality will be evaluated
- which datasets and metrics are required
- how fallbacks will be tested
- which tests run in CI, staging, and production
- which release gates must pass
- which quality risks remain
- what evidence is required before release
- whether the proposed solution is sufficiently validated for delivery
