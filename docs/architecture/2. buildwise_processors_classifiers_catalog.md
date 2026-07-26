# BuildWise AI — Processors, Classifiers, Validators, Aggregators, and Services

## 1. Purpose

This document defines all non-agent runtime components in BuildWise AI.

These components handle deterministic logic, validation, routing, safety, persistence, cost control, report assembly, and operational concerns.

Not every function should be implemented as an agent.

Using deterministic processors and classifiers where possible:

- reduces cost
- improves reliability
- improves testability
- simplifies tracing
- prevents unnecessary LLM calls
- reduces output variability
- keeps agent responsibilities clear

---

# 2. Component Set Summary

| Component | Category | Main Purpose | Model Use | Tools |
|---|---|---|---|---|
| Input Validator | Validator | Validate API payload and constraints | None | None |
| Input Guardrail Processor | Guardrail | Detect unsafe or malicious input | Deterministic first, optional fast model | Secret and pattern detectors |
| Completeness Evaluator | Classifier | Decide whether discovery information is sufficient | Fast model or hybrid | None |
| Clarification Question Generator | Processor or focused LLM task | Generate high-value questions | Fast model | None |
| Preliminary Capability Classifier | Classifier | Detect market, AI, security, and QA needs | Fast model or deterministic rules | None |
| Initial Product Definition Validator | Validator | Validate PM and BA outputs | Deterministic plus optional fast model | None |
| Specialist Planner | Planner | Select specialists and dependencies | Balanced model or hybrid rules | None |
| Cost Budget Controller | Processor | Enforce token, tool, and session budgets | None | Usage metadata |
| Tool Policy Manager | Service | Restrict and validate tool execution | None | External tools |
| Tool Output Sanitizer | Guardrail | Treat tool results as untrusted data | Deterministic plus optional fast model | None |
| Agent Output Validator | Validator | Validate schemas and domain rules | Deterministic plus optional fast model | None |
| Output Repair Processor | Processor | Repair one invalid structured output | Fast model | None |
| Cost Aggregator | Aggregator | Combine product, technical, AI, security, QA, and GTM costs | Deterministic | None |
| Lead Review Validator | Validator | Validate reviewer output | Deterministic | None |
| Blueprint Assembler | Processor | Assemble approved structured outputs | None | None |
| Final Output Validator | Validator | Validate final blueprint completeness and consistency | Deterministic plus optional fast model | None |
| Markdown Renderer | Renderer | Convert blueprint to Markdown | None | None |
| Session Manager | Service | Manage session lifecycle and status | None | Database |
| Flow State Repository | Repository | Persist and restore Flow state | None | Database |
| Usage and Cost Tracker | Service | Track tokens, costs, retries, and tool calls | None | Runtime metadata |
| Error Normalizer | Service | Convert failures into canonical errors | None | None |
| Rate Limiter | Service | Protect public API and session budget | None | In-memory or Redis |
| Trace Adapter | Service | Connect application events with CrewAI tracing | None | CrewAI tracing |
| Structured Logger | Service | Produce correlated JSON logs | None | Structlog |
| Health and Readiness Service | Service | Report application and dependency health | None | Database/provider checks |

---

# 3. Input and Safety Components

## 3.1 Input Validator

### Type

Deterministic validator.

### Main Tasks

- validate request schema
- reject empty product ideas
- enforce maximum input length
- validate optional context
- validate preferred output format
- validate answer payloads
- validate session identifiers
- reject malformed requests

### Input

- API request payload

### Output

`ValidatedIdeaInput` or a normalized validation error.

### Delegation From

- FastAPI endpoint

### Delegation To

- Input Guardrail Processor
- Session Manager

### Model

None.

### Tools

- Pydantic v2

### Failure Behavior

Return HTTP 422 with canonical validation details.

---

## 3.2 Input Guardrail Processor

### Type

Guardrail processor.

### Main Tasks

- detect prompt-injection patterns
- detect secret and credential patterns
- detect oversized or abusive input
- detect unsupported harmful requests
- redact sensitive values from logs
- classify whether the request can safely continue

### Input

- ValidatedIdeaInput

### Output

`InputGuardrailResult`

Recommended fields:

- allowed
- risk_level
- detected_patterns
- redactions
- rejection_reason
- warnings

### Delegation From

- Input Validator

### Delegation To

- Session Manager when allowed
- Error Normalizer when rejected

### Model

Deterministic checks first.

Optional fast model only for semantic risk classification.

### Tools

- regex-based prompt-injection patterns
- secret detection library or custom detector
- payload-size checks
- allowlist and denylist rules

### Failure Behavior

Fail closed for high-risk secrets, malicious injection, or unsupported requests.

---

# 4. Discovery Support Components

## 4.1 Completeness Evaluator

### Type

Classifier.

### Main Tasks

Evaluate whether the system has enough information to continue.

Dimensions:

- product goal
- primary users
- main workflow
- business objective
- data requirements
- AI expectations
- integrations
- security sensitivity
- expected scale
- timeline
- budget
- critical constraints

### Input

- DiscoveryResult
- previous clarification answers
- clarification round
- maximum round limit

### Output

`CompletenessResult`

Recommended fields:

- completeness_score
- missing_dimensions
- blocking_unknowns
- non_blocking_unknowns
- proceed
- clarification_required
- reason

### Delegation From

- Discovery Analyst

### Delegation To

- Clarification Question Generator when incomplete
- Preliminary Capability Classifier when complete
- assumption fallback when maximum rounds are reached

### Model

Fast, low-cost model or a hybrid of deterministic scoring and a fast model.

### Tools

None.

### Failure Behavior

Use deterministic fallback scoring.

---

## 4.2 Clarification Question Generator

### Type

Focused LLM processor.

It does not need to be a long-lived independent CrewAI agent.

### Main Tasks

- generate three to five high-value questions
- avoid duplicate questions
- prioritize architecture-changing unknowns
- make questions understandable to non-technical users
- define answer type
- provide options when appropriate
- explain why each question matters

### Input

- DiscoveryResult
- CompletenessResult
- previous questions
- previous answers
- clarification round

### Output

`ClarificationQuestionSet`

Recommended fields:

- question_id
- question
- rationale
- answer_type
- options
- required

### Delegation From

- Completeness Evaluator

### Delegation To

- Session Manager
- Frontend
- Human user

### Model

Fast, low-cost model.

### Tools

None.

### Failure Behavior

Use a deterministic fallback question template based on missing dimensions.

---

## 4.3 Preliminary Capability Classifier

### Type

Classifier.

### Main Tasks

Determine early capability flags before product definition.

Flags:

- current market context needed
- AI relevance
- sensitive domain
- regulated domain
- external integration likelihood
- autonomous action likelihood
- high-risk workflow
- deep QA requirement
- early market research requirement

### Input

- DiscoveryResult
- CompletenessResult

### Output

`CapabilityClassification`

Recommended fields:

- market_research_needed
- ai_relevant
- security_sensitive
- regulated_domain
- external_integrations_likely
- autonomous_actions_likely
- deep_qa_likely
- risk_level
- reasons

### Delegation From

- Completeness Evaluator

### Delegation To

- Market and GTM Strategist for early research
- Product Manager
- Specialist Planner

### Model

Fast, low-cost model or deterministic rule engine.

### Tools

None.

---

# 5. Product Definition Components

## 5.1 Initial Product Definition Validator

### Type

Validator.

### Main Tasks

- validate ProductDefinition schema
- validate RequirementsSpecification schema
- detect contradictions
- detect duplicate sections
- ensure MVP scope is explicit
- ensure requirements are testable
- ensure assumptions remain visible
- ensure Product Manager and Business Analyst outputs align

### Input

- ProductDefinition
- RequirementsSpecification
- DiscoveryResult

### Output

`ProductDefinitionValidationResult`

Recommended fields:

- valid
- missing_fields
- contradictions
- untestable_requirements
- assumption_violations
- repair_instructions

### Delegation From

- Product Manager
- Business Analyst

### Delegation To

- Output Repair Processor when invalid
- Specialist Planner when valid

### Model

Deterministic validation first.

Optional fast model for semantic consistency checks.

### Tools

None.

---

# 6. Specialist Planning Components

## 6.1 Specialist Planner

### Type

Structured planner or routing classifier.

### Main Tasks

- select required specialists
- skip unnecessary specialists
- explain each selection
- define execution dependencies
- define parallel execution groups
- estimate cost category
- preserve mandatory agents
- reduce optional work when budgets are low

### Input

- DiscoveryResult
- ProductDefinition
- RequirementsSpecification
- CapabilityClassification
- session token budget
- session cost budget

### Output

`SpecialistPlan`

Recommended fields:

- required_agents
- selected_specialists
- skipped_specialists
- selection_reasons
- execution_groups
- dependencies
- estimated_cost_category
- estimated_token_category
- degraded_mode
- skipped_due_to_budget

### Delegation From

- Initial Product Definition Validator

### Delegation To

- Solution Architect
- Market and GTM Strategist
- AI Architect
- Security Architect
- QA and Evaluation Architect

### Model

Balanced model initially.

A deterministic hybrid planner may replace parts of it later.

### Tools

None.

### Required Routing Rules

Always include:

- Solution Architect
- Market and GTM Strategist
- Lead Reviewer

Conditionally include:

- AI Architect
- Security Architect
- QA and Evaluation Architect

---

## 6.2 Cost Budget Controller

### Type

Deterministic processor.

### Main Tasks

- enforce maximum session tokens
- enforce maximum session cost
- enforce maximum agent runs
- enforce maximum tool calls
- enforce clarification-round limit
- enforce refinement-round limit
- switch to degraded execution mode
- stop optional work when budget is near limit

### Input

- UsageSummary
- SpecialistPlan
- configured limits

### Output

`BudgetDecision`

Recommended fields:

- allowed
- remaining_tokens
- remaining_cost
- remaining_tool_calls
- degraded_mode
- agents_to_skip
- reason

### Delegation From

- Specialist Planner
- Runtime before every agent or tool call

### Delegation To

- Flow router

### Model

None.

### Tools

None.

---

# 7. Tool Control Components

## 7.1 Tool Policy Manager

### Type

Runtime service.

### Main Tasks

- maintain agent-specific tool allowlists
- validate tool input schema
- enforce domain restrictions
- enforce timeout
- enforce retries
- enforce maximum result count
- enforce maximum output size
- record tool invocations
- block unsupported tools
- normalize tool errors

### Input

- agent identity
- tool request
- session budget
- tool policy

### Output

- approved tool execution request
- denied tool request
- normalized tool error

### Delegation From

- Market and GTM Strategist
- Solution Architect
- AI Architect
- Security Architect

### Delegation To

- approved external tool
- Tool Output Sanitizer

### Model

None.

### Tools

- approved web search
- approved webpage retrieval
- official documentation lookup
- approved current pricing lookup
- approved security reference lookup

---

## 7.2 Tool Output Sanitizer

### Type

Guardrail processor.

### Main Tasks

- treat external content as untrusted data
- detect prompt injection in retrieved content
- strip unsafe instructions
- enforce output-size limit
- preserve source metadata
- reject malformed responses
- redact secrets
- prevent tool content from modifying system instructions

### Input

- raw tool response
- tool metadata
- agent identity

### Output

`SanitizedToolResult`

Recommended fields:

- safe_content
- sources
- warnings
- injection_detected
- discarded_sections
- confidence

### Delegation From

- Tool Policy Manager

### Delegation To

- requesting agent

### Model

Deterministic first.

Optional fast model for semantic injection detection.

### Tools

None.

---

# 8. Agent Output Reliability Components

## 8.1 Agent Output Validator

### Type

Validator.

### Main Tasks

- validate Pydantic schema
- validate required fields
- validate confidence range
- ensure assumptions are labeled
- detect unsupported claims
- verify cited sources exist
- detect placeholders
- verify risks include mitigations
- ensure recommendations relate to requirements
- enforce agent-specific rules

### Input

- agent output
- agent contract
- upstream structured context
- source metadata when applicable

### Output

`AgentOutputValidationResult`

Recommended fields:

- valid
- schema_errors
- domain_errors
- unsupported_claims
- missing_sources
- contradictions
- repair_instructions

### Delegation From

- every agent execution

### Delegation To

- Output Repair Processor when invalid
- Flow state when valid

### Model

Deterministic first.

Optional fast model for semantic consistency.

### Tools

None.

---

## 8.2 Output Repair Processor

### Type

Focused LLM processor.

### Main Tasks

- repair invalid JSON or structured output
- fill missing required fields using existing evidence
- correct schema errors
- remove unsupported placeholders
- preserve original meaning
- avoid adding new unsupported content

### Input

- invalid output
- validation errors
- expected schema
- original task context

### Output

- repaired structured output

### Delegation From

- Agent Output Validator
- Initial Product Definition Validator
- Final Output Validator

### Delegation To

- validator for one re-check

### Model

Fast, low-cost model.

### Tools

None.

### Retry Limit

Maximum one repair attempt per output.

---

# 9. Cost and Feasibility Components

## 9.1 Cost Aggregator

### Type

Deterministic aggregator.

### Main Tasks

Aggregate cost information from all validated outputs.

Cost sources:

- Product Manager delivery assumptions
- Solution Architect engineering and infrastructure costs
- AI Architect model and AI-runtime costs
- Security Architect security-control costs
- QA Architect testing and evaluation costs
- Market and GTM Strategist launch and acquisition assumptions

### Input

- ProductDefinition
- SolutionArchitecture
- AIArchitecture when present
- SecurityArchitecture when present
- QAEvaluationPlan when present
- MarketAndGTMReport

### Output

`CostSummary`

Recommended fields:

- estimate_confidence
- one_time_cost_categories
- recurring_cost_categories
- engineering_effort_category
- infrastructure_costs
- ai_usage_costs
- third_party_costs
- security_costs
- testing_and_evaluation_costs
- gtm_costs
- scaling_cost_drivers
- cost_optimization_opportunities
- assumptions
- limitations

### Delegation From

- specialist output aggregation

### Delegation To

- Lead Reviewer
- Blueprint Assembler

### Model

None.

A model must not invent final cost calculations.

### Tools

None directly.

Current pricing evidence must come from approved specialist tools.

---

# 10. Review Support Components

## 10.1 Lead Review Validator

### Type

Deterministic validator.

### Main Tasks

- validate LeadReview schema
- verify one of the allowed approval states
- validate revision targets
- ensure at most one refinement request
- ensure issues reference actual source sections
- prevent unrestricted workflow restart

### Input

- LeadReview
- specialist output registry
- refinement count

### Output

`LeadReviewValidationResult`

### Delegation From

- Lead Reviewer

### Delegation To

- targeted specialist refinement
- Blueprint Assembler
- Output Repair Processor when structurally invalid

### Model

None.

### Tools

None.

---

# 11. Blueprint and Reporting Components

## 11.1 Blueprint Assembler

### Type

Deterministic processor.

### Main Tasks

- assemble approved structured outputs
- preserve source ownership
- order sections
- include assumptions
- include limitations
- include unresolved risks
- include partial failure warnings
- attach usage and trace metadata
- create canonical blueprint object

### Input

- approved ProductDefinition
- approved RequirementsSpecification
- approved MarketAndGTMReport
- approved SolutionArchitecture
- optional specialist outputs
- CostSummary
- LeadReview
- session metadata

### Output

`ProductBlueprint`

### Delegation From

- Lead Reviewer approval

### Delegation To

- Final Output Validator
- Markdown Renderer

### Model

None.

### Tools

None.

### Forbidden Behavior

- creating new recommendations
- modifying specialist decisions
- deleting assumptions
- hiding partial failures
- inventing sources

---

## 11.2 Final Output Validator

### Type

Validator.

### Main Tasks

- ensure all mandatory sections exist
- ensure no placeholders remain
- ensure confirmed user facts are respected
- ensure assumptions are visible
- ensure architecture supports requirements
- ensure AI recommendations include evaluation
- ensure security risks include controls
- ensure GTM plan is present
- ensure cost estimates are labeled as estimates
- ensure failed analyses are disclosed
- ensure source references exist

### Input

- ProductBlueprint

### Output

`FinalOutputValidationResult`

### Delegation From

- Blueprint Assembler

### Delegation To

- Output Repair Processor when invalid
- Markdown Renderer when valid

### Model

Deterministic first.

Optional fast model for semantic consistency.

### Tools

None.

---

## 11.3 Markdown Renderer

### Type

Deterministic renderer.

### Main Tasks

- render ProductBlueprint as Markdown
- preserve section order
- format tables
- format assumptions
- format risks
- format sources
- format cost summary
- format roadmap
- attach usage and trace summary

### Input

- validated ProductBlueprint

### Output

- final Markdown report

### Delegation From

- Final Output Validator

### Delegation To

- Session Manager
- API response

### Model

None.

### Tools

- template engine or Python renderer

---

# 12. Runtime and Operational Services

## 12.1 Session Manager

### Type

Application service.

### Main Tasks

- create sessions
- update session status
- persist clarification questions
- persist answers
- pause sessions
- resume sessions
- persist final outputs
- expose session state to API

### Input

- session commands
- Flow state updates

### Output

- persisted session
- current session state

### Tools

- SQLite for local development
- PostgreSQL for deployment

---

## 12.2 Flow State Repository

### Type

Repository.

### Main Tasks

Persist:

- original idea
- discovery result
- questions
- answers
- capability classification
- product definition
- specialist plan
- specialist outputs
- cost summary
- lead review
- refinement count
- final blueprint
- usage metadata
- failures

### Model

None.

### Tools

- SQLAlchemy
- SQLite or PostgreSQL

---

## 12.3 Usage and Cost Tracker

### Type

Application service.

### Main Tasks

Track by:

- session
- agent
- task
- model
- provider
- tool

Metrics:

- input tokens
- output tokens
- agent runs
- tool calls
- retries
- estimated cost
- duration
- failed calls
- degraded-mode decisions

### Input

- CrewAI execution metadata
- provider usage metadata
- tool execution metadata

### Output

`UsageSummary`

### Model

None.

### Tools

- configured model pricing table
- runtime counters

---

## 12.4 Error Normalizer

### Type

Application service.

### Main Tasks

Normalize:

- validation errors
- rate-limit errors
- provider errors
- tool errors
- timeout errors
- output validation errors
- session conflicts
- persistence errors
- unknown errors

### Output

Canonical error:

```json
{
  "code": "SPECIALIST_EXECUTION_FAILED",
  "message": "The specialist analysis could not be completed.",
  "recoverable": true,
  "stage": "specialist_execution",
  "session_id": "session-id",
  "request_id": "request-id"
}
```

### Model

None.

---

## 12.5 Rate Limiter

### Type

Application service.

### Main Tasks

- enforce per-IP request limits
- limit active sessions
- limit answer submissions
- limit tool calls
- limit clarification rounds
- prevent retry abuse
- protect public deployment

### Model

None.

### Tools

- in-memory limiter for single-instance deployment
- Redis only when multiple replicas are introduced

---

## 12.6 Trace Adapter

### Type

Observability service.

### Main Tasks

- initialize CrewAI trace
- attach request and session identifiers
- trace Flow transitions
- trace agent executions
- trace task executions
- trace tool calls
- trace human feedback pauses
- trace retries
- trace failures
- record latency and usage

### Model

None.

### Tools

- CrewAI tracing

---

## 12.7 Structured Logger

### Type

Observability service.

### Main Tasks

Produce JSON logs containing:

- timestamp
- level
- request_id
- session_id
- flow_id
- trace_id
- stage
- agent_name
- task_name
- tool_name
- status
- duration_ms
- retry_count
- estimated_cost
- error_code

Must not log:

- API keys
- raw credentials
- complete system prompts
- hidden reasoning
- sensitive user data unnecessarily
- full unredacted tool responses

### Tools

- Structlog

---

## 12.8 Health and Readiness Service

### Type

Operational service.

### Main Tasks

Support:

- `GET /health`
- `GET /ready`
- `GET /metrics/summary`

Checks:

- application process
- configuration validity
- database connectivity
- required provider configuration
- persistence readiness

### Model

None.

---

# 13. End-to-End Delegation Flow

```text
Frontend
    ↓
Input Validator
    ↓
Input Guardrail Processor
    ↓
Session Manager
    ↓
Discovery Analyst
    ↓
Completeness Evaluator
    ├── Incomplete
    │      ↓
    │  Clarification Question Generator
    │      ↓
    │  Session pause
    │      ↓
    │  Human answers
    │      ↓
    │  Session resume
    │      └──────────────→ Completeness Evaluator
    │
    └── Complete
           ↓
Preliminary Capability Classifier
           ↓
Optional Early Market Research
           ↓
Product Manager
           ↓
Business Analyst
           ↓
Initial Product Definition Validator
           ↓
Specialist Planner
           ↓
Cost Budget Controller
           ↓
Selected Specialists
           ↓
Agent Output Validator
           ↓
Cost Aggregator
           ↓
Lead Reviewer
           ↓
Lead Review Validator
           ├── Targeted refinement
           │       ↓
           │  Selected specialist
           │       ↓
           │  Revalidation
           │       ↓
           │  Lead Reviewer final check
           │
           └── Approved
                  ↓
Blueprint Assembler
                  ↓
Final Output Validator
                  ↓
Markdown Renderer
                  ↓
Session Manager
                  ↓
Final Report
```

---

# 14. Final Non-Agent Component Set

## Classifiers and Planners

- Completeness Evaluator
- Preliminary Capability Classifier
- Specialist Planner

## Validators and Guardrails

- Input Validator
- Input Guardrail Processor
- Initial Product Definition Validator
- Agent Output Validator
- Lead Review Validator
- Final Output Validator
- Tool Output Sanitizer

## Processors and Aggregators

- Clarification Question Generator
- Output Repair Processor
- Cost Budget Controller
- Cost Aggregator
- Blueprint Assembler
- Markdown Renderer

## Runtime Services

- Session Manager
- Flow State Repository
- Usage and Cost Tracker
- Tool Policy Manager
- Error Normalizer
- Rate Limiter
- Trace Adapter
- Structured Logger
- Health and Readiness Service
