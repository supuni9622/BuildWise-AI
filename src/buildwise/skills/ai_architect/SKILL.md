---
name: ai-architect
description: >
  AI architecture decision methodology for designing production-minded,
  secure, observable, evaluable, and cost-aware AI capabilities, including
  models, prompts, tools, agents, RAG, guardrails, human oversight, and
  fallback behavior.
version: "1.0.0"
---

# AI Architect Skill

## Purpose

Use this skill when validated requirements contain AI-assisted, AI-core, RAG,
agentic, generative, classification, extraction, recommendation, or other
model-driven capabilities.

The objective is to produce a coherent `AIArchitecture` that defines:

- where AI is justified
- where deterministic software is preferable
- model requirements and model roles
- model-selection strategy
- prompt contracts
- controlled tool policies
- AI agents and workflows
- RAG architecture when required
- guardrails
- evaluation strategy
- AI observability
- human oversight
- fallback behavior
- AI risks
- cost controls

This skill does not own:

- product scope
- product feature priority
- business requirements
- general application architecture
- cloud infrastructure design
- complete security architecture
- complete QA strategy
- final blueprint approval

---

# Ownership Boundary

The AI Architect owns:

- AI capability decomposition
- model-role definition
- model requirements
- model-selection rationale
- model-routing strategy
- prompt contracts
- tool-use policies
- agent design
- agent-workflow design
- RAG design
- AI guardrails
- AI evaluation
- AI observability
- human oversight
- AI fallback strategy
- AI cost strategy
- AI-specific risks

The AI Architect does not own:

- product vision
- personas
- MVP scope
- feature prioritization
- functional requirement authoring
- service boundaries
- database selection
- deployment topology
- identity architecture
- encryption strategy
- compliance approval
- complete release strategy

---

# Core Principles

## 1. AI must be justified

Do not introduce AI merely because the product idea mentions AI.

For every proposed AI capability, ask:

1. What user outcome requires probabilistic or model-driven behavior?
2. Can deterministic software solve the problem reliably?
3. What value does AI add?
4. What new risks does AI introduce?
5. What happens when the model is unavailable or incorrect?
6. How will quality be measured?

Prefer deterministic software when the required behavior is:

- rules-based
- calculation-based
- transactional
- permission-driven
- schema-driven
- workflow-driven
- exact
- legally prescribed
- safety-critical without human review

---

## 2. Design capabilities before selecting models

Do not begin with a provider or model name.

First define:

- capability
- user value
- expected behavior
- input
- output
- quality target
- latency target
- cost constraint
- privacy constraint
- grounding need
- tool need
- human-review need
- fallback behavior

Model selection should follow requirements.

---

## 3. Prefer the simplest AI architecture

Use the minimum architecture needed to satisfy the capability.

Consider this order:

1. deterministic logic
2. one direct model call
3. one model call with structured output
4. model call with retrieval
5. model call with tools
6. one specialized agent
7. Flow-orchestrated agent workflow
8. multiple agents or Crews

Do not jump to multi-agent architecture without a clear coordination need.

---

## 4. Structured output by default

When model output enters application logic, prefer structured output.

Use:

- Pydantic models
- explicit schemas
- task `output_pydantic`
- response-format validation
- deterministic guardrails

Avoid relying on manual JSON extraction from free-form text.

Free-form output is appropriate only when the output is intended primarily for
human reading.

---

## 5. Flows own orchestration

For CrewAI-based applications:

- Flows own state
- Flows own routing
- Flows own branching
- Flows own pause and resume
- Flows own human clarification
- Flows own execution order
- Flows decide which Crews run
- Crews own focused reasoning work
- Agents remain specialized
- Tasks define concrete assignments

Do not place deterministic workflow control inside an agent prompt.

---

## 6. Tools require explicit control

Tools provide actions and therefore expand the risk surface.

For every tool define:

- purpose
- allowed operations
- prohibited operations
- side effects
- authentication
- authorization
- input schema
- output schema
- timeout
- retry policy
- maximum calls
- audit requirements
- redaction requirements
- idempotency
- human approval

Do not grant tools broadly for convenience.

---

## 7. Evaluation is part of architecture

A capability is incomplete until its quality can be measured.

Every AI capability must define:

- evaluation metrics
- evaluation dataset
- test cases
- target thresholds
- release criteria
- regression policy
- failure behavior
- ownership

Do not defer evaluation until after implementation.

---

# AI Architecture Process

Follow this process in order.

## Step 1 — Review validated inputs

Review:

- ProductDefinition
- RequirementsSpecification
- SolutionArchitecture
- capability classification
- security signals
- delivery constraints
- cost constraints
- assumptions
- open questions

Identify which requirements genuinely need AI.

Do not reinterpret product intent.

---

## Step 2 — Define AI capabilities

For every AI capability, define:

- name
- purpose
- user value
- use-case type
- criticality
- input
- output
- expected behavior
- deterministic requirements
- human-review requirements
- non-AI fallback
- related product features
- related requirements
- assumptions
- limitations

Do not combine unrelated AI behaviors into one capability.

---

## Step 3 — Challenge AI necessity

For each capability, compare:

- deterministic implementation
- rule-based implementation
- search-based implementation
- standard analytics
- statistical model
- LLM-based implementation
- agentic implementation

Document why the selected approach is justified.

Reject AI when deterministic alternatives are:

- more accurate
- cheaper
- safer
- easier to maintain
- easier to audit
- sufficient for the user outcome

---

## Step 4 — Define model roles

Define model roles before selecting models.

Potential roles include:

- generation
- reasoning
- classification
- extraction
- embedding
- reranking
- moderation
- vision
- speech
- judge
- fallback

For each role, define:

- purpose
- required capabilities
- quality requirements
- context needs
- output-token needs
- latency limit
- cost limit
- structured-output need
- tool-calling need
- streaming need
- multimodal need
- privacy and residency constraints

---

## Step 5 — Define the model strategy

Choose an appropriate strategy:

- single model
- model routing
- multi-provider
- self-hosted
- hybrid

### Single model

Use when:

- capability variation is low
- simplicity matters
- provider dependence is acceptable
- cost and quality remain within limits

### Model routing

Use when:

- tasks have materially different complexity
- some tasks require stronger reasoning
- cost optimization is important
- latency requirements vary
- structured output or context needs differ

### Multi-provider

Use when:

- resilience is required
- provider outage risk is material
- regulatory or regional requirements differ
- model specialization provides clear value

### Self-hosted

Use only when justified by:

- privacy
- residency
- predictable high volume
- provider restrictions
- specialized fine-tuning
- organizational policy

Do not use multi-provider or self-hosting merely for portfolio complexity.

---

## Step 6 — Select models

For each model selection, evaluate:

- capability fit
- structured-output support
- tool-use support
- context window
- reasoning quality
- latency
- price
- availability
- data handling
- regional availability
- provider reliability
- observability support
- fallback compatibility
- operational maturity

Document:

- selected role
- provider
- model or model family
- rationale
- advantages
- disadvantages
- alternatives
- fallback
- timeout
- retry limit
- confidence
- cost assumptions

Do not present rapidly changing pricing or model availability as timeless facts.

---

## Step 7 — Design prompt contracts

A prompt contract should define:

- purpose
- prompt type
- version
- model role
- required variables
- sensitive variables
- system behavior
- instruction summary
- expected output
- structured-output schema
- prohibited behavior
- repair strategy
- failure behavior
- human-review need
- risk level

Prompts should be:

- versioned
- testable
- traceable
- concise
- schema-aware
- separated from application logic

Do not embed business rules only inside prompts when they can be enforced
deterministically.

---

## Step 8 — Design tool policies

For each tool, MCP server, or app integration, define:

- why it is required
- which agent may use it
- allowed operations
- prohibited operations
- side-effect type
- sensitive-data policy
- timeout
- retry policy
- call limit
- authorization
- audit logging
- idempotency
- approval requirement
- fallback behavior

Apply least privilege.

### Side-effect rules

Read-only tools may operate without human approval when authorized.

Reversible writes require:

- authorization
- audit logging
- bounded scope
- idempotency when applicable

Irreversible writes and consequential external actions require:

- explicit authorization
- human approval
- audit logging
- input validation
- clear confirmation
- bounded execution

---

## Step 9 — Decide whether agents are needed

Use a direct model call when:

- there is one focused reasoning task
- no tool planning is required
- no multi-step execution is required
- no delegated work is required

Use one specialized agent when:

- the task requires iterative reasoning
- tools may be selected dynamically
- bounded autonomy is useful
- the agent has one clear responsibility

Use a Crew when:

- multiple specialists need to collaborate
- tasks have distinct ownership
- outputs of one task inform another
- review or synthesis is required

Use a Flow when:

- routing is deterministic
- state must persist
- human input may pause execution
- branches depend on structured state
- multiple Crews must be coordinated
- execution must resume after interruption

Do not use one generic agent for the entire application.

---

## Step 10 — Design agents

Every proposed agent must have:

- one clear role
- one clear goal
- concise backstory
- explicit responsibilities
- explicit exclusions
- limited tools
- model role
- prompt contracts
- maximum iterations
- maximum tool calls
- structured output
- failure behavior
- approval requirements

Enable delegation only when there is a validated need.

Avoid agents whose responsibility overlaps significantly with another agent.

---

## Step 11 — Design AI workflows

For every workflow, define:

- entry condition
- state
- steps
- order
- dependencies
- routes
- outputs
- completion condition
- timeout
- retries
- failure behavior
- persistence
- resumability
- streaming
- approval points

In CrewAI-based applications, prefer:

- `@start()` for entry points
- `@listen()` for deterministic sequencing
- `@router()` for structured branching
- `@persist` for resumable state
- human feedback for approval or clarification
- focused Crew execution from Flow steps

Do not hide critical workflow decisions inside free-form agent reasoning.

---

## Step 12 — Design RAG only when required

Use RAG when the model must answer or generate using:

- private documents
- changing knowledge
- domain-specific documents
- source-grounded evidence
- large corpora
- user-owned knowledge

Do not use RAG merely because documents exist.

A RAG design must define:

- knowledge sources
- ingestion
- parsing
- chunking
- metadata
- embedding
- indexing
- vector store
- sparse retrieval when useful
- hybrid retrieval when useful
- reranking
- filtering
- context construction
- citation
- access control
- freshness
- deletion
- evaluation

---

## Step 13 — Define chunking and retrieval

### Chunking

Choose based on document structure and retrieval needs.

Options include:

- fixed-size
- recursive
- semantic
- document-structure-aware
- parent-child
- custom

Preserve meaningful boundaries where possible.

Ensure overlap remains lower than chunk size.

### Retrieval

Choose based on query and corpus behavior.

Options include:

- dense
- sparse
- hybrid
- metadata-filtered
- graph
- multi-stage

Define:

- initial top-k
- final top-k
- filters
- reranking
- relevance threshold
- fallback behavior

Do not assume dense-only retrieval is always sufficient.

---

## Step 14 — Design context construction

Define:

- token budget
- reserved output budget
- deduplication
- source diversity
- parent expansion
- adjacent merging
- compression
- truncation
- citation format
- empty-context behavior

Do not fill the entire context window simply because space is available.

Prioritize relevant, authoritative, non-duplicated evidence.

---

## Step 15 — Define guardrails

Guardrails should exist at the appropriate stages:

- input
- retrieval
- prompt
- tool
- generation
- output
- agent
- workflow

Potential controls include:

- schema validation
- content filtering
- prompt-injection detection
- PII detection
- secret detection
- authorization
- tool allowlists
- grounding checks
- citation validation
- rate limits
- budget limits
- human approval

For each guardrail define:

- trigger
- method
- action
- blocking behavior
- retry behavior
- audit requirements
- related capabilities

Prefer deterministic validation when possible.

---

## Step 16 — Define evaluation

Each capability must have evaluation coverage.

Use a combination of:

- deterministic tests
- golden datasets
- synthetic datasets
- adversarial cases
- production samples
- human evaluation
- LLM-as-judge
- regression suites

Potential metrics include:

- correctness
- relevance
- groundedness
- faithfulness
- completeness
- schema validity
- retrieval recall
- retrieval precision
- tool success
- task completion
- safety
- latency
- cost
- human rating

LLM-as-judge should not be the only quality signal for critical capabilities.

---

## Step 17 — Define AI observability

Capture signals such as:

- Flow execution
- Crew execution
- task execution
- agent steps
- model calls
- prompt versions
- tool calls
- retrieval traces
- guardrail decisions
- evaluation scores
- token usage
- cost
- latency
- time to first token
- tokens per second
- failures

Ensure sensitive data is redacted.

Distinguish:

- LLM execution tracing
- structured application logging
- aggregate metrics
- business usage records

---

## Step 18 — Define human oversight

Require human oversight when AI output may:

- create legal or financial consequences
- affect access or permissions
- expose sensitive data
- perform irreversible actions
- trigger external communication
- make regulated recommendations
- materially affect users
- act with high uncertainty

Define:

- review point
- information shown to the reviewer
- approval options
- rejection behavior
- revision behavior
- audit record
- timeout
- fallback

---

## Step 19 — Define fallback behavior

For each critical AI capability, define what happens when:

- the model times out
- the provider is unavailable
- output fails schema validation
- retrieval returns insufficient context
- a guardrail blocks output
- a tool fails
- cost limits are reached
- confidence is too low
- human approval is denied

Fallback options include:

- retry
- repair
- alternate model
- deterministic path
- reduced capability
- human review
- continue with limitation
- fail safely

Do not use infinite retries.

---

## Step 20 — Identify AI risks

Review risks including:

- hallucination
- incorrect output
- bias
- toxicity
- prompt injection
- data leakage
- privacy exposure
- tool misuse
- excessive agency
- model drift
- retrieval failure
- evaluation gaps
- provider lock-in
- availability
- latency
- uncontrolled cost
- weak observability
- insufficient human oversight

For each risk, define:

- likelihood
- severity
- impact
- trigger
- mitigation
- contingency
- monitoring indicator
- ownership
- acceptance status

---

## Step 21 — Define cost controls

AI cost design should include:

- model tiering
- token limits
- tool-call limits
- retry limits
- caching
- batching
- prompt reduction
- retrieval limits
- output limits
- provider fallback rules
- per-run budgets
- user quotas
- rate limits
- cost attribution

Do not optimize cost in a way that undermines required quality or safety.

---

## Step 22 — Make the architecture decision

Use one supported outcome.

### Approved

Use when the architecture is complete, traceable, evaluated, guarded, and has no
blocking questions.

### Approved with assumptions

Use when implementation can proceed with explicit assumptions.

### Requires clarification

Use when unresolved decisions prevent responsible AI architecture.

### Cannot proceed

Use when the requested AI behavior cannot be designed safely or coherently with
available information.

The decision must match:

- open questions
- assumptions
- risks
- limitations
- evaluation coverage
- fallback coverage
- confidence

---

# CrewAI-Specific Design Rules

When the implementation uses CrewAI:

- use Flows for orchestration
- use structured Flow state
- use `@router()` for deterministic routing
- use `@persist` for resumable workflows
- use focused Crews
- use specialized Agents
- use Tasks with `output_pydantic`
- use Task guardrails
- use Skills for reusable methodology
- use Knowledge for retrieved facts
- use Tools, MCPs, and Apps for actions
- use tracing for runtime inspection
- use Flow usage metrics for complete token accounting

Do not recreate these capabilities as custom platforms unless a real gap exists.

---

# Architecture Quality Checklist

Before returning `AIArchitecture`, verify:

- every AI capability is justified
- deterministic alternatives were considered
- each capability has model-requirement coverage
- each capability has evaluation coverage
- RAG capabilities have complete RAG design
- agentic capabilities have workflow design
- model selections trace to requirements
- prompts are versioned
- tools are least-privileged
- side effects are controlled
- guardrails cover material risks
- human oversight is defined where required
- fallbacks exist
- observability is defined
- cost controls are defined
- assumptions are explicit
- open questions are not hidden
- AI architecture fits the SolutionArchitecture
- output conforms to `AIArchitecture`

---

# Prohibited Behavior

Never:

- add AI without a validated need
- recommend multi-agent systems by default
- use agents for deterministic routing
- grant unrestricted tools
- allow irreversible actions without approval
- rely on manual JSON parsing
- claim model output is deterministic
- guarantee model quality without evaluation
- use RAG without a grounding need
- use LLM-as-judge as the only critical evaluator
- ignore failure and fallback behavior
- ignore token and cost limits
- redesign the general application architecture
- replace security architecture
- replace QA architecture
- approve the final blueprint

---

# Completion Standard

The AI architecture is complete when an implementation team can clearly
understand:

- which capabilities use AI
- why AI is justified
- which model roles exist
- how models are selected and routed
- how prompts are managed
- which tools and agents are allowed
- how workflows are orchestrated
- whether RAG is required and how it works
- which guardrails apply
- how quality is evaluated
- how execution is observed
- where humans intervene
- how failures are handled
- how cost is controlled
- which AI risks remain
- whether implementation may proceed