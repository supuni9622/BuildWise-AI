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

![BuildWise AI final flow](<BuildWise AI -final flow.drawio.png>)
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

For the implementation-backed browser-to-report lifecycle, see
[Current end-to-end implementation flow](docs/current_end_to_end_flow.md).

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

## Blueprint report storage

Generated blueprint Markdown is stored after blueprint assembly and before the
consultation is marked complete.

Local development uses the filesystem backend by default and requires no AWS
configuration:

```env
REPORT_STORAGE_BACKEND=filesystem
REPORT_STORAGE_PATH=data/reports
STORE_BLUEPRINT_JSON=false
```

The generated report is written to:

```text
data/reports/{consultation_id}/blueprint.md
```

To use S3, create the bucket first and configure:

```env
REPORT_STORAGE_BACKEND=s3
S3_REPORT_BUCKET=your-buildwise-reports-bucket
AWS_REGION=ap-south-1
STORE_BLUEPRINT_JSON=false
```

Provide credentials through the standard AWS credential chain. Local
credentials can be supplied through environment variables:

```env
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
# Required only for temporary credentials:
AWS_SESSION_TOKEN=your-session-token
```

For deployed environments, prefer an IAM role or workload identity instead of
long-lived access keys. The application needs `s3:PutObject` for:

```text
arn:aws:s3:::your-buildwise-reports-bucket/consultations/*
```

S3 reports use the fixed MVP key:

```text
consultations/{consultation_id}/blueprints/v1/blueprint.md
```

Set `STORE_BLUEPRINT_JSON=true` to also store `blueprint.json` under the same
versioned prefix. For MinIO, LocalStack, or another S3-compatible service, set
`S3_ENDPOINT_URL` to its endpoint.

PostgreSQL stores the report location and version-1 metadata in the
`blueprint_reports` table. The existing database initialization creates this
table automatically.

When using the filesystem backend in Docker, mount `data/reports` as a volume
if reports must survive container replacement.

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

The `.env.example` includes:
```
CREWAI_TRACING_ENABLED=true
```

BuildWise passes this value directly to its native CrewAI Flow and Crews.
Set it to `false` to disable tracing. Because the application setting is an
explicit runtime override, CrewAI CLI consent settings do not override it.

---
Runtime safety and capacity controls

The default local limits are:

```env
MAX_SESSION_TOKENS=120000
MAX_ESTIMATED_COST_USD=10.00
MAX_AGENT_EXECUTIONS=20
MAX_TOOL_CALLS=30
MAX_EXECUTION_SECONDS=900
MAX_RETRIES_PER_OPERATION=2

API_RATE_LIMIT_REQUESTS=30
API_RATE_LIMIT_WINDOW_SECONDS=60
MAX_ACTIVE_CONSULTATIONS=10
```

Crew and governed tool executions consume these persisted session budgets.
Tool calls are read-only, sanitized, bounded by per-tool timeouts/retries, and
rejected when their URL or input policy fails. The API limiter is process-local
and suitable for the single-process MVP. A multi-worker or horizontally scaled
deployment should replace it with a shared Redis/API-gateway limiter.

The application returns HTTP `429` when either the per-client request limit or
the process-wide active-consultation limit is reached.

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
