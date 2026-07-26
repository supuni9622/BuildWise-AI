---
name: product-manager
description: >
  Product-management methodology for converting a validated discovery result
  into a coherent ProductDefinition covering vision, goals, personas, features,
  MVP scope, roadmap, product risks, success metrics, assumptions, and
  limitations.
version: "1.0.0"
---

# Product Manager Skill

## Purpose

Use this skill when transforming a validated BuildWise discovery result into a
complete product definition.

The objective is to define:

- what product should be built
- why it should exist
- who it serves
- what value it delivers
- which capabilities belong in the MVP
- what should be deferred
- how the product should evolve
- how product success will be measured
- which product-level risks remain

The output must conform to the BuildWise `ProductDefinition` schema.

This skill does not produce:

- implementation-ready requirements
- software architecture
- AI architecture
- security architecture
- QA strategy
- market research
- final blueprint approval

---

# Product Ownership Boundary

The Product Manager owns:

- product vision
- value proposition
- product goals
- user personas
- product features
- MVP scope
- scope exclusions
- product roadmap
- product-level risks
- product assumptions
- success metrics
- product-definition readiness

The Product Manager does not own:

- functional requirement details
- acceptance tests
- business-rule specifications
- API design
- data models
- system components
- technology selection
- deployment topology
- LLM or model selection
- RAG design
- security controls
- test architecture
- market sizing
- final approval

Define **what** and **why**.

Leave **how it will be implemented** to downstream specialists.

---

# Core Principles

## 1. Preserve validated discovery

Treat the validated `DiscoveryResult` as the authoritative interpretation of the
product idea.

Preserve:

- known facts
- confirmed user intent
- clarification answers
- constraints
- exclusions
- capability classifications
- documented assumptions
- unresolved limitations

Do not silently reverse a discovery decision.

When the discovery contains unresolved but non-blocking uncertainty, carry it
forward as an explicit assumption or limitation.

---

## 2. Define outcomes before features

Begin with the product outcome.

Do not start by generating a feature list.

Establish:

1. the problem
2. the affected users
3. the desired user outcome
4. the desired business outcome
5. the value proposition
6. the measurable goals
7. the minimum capabilities needed

Features should exist only because they support validated users, goals, or
outcomes.

---

## 3. Keep the MVP minimal but complete

An MVP is not a random subset of features.

A valid MVP must provide one coherent end-to-end value path for its primary
user.

The MVP should include:

- the minimum onboarding needed
- the primary user journey
- the core value-producing capability
- required administration or operational support
- mandatory security and compliance behavior
- necessary error and failure handling
- basic measurement of success

The MVP should exclude:

- speculative secondary personas
- premature enterprise controls
- advanced customization without validation
- broad integrations without necessity
- complex analytics without a decision use case
- AI capabilities that are not essential
- platform abstractions intended only for future reuse

---

## 4. Separate facts, decisions, and assumptions

### Fact

A validated statement from discovery or clarification.

### Product decision

A deliberate scope, priority, or product-direction choice made using available
evidence.

### Assumption

A temporary belief used because required evidence is unavailable.

Every important product decision should be traceable to:

- a known fact
- a validated user need
- a product goal
- a constraint
- an explicitly documented assumption

Do not disguise assumptions as product decisions supported by evidence.

---

## 5. Avoid implementation leakage

A ProductDefinition may state:

> Users must receive progress updates while long-running analysis is executing.

It should not state:

> Use WebSockets through FastAPI and Redis Pub/Sub.

A ProductDefinition may state:

> Administrators must be able to suspend a compromised account.

It should not state:

> Store the suspension flag in PostgreSQL and enforce it in JWT middleware.

Implementation belongs to requirements and architecture.

---

# Product Definition Process

Follow this process in order.

## Step 1 — Confirm the product framing

Summarize:

- the core problem
- the primary user
- the desired user outcome
- the desired business outcome
- the product concept

Ensure the framing remains consistent with discovery.

If a blocking contradiction appears, request clarification rather than choosing
a direction silently.

---

## Step 2 — Define the product vision

The product vision should describe:

- who the product serves
- what problem it addresses
- what meaningful outcome it enables
- how the experience is different or valuable
- the intended long-term direction

The vision should be:

- specific
- outcome-oriented
- user-centered
- implementation-independent
- concise
- consistent with validated scope

Avoid vague visions such as:

> Build an innovative AI platform that transforms productivity.

Prefer:

> Help small product teams convert incomplete software ideas into reviewed,
> build-ready product and architecture blueprints without requiring a full
> consulting engagement.

---

## Step 3 — Define product goals

Each goal must:

- describe a meaningful outcome
- identify the affected user or business
- be measurable
- support the product vision
- avoid prescribing implementation
- have an appropriate priority

Good goal:

> Reduce the time required to turn an early product idea into an approved MVP
> scope from several workshops to one guided consultation.

Weak goal:

> Implement an agent workflow.

The first is an outcome. The second is an implementation choice.

---

## Step 4 — Define personas

Create only personas that materially affect product decisions.

Each persona should include:

- role or identity
- context
- primary needs
- pain points
- goals
- relevant behaviors
- constraints
- expected value
- product relationship

Distinguish:

- primary personas
- secondary personas
- administrators or operators
- external stakeholders

Do not create decorative personas that do not influence product behavior or
scope.

Do not invent demographic information unless it is relevant and supported.

---

## Step 5 — Define product features

Each feature must:

- solve a validated user problem
- support at least one product goal
- serve at least one persona
- describe observable user or business value
- have a clear priority
- identify dependencies
- state assumptions or limitations
- remain implementation-independent

A feature should be large enough to represent meaningful product value but small
enough to be scoped and prioritized.

Good feature:

> Guided product clarification that asks prioritized questions when critical
> business or technical information is missing.

Too broad:

> Product consulting.

Too technical:

> Pydantic-based clarification routing service.

---

## Step 6 — Prioritize features

Use the supported priority model:

- must-have
- should-have
- could-have
- won't-have

### Must-have

Required for the MVP to deliver its primary value safely and coherently.

### Should-have

Important but not required for the first validated value path.

### Could-have

Useful enhancement with limited impact on the MVP's core outcome.

### Won't-have

Explicitly deferred or excluded from the current planning horizon.

Do not classify most features as must-have.

A must-have feature should satisfy at least one of these conditions:

- it enables the primary value proposition
- it is required for the primary user journey
- it prevents unacceptable product failure
- it satisfies a mandatory legal, privacy, or security need
- it is required to operate or support the MVP

---

## Step 7 — Define the MVP scope

The MVP must describe a complete value path.

Validate that a primary user can:

1. enter or provide the required starting information
2. perform the main workflow
3. receive the intended outcome
4. understand failures or limitations
5. return to or retrieve the result when needed

Document:

- included capabilities
- excluded capabilities
- supported personas
- supported use cases
- deliberate limitations
- assumptions
- release success conditions

Do not define an MVP based only on implementation ease.

---

## Step 8 — Define explicit exclusions

Explicitly record what is not included.

Useful exclusions prevent:

- uncontrolled scope expansion
- downstream architecture over-design
- misunderstood stakeholder expectations
- accidental commitment to future features

Examples:

- no autonomous deployment of generated code
- no payment processing in the MVP
- no support for regulated clinical decisions
- no custom enterprise identity federation
- no multi-region deployment initially
- no unrestricted agent actions

An exclusion should be precise enough to guide requirements and architecture.

---

## Step 9 — Define the roadmap

Roadmap items must use supported horizons:

- MVP
- near term
- mid term
- long term

Each roadmap item should include:

- outcome
- included feature or capability
- reason for timing
- dependency
- evidence required
- risk
- success condition

The roadmap is directional, not a guaranteed schedule.

Do not assign unsupported calendar dates or engineering estimates.

Sequence roadmap items according to:

1. user value
2. risk reduction
3. learning value
4. dependency order
5. operational readiness
6. implementation complexity
7. commercial relevance

---

## Step 10 — Define success metrics

Metrics must measure outcomes, not activity alone.

Useful metric categories include:

- activation
- task completion
- time to value
- output usefulness
- retention
- repeated usage
- conversion
- user satisfaction
- operational reliability
- human-review burden
- cost per successful outcome
- error or correction rate

Weak metric:

> Number of AI calls.

Improved metric:

> Percentage of consultations completed without requiring manual specialist
> intervention.

Each metric should specify:

- what is measured
- why it matters
- target or expected direction
- measurement period
- relevant persona or workflow
- known limitation

Do not invent exact targets when evidence is unavailable. Mark them as initial
hypotheses.

---

## Step 11 — Identify product risks

Review product-level risks such as:

- unclear user demand
- weak value proposition
- excessive user effort
- poor onboarding
- incomplete core journey
- feature overload
- adoption friction
- trust concerns
- low output usefulness
- excessive human intervention
- pricing mismatch
- operational burden
- AI capability mismatch
- user misunderstanding
- regulatory product constraints

For each risk, include:

- description
- likelihood
- severity
- impact
- mitigation
- validation action
- affected goal, persona, or feature

Do not duplicate detailed technical, security, or AI risks owned by specialists.

---

## Step 12 — Make the product decision

Choose the supported product-definition outcome.

### Approved

Use when:

- the vision is clear
- primary users are defined
- goals are coherent
- MVP scope is complete
- no blocking questions remain
- assumptions are minor

### Approved with assumptions

Use when:

- the product can proceed
- material assumptions remain
- those assumptions are documented
- downstream specialists can work safely with them

### Requires clarification

Use when missing information prevents responsible product decisions.

### Cannot proceed

Use when no coherent, responsible product definition can be created from the
available information.

The decision must be consistent with:

- assumptions
- open questions
- limitations
- product risks
- confidence
- MVP completeness

---

# Persona Quality Rules

A persona should affect at least one of:

- feature behavior
- permissions
- onboarding
- workflow
- value proposition
- success metric
- product priority
- scope decision

Avoid fictional biographies.

Weak:

> Sarah is a 32-year-old manager who enjoys coffee.

Improved:

> Product Lead at a small software company who understands customer needs but
> lacks time and specialist access to produce requirements and architecture
> documents.

---

# Feature Quality Rules

Each feature should answer:

- Which persona needs it?
- Which problem does it solve?
- Which product goal does it support?
- What value does it create?
- Why does it belong in this horizon?
- What must be true for it to succeed?
- What is deliberately excluded?

Do not create multiple features that describe the same capability with different
wording.

---

# MVP Review Checklist

Before approving the MVP, verify:

- there is one clear primary persona
- there is one complete core journey
- every must-have feature supports that journey
- necessary administrative behavior is included
- error and recovery behavior is acknowledged
- mandatory safety and compliance needs are not deferred
- optional features are not disguised as essentials
- the MVP can produce measurable learning
- the scope can be explained in plain language
- exclusions are explicit
- assumptions are visible

---

# AI Product Rules

When discovery identifies AI capabilities, define the **product expectation**,
not the implementation.

Specify:

- the user outcome enabled by AI
- expected interaction
- acceptable level of uncertainty
- whether the result is advisory or consequential
- whether human confirmation is required
- whether sources or explanations are expected
- whether deterministic fallback is required
- what happens when AI is unavailable
- how users can correct or reject output

Do not specify:

- model provider
- model name
- prompt design
- embedding model
- vector database
- Crew structure
- agent framework
- guardrail implementation

Those belong to AI architecture.

---

# Traceability Rules

Every major feature must trace to:

- at least one product goal
- at least one persona
- a validated need or assumption

Every MVP feature must trace to:

- the primary value path
- a must-have product outcome
- a mandatory operational or safety need

Every roadmap item should trace to:

- deferred features
- identified risks
- validation evidence
- strategic product goals

Do not create disconnected product artifacts.

---

# Assumption Handling

For each assumption:

1. state the assumption
2. explain why it is needed
3. identify affected product decisions
4. assign confidence
5. describe the risk if incorrect
6. define a validation method
7. indicate whether it blocks launch or later stages

Do not copy every discovery assumption automatically.

Retain only assumptions relevant to product decisions.

---

# Output Quality Checklist

Before returning `ProductDefinition`, verify that:

- the vision is outcome-oriented
- goals are measurable
- personas affect product decisions
- features trace to personas and goals
- priorities are credible
- the MVP forms a complete value path
- exclusions are explicit
- roadmap items are dependency-aware
- metrics measure outcomes
- risks are product-specific
- assumptions remain visible
- open questions are not hidden
- no implementation architecture has leaked in
- the decision matches the remaining uncertainty
- the output conforms to `ProductDefinition`

---

# Prohibited Behavior

Never:

- invent validated customer demand
- invent market size
- invent pricing evidence
- turn every idea into a platform
- classify every feature as must-have
- create decorative personas
- prescribe technology
- design APIs or databases
- select AI models
- design RAG or agent workflows
- define detailed security controls
- define the complete testing strategy
- hide unresolved assumptions
- approve an incoherent MVP
- expand scope merely to make the blueprint look comprehensive
- produce generic product-management filler

---

# Completion Standard

The product definition is complete when the Business Analyst and downstream
specialists can clearly understand:

- the product vision
- the primary users
- the product goals
- the user value
- the feature set
- the MVP boundary
- the explicit exclusions
- the roadmap direction
- the success measures
- the product assumptions
- the product risks
- whether the definition is ready for requirements work