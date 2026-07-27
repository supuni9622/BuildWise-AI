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

![BuildWise AI -Full flow](<BuildWise AI -Full flow.drawio.png>)
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
uv python install 3.12
uv run python --version
uv sync
uv lock
cp .env.example .env


uv run uvicorn buildwise.main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8080
```

Add the provider and research credentials to `.env` before starting the
backend:

```env
OPENAI_API_KEY=your-openai-api-key
SERPER_API_KEY=your-serper-api-key
```

Create a Serper key at [serper.dev](https://serper.dev/).
`SERPER_API_KEY` enables live web and competitor research for the Market &
GTM Strategist. Restart the backend after adding or changing the key.

Serper is optional for the overall workflow. Without it, BuildWise continues
with an explicit market-research evidence gap instead of using live web
search.

## Frontend

Keep the backend running on port `8080`. In a second terminal, run:

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

The frontend connects to `http://localhost:8080/api/v1` by default. To use a
different backend URL, copy the example environment file and update it:

```bash
cd web
cp .env.example .env.local
```

```env
NEXT_PUBLIC_BUILDWISE_API_URL=http://localhost:8080/api/v1
```

Check the API:
```
curl -s http://localhost:8080/health | python -m json.tool
```
Expected shape:
```json
{
  "status": "ok",
  "service": "BuildWise AI",
  "version": "0.1.0",
  "checks": {}
}
```
Check readiness:
```
curl -s http://localhost:8080/ready | python -m json.tool
```
Expected with a valid API key and working database:
```json
{
  "status": "ready",
  "service": "BuildWise AI",
  "version": "0.1.0",
  "checks": {
    "database": true,
    "llm_provider_configuration": true
  }
}
```
Check API version root:
```curl
curl -s http://localhost:8080/api/v1 | python -m json.tool
```
Expected:
```json
{
  "name": "BuildWise AI",
  "version": "0.1.0",
  "api_version": "v1",
  "status": "available"
}
```
Check request ID propagation:
```
curl -i \
  -H "X-Request-ID: buildwise-local-test-001" \
  http://localhost:8080/health
```

The response should include:
```
X-Request-ID: buildwise-local-test-001
```
---

Run the CrewAI smoke Flow
```bash
uv run python -m buildwise.flows.smoke
```

Expected:

BuildWise CrewAI smoke flow completed.

This verifies:

CrewAI imports correctly
A typed Flow state can be initialized
@start() executes
@listen() receives the previous stage output
Flow state can be mutated
kickoff() completes
No LLM call is needed for the foundation smoke test

CrewAI Flows support structured state and event-driven transitions, which we will use heavily from Phase 2 onward.

---

# Docker

```bash
docker build -t buildwise-ai .
docker run -p 8000:8000 buildwise-ai
```

---
Enable CrewAI tracing

The .env.example already includes:
```
CREWAI_TRACING_ENABLED=true
```

You can also configure tracing through the CrewAI CLI:
```bash
uv run crewai traces enable
```
Check status:
```bash
uv run crewai traces status
```
Disable when required:
```bash
uv run crewai traces disable
```

---
Run quality checks
Ruff lint
```bash
uv run ruff check src tests
```
Apply safe automatic fixes:
```bash
uv run ruff check src tests --fix
```
Ruff format
```bash
uv run ruff format src tests
```
Check without modifying:
```bash
uv run ruff format --check src tests
```
Mypy
```bash
uv run mypy src
```
Application import smoke test
```bash
uv run python -c "from buildwise.main import app; print(app.title)"
```

Expected:

BuildWise AI
Pytest

After Claude Code generates the tests from:

docs/phase-0-test-cases.md

run:
```bash
uv run pytest
```

With coverage:
```bash
uv run pytest \
  --cov=buildwise \
  --cov-report=term-missing \
  --cov-report=html
```

The CI workflow temporarily skips Pytest when no test_*.py files exist. Once Claude generates them, CI will detect and execute them automatically.

---

# start only postgress with docker
```bash
docker compose up -d postgres
```
Check its health:
```bash
docker compose ps
```

Follow PostgreSQL logs:
```bash
docker compose logs -f postgres
```

# Start / stop the app locally

Start PostgreSQL and the API:
```bash
docker compose up -d postgres && uv run uvicorn buildwise.main:app --reload --host 0.0.0.0 --port 8080
```

Stop the API and PostgreSQL:
```bash
pkill -f "uvicorn buildwise.main:app" && docker compose stop postgres
```

# Run with Docker
API using local SQLite

Build:
```bash
docker build -t buildwise-ai:phase-0 .
```
Run:
```bash
docker run --rm \
  --name buildwise-api \
  --env-file .env \
  -p 8000:8000 \
  buildwise-ai:phase-0
```
Check:
```bash
curl http://localhost:8080/health
```
Inspect the runtime user:
```bash
docker exec buildwise-api whoami
```

Expected:

buildwise

The container does not run as root.

API and PostgreSQL

Start:
```bash
docker compose up --build
```
Run detached:
```bash
docker compose up --build -d
```
Check services:
```bash
docker compose ps
```
Check API logs:
```bash
docker compose logs -f api
```
Check PostgreSQL logs:
```bash
docker compose logs -f postgres
```
Check health:
```bash
curl -s http://localhost:8080/health | python -m json.tool
```
Check readiness:
```bash
curl -s http://localhost:8080/ready | python -m json.tool
```
Stop:
```bash
docker compose down
```
Remove the database volume:
```bash
docker compose down -v
```
---
# Project Goals

- Learn CrewAI deeply
- Build a realistic AI product
- Demonstrate AI Engineering practices
- Showcase agent orchestration
- Generate real business value

# Practical model routing

Use the models as follows:
```
Claude Haiku 4.5
├── Completeness Evaluator
├── Preliminary Capability Classifier
├── Clarification Question Generator
├── Output Repair Processor
└── Lightweight semantic consistency checks

Claude Sonnet 5
├── Discovery Analyst
├── Product Manager
├── Business Analyst
├── Market and GTM Strategist
├── Solution Architect
├── AI Architect
├── Security Architect
├── QA and Evaluation Architect
└── Specialist Planner, when LLM assistance is needed

Claude Opus 4.8
└── Lead Reviewer
```
The Cost Aggregator, validators, budget controller, Blueprint Assembler, and Markdown Renderer should not use any of these models unless their deterministic checks fail and a specifically bounded repair is required.

## Open ai
```
Routing
GPT-5.4 Nano
├── Completeness Evaluator
├── Capability Classifier
├── Clarification Question Generator
├── Output Repair
└── Semantic validation assistance

GPT-5.4 Mini
├── Discovery Analyst
├── Product Manager
├── Business Analyst
├── Market and GTM Strategist
├── Security Architect
├── QA and Evaluation Architect
└── Specialist Planner

GPT-5.6 Luna
├── Solution Architect
└── AI Architect

GPT-5.6 Terra
└── Lead Reviewer
```

# Full architectural Flow

![alt text](<AI consulting process flowchart.png>)

Locked architecture direction
FastAPI
   ↓
API routers
   ↓
CrewAI Flow runtime
   ↓
Focused Crews
   ↓
Specialized Agents
   ↓
Tools / MCPs / Skills / Knowledge
   ↓
Structured Pydantic outputs
   ↓
Persistence / Reporting / API response

# Core rules

## Flows own orchestration
state
routing
branching
pause and resume
human clarification
execution order
calling crews

## Crews own focused units of reasoning
discovery
product definition
requirements
architecture
specialist planning
review

## Agents remain specialists
no generic “do everything” agent
clear roles
limited tools
controlled delegation

## Tasks use structured outputs
output_pydantic
task guardrails
explicit expected outputs
no fragile manual JSON parsing

## FastAPI remains the transport layer
accepts requests
starts or resumes flows
exposes status and results
streams Flow events
does not contain orchestration logic

## PostgreSQL remains the business system of record
sessions
artifacts
user clarification
final blueprints
execution metadata

## CrewAI persistence is runtime persistence
Flow state recovery
resume/fork semantics
human-in-the-loop continuation

## Skills provide methodology
product management procedures
business analysis procedures
architecture review methodology
security and QA checklists

## Knowledge provides reference material
templates
standards
internal guidance
reusable factual documents

## Tools provide controlled actions
web search
web scraping
GitHub search
future MCP access
persistence or document tools only when justified
