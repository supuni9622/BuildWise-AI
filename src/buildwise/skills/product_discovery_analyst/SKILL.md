---
name: product-discovery-analyst
description: >
  Product discovery methodology for converting incomplete product ideas into
  structured, evidence-aware discovery results without inventing missing facts
  or prematurely designing the product.
version: "1.0.0"
---

# Product Discovery Analyst Skill

## Purpose

Use this skill when analyzing an early-stage, vague, incomplete, or partially
validated product idea.

The objective is to produce a clear discovery assessment that separates:

- user-provided facts
- clarification answers
- derived observations
- assumptions
- unknowns
- risks
- capability signals
- unresolved questions
- readiness for downstream product definition

The output must support the BuildWise `DiscoveryResult` schema.

This skill does not define the final product, requirements, architecture,
technology stack, AI design, security architecture, QA strategy, or final
blueprint.

---

# Core Principles

## 1. Preserve the user's intent

Interpret the product idea faithfully.

Do not rewrite the idea into a different product because another direction
appears more attractive, technically interesting, commercially promising, or
easier to build.

Preserve:

- the stated problem
- the intended users
- the desired outcome
- explicit constraints
- explicit exclusions
- preferred business model
- delivery expectations
- technology constraints when explicitly provided

When the user's intent is ambiguous, record the ambiguity rather than choosing
an interpretation silently.

---

## 2. Separate evidence from inference

Every meaningful statement must belong to one of these categories:

### Known fact

A statement explicitly provided by the user, confirmed through clarification,
or supported by an approved external source.

### Derived observation

A reasonable conclusion based directly on known facts.

Derived observations must:

- identify their supporting facts
- avoid overstating certainty
- remain reversible when new evidence appears

### Assumption

A temporary working belief used to continue analysis.

Assumptions must:

- be clearly labeled
- explain why they are needed
- explain what decision they affect
- describe how they could be validated

### Unknown

Missing information that may affect product, technical, commercial, security,
delivery, compliance, cost, or quality decisions.

Never present assumptions, guesses, conventions, or common industry patterns as
confirmed facts.

---

## 3. Prefer clarification over invention

When critical information is missing, generate a clarification question instead
of manufacturing an answer.

A clarification question should be asked only when the answer materially affects
one or more of the following:

- product value
- target users
- MVP scope
- business rules
- requirements
- architecture
- AI capability
- security
- privacy
- compliance
- integration design
- delivery plan
- cost
- QA strategy
- market strategy

Do not ask questions merely because additional detail would be interesting.

---

## 4. Keep discovery separate from product definition

Discovery determines whether the idea is sufficiently understood.

Discovery may identify:

- likely users
- user problems
- desired outcomes
- possible capability categories
- constraints
- uncertainties
- early risks

Discovery must not finalize:

- product vision
- feature priority
- MVP scope
- roadmap
- user stories
- acceptance criteria
- technology choices
- system components
- model providers
- deployment architecture
- market positioning
- final pricing

Those belong to downstream specialists.

---

## 5. Use minimum sufficient discovery

Do not over-analyze a simple product.

The discovery output should be proportional to:

- product complexity
- uncertainty
- business risk
- technical risk
- AI involvement
- sensitive data
- regulatory exposure
- integration complexity
- delivery constraints

A simple internal CRUD application should not receive the same discovery depth
as a regulated multi-tenant AI platform.

---

# Discovery Process

Follow this process in order.

## Step 1 — Restate the idea

Produce a concise interpretation of:

- the product
- the problem
- the intended users
- the expected outcome

The restatement should be neutral and should not introduce new scope.

Confirm that the interpretation remains faithful to the supplied input.

---

## Step 2 — Extract known facts

Extract facts from:

- the original product idea
- submitted clarification answers
- approved supporting context
- approved external research when tools are explicitly available

Each fact should include:

- the statement
- its source type
- its relevance
- its confidence
- any limitation

Do not combine multiple independent facts into one oversized statement.

---

## Step 3 — Identify assumptions

Identify assumptions required to understand or continue the consultation.

For each assumption, record:

- the assumption
- why it is currently reasonable
- what decision depends on it
- its risk if incorrect
- how it can be validated

Avoid assumptions that merely repeat known facts.

---

## Step 4 — Identify unknowns

Identify missing information.

Classify each unknown as:

- blocking
- important but non-blocking
- optional refinement

A blocking unknown is one that prevents a responsible downstream decision.

Typical blocking unknowns include:

- no identifiable target user
- no defined problem
- contradictory desired outcomes
- unclear handling of sensitive data
- unknown regulatory environment
- unknown consequential external actions
- missing access-control expectations
- unclear core business model
- unclear integration dependency
- unresolved AI necessity
- incompatible constraints

Do not classify every unknown as blocking.

---

## Step 5 — Evaluate completeness

Evaluate whether the idea is sufficiently complete for downstream work.

Consider:

- problem clarity
- target-user clarity
- outcome clarity
- scope clarity
- constraint clarity
- business-context clarity
- data clarity
- integration clarity
- security and privacy clarity
- AI-capability clarity
- delivery clarity

The completeness decision must be supported by explicit reasoning.

Do not rely only on a numeric score.

---

## Step 6 — Generate clarification questions

Generate the smallest useful set of questions.

Each question must:

- address one material uncertainty
- be answerable by the user
- explain why it matters
- identify the affected downstream decisions
- avoid requesting information already available
- avoid combining unrelated questions
- use plain language
- include examples only when they help the user answer accurately

Prioritize questions in this order:

1. product problem and users
2. business-critical behavior
3. sensitive data and regulation
4. AI necessity and expected behavior
5. integrations and external dependencies
6. scope and delivery constraints
7. cost and operational constraints
8. non-blocking refinements

Do not ask more questions than needed to unblock the next stage.

---

## Step 7 — Classify capabilities

Use the supported BuildWise capability taxonomy.

Potential capability classifications include:

- standard software
- AI-assisted
- AI-core
- RAG
- agentic workflow
- automation
- marketplace
- analytics
- real-time
- integration-heavy
- sensitive data
- regulated

Only select a capability when evidence supports it.

### AI classification rules

Classify a product as AI-assisted when AI improves part of the experience but the
core product remains useful without AI.

Classify it as AI-core when the product's primary value depends on model-driven
behavior.

Classify RAG only when the product needs grounded generation or retrieval over a
specific knowledge corpus.

Classify agentic workflow only when the system needs goal-directed reasoning,
tool use, branching, multi-step execution, or human approval around actions.

Do not classify ordinary automation as agentic solely because an LLM is present.

---

## Step 8 — Identify early risks

Identify only material early-stage risks.

Review these categories:

- product
- business
- market
- technical
- architecture
- integration
- AI
- security
- privacy
- compliance
- data
- quality
- delivery
- operations
- cost

Each risk should include:

- description
- severity
- likelihood
- supporting rationale
- likely impact
- proposed mitigation or validation action

Do not produce generic risks that apply to every software project.

---

## Step 9 — Determine the next step

Choose one supported outcome:

### Continue to product definition

Use when the idea is sufficiently understood and no blocking clarification is
required.

### Request clarification

Use when specific missing information prevents responsible downstream work.

### Continue with limitations

Use when remaining uncertainty is non-blocking and can be recorded explicitly.

### Fail discovery

Use only when:

- the input is unusable
- the request is internally contradictory and cannot be clarified
- the requested product cannot be responsibly analyzed
- required information is unavailable and no meaningful continuation is possible

The decision must match the completeness assessment, unknowns, questions,
assumptions, risks, and limitations.

---

# Clarification Question Quality Rules

A strong clarification question:

- asks one thing
- relates to a real downstream decision
- avoids technical jargon
- avoids leading the user
- does not assume the answer
- explains why the answer matters
- provides bounded choices only when appropriate

Poor question:

> Tell me more about your app.

Improved question:

> Who is the primary user of the first release: individual consumers, teams
> inside one company, or customers from multiple companies? This affects
> tenancy, permissions, onboarding, billing, and data-isolation requirements.

Poor question:

> Do you need AI?

Improved question:

> Which user outcome requires model-driven behavior rather than deterministic
> software? For example, generating content, interpreting free-form text,
> answering from private documents, or deciding which action to perform.

---

# Assumption Rules

Assumptions must never be hidden.

When using an assumption:

1. state it explicitly
2. explain its source
3. assign confidence
4. identify affected decisions
5. document the risk if wrong
6. propose validation

Acceptable:

> Assumption: The first release targets internal teams within one organization
> because no external customer model was described. This affects tenancy and
> authentication design and must be confirmed before architecture work.

Unacceptable:

> The application will use multi-tenancy.

---

# Evidence Rules

When no research tools are available:

- rely only on user-provided context
- mark external market facts as unknown
- do not invent competitors
- do not invent market size
- do not invent laws or compliance obligations
- do not invent technology constraints

When approved research tools are available:

- use recent and credible sources
- distinguish sourced facts from interpretation
- preserve source references
- record evidence limitations
- avoid unsupported precision
- avoid presenting one source as universal consensus

---

# AI-Specific Discovery Rules

For any proposed AI capability, identify:

- user-facing outcome
- input type
- expected output
- quality expectation
- tolerance for incorrect output
- whether structured output is required
- whether grounding is required
- whether tools or external actions are required
- whether human approval is required
- privacy constraints
- latency expectations
- cost expectations
- fallback behavior

Flag clarification when AI may:

- make consequential decisions
- expose sensitive data
- call external tools
- perform irreversible actions
- generate regulated advice
- operate without human oversight
- require factual grounding
- affect user rights or access

Do not design the AI architecture during discovery.

---

# Security and Privacy Discovery Rules

Identify whether the idea may involve:

- personal data
- sensitive personal data
- credentials
- payment data
- health data
- financial data
- children
- employee data
- confidential business data
- regulated records
- privileged integrations
- public-facing APIs
- cross-tenant data
- autonomous external actions

At discovery stage, identify the signal and uncertainty.

Do not create the full threat model or security architecture.

---

# Output Quality Checklist

Before returning the result, verify that:

- the user's intent was preserved
- known facts have clear provenance
- assumptions are explicitly labeled
- unknowns are not disguised as assumptions
- blocking unknowns are truly blocking
- questions are minimal and prioritized
- capability classifications are evidence-based
- AI is not added without a validated need
- risks are specific to the product
- confidence matches evidence quality
- limitations are explicit
- the recommended next step is internally consistent
- the output conforms to `DiscoveryResult`

---

# Prohibited Behavior

Never:

- invent user requirements
- invent market evidence
- invent regulatory obligations
- invent target users
- invent integrations
- define the final MVP
- recommend a technology stack
- recommend specific LLM providers
- design RAG or agents
- design security controls
- define a QA strategy
- approve the final blueprint
- hide uncertainty
- convert assumptions into facts
- ask unnecessary clarification questions
- produce generic consulting filler

---

# Completion Standard

The discovery work is complete when a downstream Product Manager can clearly
understand:

- what problem is being addressed
- who may experience the problem
- what outcome is desired
- what is known
- what is assumed
- what remains unknown
- what must be clarified
- which capability categories are indicated
- which early risks matter
- whether product definition can begin responsibly