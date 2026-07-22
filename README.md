# BuildWise-AI - AI Product Consulting Board

> Transform vague product ideas into build-ready solution blueprints.


BuildWise AI is a CrewAI-powered product consulting board that transforms vague product ideas into market-aware, secure, testable, cost-conscious, and build-ready product blueprints. It uses adaptive human discovery, dynamic specialist routing, tool-enabled research, structured multi-agent collaboration, bounded reflection, guardrails, traceability, and cost-aware execution.

BuildWise AI is a CrewAI-powered multi-agent consulting board that helps users convert incomplete ideas into:

- Product Requirements
- Market Insights
- Solution Architectures
- AI Strategies
- Security Designs
- Implementation Roadmaps

---

# Features

## Human-in-the-loop Discovery

Users do not need to know how to write requirements.

The system dynamically asks clarification questions only when necessary.

---

## Multi-Agent Consulting Board

Roles:

- Discovery Analyst
- Product Manager
- Business Analyst
- Solution Architect
- AI Architect
- Security Architect
- Engineering Lead
- QA Architect
- Market Analyst
- Lead Reviewer

---

## Dynamic Specialist Routing

Only relevant specialists are executed.

---

## Structured Product Blueprint Generation

Outputs:

- PRD
- Architecture
- AI Strategy
- Risks
- Delivery Plan

---

## CrewAI Capabilities Used

- Flows
- Crews
- Human Feedback
- Parallel Execution
- Structured Outputs
- Tool Usage
- Tracing
- Reflection Loops

---

# Architecture

```text
Idea
 ↓
Discovery
 ↓
Human Questions
 ↓
Requirements
 ↓
Specialists
 ↓
Review
 ↓
Blueprint
```

---

# Tech Stack

- Python 3.12
- FastAPI
- CrewAI v1.15.5
- Pydantic v2
- SQLite/Postgres
- Structlog
- Docker
- GitHub Actions

---

# Local Development

```bash
uv sync
cp .env.example .env
uv run uvicorn src.buildwise.main:app --reload
```

---

# Docker

```bash
docker build -t buildwise-ai .
docker run -p 8000:8000 buildwise-ai
```

---

# Project Goals

- Learn CrewAI deeply
- Build a realistic AI product
- Demonstrate AI Engineering practices
- Showcase agent orchestration
- Generate real business value