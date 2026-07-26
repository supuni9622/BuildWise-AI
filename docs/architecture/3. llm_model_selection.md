# BuildWise AI — Model Provider Strategy and Cost Analysis

## Purpose

This document explains:

1. Why Claude was initially selected as the primary provider.
2. Why OpenAI may ultimately be the better choice for the first BuildWise release.
3. Recommended model routing.
4. Cost implications.
5. Future multi-provider strategy.

---

# 1. BuildWise Workload Characteristics

BuildWise AI is not a simple chatbot.

It is a multi-agent consulting workflow that generates large structured outputs.

Typical execution:

```text
Discovery
↓
Clarification
↓
Product Definition
↓
Business Analysis
↓
Architecture
↓
AI Design
↓
Security Design
↓
QA Strategy
↓
GTM Strategy
↓
Review
↓
Blueprint Generation
```

This means BuildWise workloads involve:

- Long prompts
- Long structured outputs
- Cross-document reasoning
- Agent-to-agent context handoffs
- Requirement traceability
- Large Pydantic schemas
- Extensive Markdown generation
- Multi-stage synthesis

Output token cost therefore matters significantly.

---

# 2. Initial Recommendation — Claude as Primary Provider

Initial recommendation:

```env
ANTHROPIC_API_KEY=

PRIMARY_AGENT_MODEL=anthropic/claude-sonnet-5
ARCHITECT_MODEL=anthropic/claude-sonnet-5
LEAD_REVIEWER_MODEL=anthropic/claude-opus-4-8
FAST_MODEL=anthropic/claude-haiku-4-5
```

---

# 3. Why Claude Was Initially Selected

The recommendation was not based on OpenAI being weak.

Claude was initially chosen because BuildWise heavily benefits from:

## Long Structured Reasoning

BuildWise produces:

- Product documents
- Requirements
- Architecture reports
- AI strategy documents
- Security reports
- QA plans
- GTM reports
- Final blueprints

Claude models are particularly strong at:

- long-form reasoning
- large structured outputs
- maintaining formatting consistency
- following instructions precisely
- multi-document synthesis

---

## Large Context Windows

Claude Sonnet 5 and Opus 4.8 support:

```text
1M token context windows
```

This is valuable because BuildWise eventually passes large specialist outputs between agents.

---

## Better Multi-Document Analysis

The Lead Reviewer must:

- compare all specialist outputs
- detect contradictions
- detect missing sections
- identify overengineering
- request targeted revisions

Claude models perform particularly well at these tasks.

---

## Simpler Architecture

Using only one provider simplifies:

- API configuration
- retry handling
- provider errors
- token tracking
- cost estimation
- debugging
- deployment

For a project that must be built in:

```text
2–4 days
```

simplicity is valuable.

---

# 4. Claude Model Routing

## Fast Tier

```env
FAST_MODEL=anthropic/claude-haiku-4-5
```

Used for:

- Completeness Evaluator
- Capability Classifier
- Clarification Generator
- Output Repair
- Lightweight semantic validation

---

## Balanced Tier

```env
PRIMARY_AGENT_MODEL=anthropic/claude-sonnet-5
```

Used for:

- Discovery Analyst
- Product Manager
- Business Analyst
- Market and GTM Strategist
- Security Architect
- QA Architect
- Specialist Planner

---

## Architecture Tier

```env
ARCHITECT_MODEL=anthropic/claude-sonnet-5
```

Used for:

- Solution Architect
- AI Architect

---

## Reviewer Tier

```env
LEAD_REVIEWER_MODEL=anthropic/claude-opus-4-8
```

Used only for:

- Lead Reviewer

---

# 5. Why Not Use Opus Everywhere?

Opus is expensive.

The Solution Architect and AI Architect do not require frontier-level reasoning.

They produce:

- product architectures
- integrations
- deployment recommendations
- AI workflow designs

These are sophisticated tasks but not:

- scientific research
- complex coding agents
- theorem proving
- advanced autonomous reasoning

Using Opus everywhere would significantly increase cost.

---

## Recommended Approach

Use:

```text
Sonnet → specialists
Opus → reviewer only
```

The reviewer runs only once or twice.

Therefore Opus cost remains controlled.

---

# 6. Claude Pricing

## Current Pricing

| Tier | Model | Input | Output |
|------|--------|-------:|--------:|
| Fast | Claude Haiku 4.5 | $1 | $5 |
| Balanced | Claude Sonnet 5 | $2 | $10 |
| Reviewer | Claude Opus 4.8 | $5 | $25 |

Pricing per:

```text
1M tokens
```

Note:

Sonnet promotional pricing ends:

```text
31 August 2026
```

After that:

```text
$3 input
$15 output
```

---

# 7. Cost Re-Evaluation

After evaluating BuildWise more deeply, cost becomes extremely important.

BuildWise is:

```text
output heavy
```

Multiple agents generate:

- PRDs
- Requirements
- Architectures
- GTM reports
- QA reports
- Security reports
- Final blueprints

Output tokens dominate costs.

---

# 8. OpenAI Cost Comparison

## Current Pricing

| BuildWise Tier | OpenAI | Input | Output |
|---------------|---------|-------:|--------:|
| Fast | GPT-5.4 Nano | $0.20 | $1.25 |
| Balanced | GPT-5.4 Mini | $0.75 | $4.50 |
| Architecture | GPT-5.6 Luna | $1 | $6 |
| Reviewer | GPT-5.6 Terra | $2.50 | $15 |

---

## Claude Comparison

| BuildWise Tier | Claude | Input | Output |
|---------------|---------|-------:|--------:|
| Fast | Haiku 4.5 | $1 | $5 |
| Balanced | Sonnet 5 | $2 | $10 |
| Architecture | Sonnet 5 | $2 | $10 |
| Reviewer | Opus 4.8 | $5 | $25 |

---

# 9. Approximate Savings Using OpenAI

Compared with Claude:

## Fast Tier

```text
75–80% cheaper
```

---

## Balanced Agents

```text
55–63% cheaper
```

---

## Architecture Tier

```text
40–50% cheaper
```

---

## Reviewer Tier

```text
40–50% cheaper
```

---

# 10. Tokenization Difference

Anthropic documentation also notes that recent Claude models may generate approximately:

```text
~30% more tokens
```

for equivalent content.

For BuildWise this matters because:

```text
Large reports
+
Large outputs
+
Many agents
=
Higher effective cost
```

---

# 11. Final Recommendation for V1

Although Claude may provide slightly stronger long-form synthesis, BuildWise V1 should prioritize:

- lower cost
- faster iteration
- easier debugging
- simpler deployment
- single-provider integration

Therefore the recommended provider for V1 becomes:

# OpenAI

---

# 12. Recommended V1 Configuration

```env
OPENAI_API_KEY=

FAST_MODEL=openai/gpt-5.4-nano
PRIMARY_AGENT_MODEL=openai/gpt-5.4-mini
ARCHITECT_MODEL=openai/gpt-5.6-luna
LEAD_REVIEWER_MODEL=openai/gpt-5.6-terra
```

---

# 13. OpenAI Routing Strategy

## GPT-5.4 Nano

Used for:

- Completeness Evaluator
- Capability Classifier
- Clarification Generator
- Output Repair
- Semantic validations

---

## GPT-5.4 Mini

Used for:

- Discovery Analyst
- Product Manager
- Business Analyst
- Market and GTM Strategist
- Security Architect
- QA Architect
- Specialist Planner

---

## GPT-5.6 Luna

Used for:

- Solution Architect
- AI Architect

---

## GPT-5.6 Terra

Used for:

- Lead Reviewer

---

# 14. Future Multi-Provider Strategy

BuildWise architecture should remain provider agnostic.

Future experiments may include:

## Hybrid Mode

```text
Fast tasks → GPT
Most specialists → GPT
Lead Reviewer → Claude Opus
```

or

```text
All specialists → GPT
Lead Reviewer → Sonnet
```

This can be implemented later without architectural changes.

---

# 15. Final Decision

## V1 Recommendation

```env
FAST_MODEL=openai/gpt-5.4-nano
PRIMARY_AGENT_MODEL=openai/gpt-5.4-mini
ARCHITECT_MODEL=openai/gpt-5.6-luna
LEAD_REVIEWER_MODEL=openai/gpt-5.6-terra
```

Reasons:

- substantially cheaper
- easier iteration
- simpler tracking
- sufficient capability
- ideal for a 2–4 day portfolio project

---

# 16. Claude Recommendation (Alternative)

If quality becomes more important than cost:

```env
FAST_MODEL=anthropic/claude-haiku-4-5
PRIMARY_AGENT_MODEL=anthropic/claude-sonnet-5
ARCHITECT_MODEL=anthropic/claude-sonnet-5
LEAD_REVIEWER_MODEL=anthropic/claude-opus-4-8
```

Reasons:

- stronger long-form synthesis
- stronger structured reasoning
- excellent multi-document review
- superior reviewer capabilities

---

# 17. Final Verdict

## Best Quality

```text
Claude
```

## Best Cost

```text
OpenAI
```

## Best Choice for BuildWise V1

```text
OpenAI
```

because BuildWise is:

- multi-agent
- output-heavy
- portfolio-focused
- time-constrained
- budget-sensitive

and GPT models provide more than enough capability while significantly reducing cost.