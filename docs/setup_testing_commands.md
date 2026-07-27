# BuildWise AI — Setup, Testing, and Docker Commands

This is the operational command reference for the current implementation.
Run commands from the repository root unless a section says otherwise.

## 1. Prerequisites

- Python 3.12
- [`uv`](https://docs.astral.sh/uv/)
- Docker Desktop or Docker Engine with Compose
- Node.js 22.13 or newer
- npm
- Git

Verify:

```bash
uv --version
docker --version
docker compose version
node --version
npm --version
git --version
```

## 2. Install the backend

Install Python and the locked dependencies:

```bash
uv python install 3.12
uv sync --frozen
```

Use this only when intentionally updating dependencies:

```bash
uv lock
uv sync
```

Verify imports:

```bash
uv run python --version
uv run python -c "import crewai; print(crewai.__version__)"
uv run python -c "from buildwise.main import app; print(app.title)"
```

## 3. Configure the environment

Create the local environment file:

```bash
cp .env.example .env
```

Minimum provider configuration:

```env
OPENAI_API_KEY=your-openai-api-key
```

Optional live web research:

```env
SERPER_API_KEY=your-serper-api-key
```

Create a Serper key at [serper.dev](https://serper.dev/). Without it,
consultations can still run, but live Market & GTM research is omitted and
disclosed as an evidence limitation.

The active model defaults are:

```env
FAST_MODEL=openai/gpt-5-mini
PRIMARY_AGENT_MODEL=openai/gpt-5-mini
ARCHITECT_MODEL=openai/gpt-5.2
LEAD_REVIEWER_MODEL=openai/gpt-5.2
```

Keep unimplemented evaluation/fallback paths disabled:

```env
MODEL_FALLBACK_ENABLED=false
EVALUATION_ENABLED=false
CROSS_PROVIDER_EVALUATION_ENABLED=false
```

## 4. PostgreSQL for local backend execution

The example environment expects PostgreSQL on `localhost:5432`.

Start only PostgreSQL:

```bash
docker compose up -d postgres
```

Inspect status and health:

```bash
docker compose ps
docker compose exec postgres pg_isready -U buildwise -d buildwise
```

Follow or inspect logs:

```bash
docker compose logs -f postgres
docker compose logs --tail=100 postgres
```

Open a PostgreSQL shell:

```bash
docker compose exec postgres psql -U buildwise -d buildwise
```

Useful `psql` commands:

```text
\dt
\d consultations
\d artifacts
\d clarification_rounds
\d revisions
\d usage
\d blueprint_reports
\q
```

Stop PostgreSQL without deleting data:

```bash
docker compose stop postgres
```

## 5. Run the backend locally

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Run FastAPI on the port expected by the frontend:

```bash
uv run uvicorn buildwise.main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8080
```

Endpoints:

- `http://localhost:8080/health`
- `http://localhost:8080/ready`
- `http://localhost:8080/docs`
- `http://localhost:8080/redoc`
- `http://localhost:8080/api/v1`

Import/startup smoke test without running a server:

```bash
DEBUG=false APP_ENV=test CREWAI_TRACING_ENABLED=false \
  uv run python -c "from buildwise.main import app; print(app.title)"
```

## 6. Run the frontend

In a second terminal:

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

The default API URL is `http://localhost:8080/api/v1`. To override it:

```bash
cd web
cp .env.example .env.local
```

Set:

```env
NEXT_PUBLIC_BUILDWISE_API_URL=http://localhost:8080/api/v1
```

The frontend also supports changing and saving the API URL from its settings
control.

## 7. API verification commands

Health:

```bash
curl --fail --silent http://localhost:8080/health | python -m json.tool
```

Readiness:

```bash
curl --silent http://localhost:8080/ready | python -m json.tool
```

API version root:

```bash
curl --fail --silent http://localhost:8080/api/v1 | python -m json.tool
```

Request ID propagation:

```bash
curl --include \
  -H "X-Request-ID: buildwise-local-test-001" \
  http://localhost:8080/health
```

Start a consultation:

```bash
curl --fail-with-body \
  --request POST \
  --header "Content-Type: application/json" \
  --data '{
    "title": "Team Scheduler",
    "idea": "Build a scheduling product for distributed software teams.",
    "target_users": ["distributed software teams"],
    "known_features": ["timezone-aware availability"],
    "target_platforms": ["web"],
    "delivery_expectation": "mvp",
    "submission_channel": "api"
  }' \
  http://localhost:8080/api/v1/consultations
```

Save the returned consultation ID:

```bash
export BUILDWISE_CONSULTATION_ID="replace-with-consultation-id"
```

Check status:

```bash
curl --fail-with-body \
  "http://localhost:8080/api/v1/consultations/${BUILDWISE_CONSULTATION_ID}" \
  | python -m json.tool
```

Get a completed result:

```bash
curl --fail-with-body \
  "http://localhost:8080/api/v1/consultations/${BUILDWISE_CONSULTATION_ID}/result" \
  | python -m json.tool
```

Clarification submission requires the current round and question IDs returned
by the status endpoint:

```bash
curl --fail-with-body \
  --request POST \
  --header "Content-Type: application/json" \
  --data '{
    "clarification_round": 1,
    "answers": [
      {
        "question_id": "replace-with-question-id",
        "answer": "Small distributed product teams"
      }
    ]
  }' \
  "http://localhost:8080/api/v1/consultations/${BUILDWISE_CONSULTATION_ID}/clarifications"
```

## 8. Blueprint report storage

### Local filesystem

Default configuration:

```env
REPORT_STORAGE_BACKEND=filesystem
REPORT_STORAGE_PATH=data/reports
STORE_BLUEPRINT_JSON=false
```

Output:

```text
data/reports/{consultation_id}/blueprint.md
```

Set `STORE_BLUEPRINT_JSON=true` to also write `blueprint.json`.

Inspect local reports:

```bash
find data/reports -maxdepth 3 -type f -print
```

### S3

Create the bucket, then configure:

```env
REPORT_STORAGE_BACKEND=s3
S3_REPORT_BUCKET=your-buildwise-reports-bucket
AWS_REGION=ap-south-1
STORE_BLUEPRINT_JSON=false
```

Use the standard AWS credential chain. For temporary local credentials:

```env
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_SESSION_TOKEN=your-session-token
```

Prefer IAM roles or workload identity in deployed environments. The runtime
needs `s3:PutObject` for:

```text
arn:aws:s3:::your-buildwise-reports-bucket/consultations/*
```

Report keys:

```text
consultations/{consultation_id}/blueprints/v1/blueprint.md
consultations/{consultation_id}/blueprints/v1/blueprint.json
```

For MinIO, LocalStack, or another S3-compatible service:

```env
S3_ENDPOINT_URL=http://localhost:4566
```

## 9. Runtime safety settings

Defaults:

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

Crew and governed-tool executions consume persisted session budgets. API and
active-session limits are process-local and intended for the single-process
MVP.

Tracing and verbosity:

```env
CREWAI_TRACING_ENABLED=false
CREWAI_VERBOSE=false
```

Disable tracing for tests and offline local checks.

## 10. Backend tests and static checks

Run the CrewAI Flow smoke test:

```bash
DEBUG=false APP_ENV=test CREWAI_TRACING_ENABLED=false \
  uv run python -m buildwise.flows.smoke
```

Run all tests:

```bash
DEBUG=false APP_ENV=test \
CREWAI_TRACING_ENABLED=false CREWAI_DISABLE_TELEMETRY=true \
OTEL_SDK_DISABLED=true \
uv run pytest
```

Run concise tests:

```bash
DEBUG=false APP_ENV=test \
CREWAI_TRACING_ENABLED=false CREWAI_DISABLE_TELEMETRY=true \
OTEL_SDK_DISABLED=true \
uv run pytest -q
```

Run one file:

```bash
DEBUG=false APP_ENV=test \
CREWAI_TRACING_ENABLED=false CREWAI_DISABLE_TELEMETRY=true \
OTEL_SDK_DISABLED=true \
uv run pytest tests/unit/application/test_runtime_budget.py -q
```

Run one test by name:

```bash
DEBUG=false APP_ENV=test \
CREWAI_TRACING_ENABLED=false CREWAI_DISABLE_TELEMETRY=true \
OTEL_SDK_DISABLED=true \
uv run pytest -k "runtime_budget" -q
```

Coverage equivalent to the CI threshold:

```bash
DEBUG=false APP_ENV=test \
CREWAI_TRACING_ENABLED=false CREWAI_DISABLE_TELEMETRY=true \
OTEL_SDK_DISABLED=true \
uv run pytest \
  --cov=buildwise \
  --cov-report=term-missing \
  --cov-fail-under=70
```

Generate an HTML coverage report:

```bash
DEBUG=false APP_ENV=test \
CREWAI_TRACING_ENABLED=false CREWAI_DISABLE_TELEMETRY=true \
OTEL_SDK_DISABLED=true \
uv run pytest \
  --cov=buildwise \
  --cov-report=html
```

Open `htmlcov/index.html` after the command completes.

Ruff:

```bash
uv run ruff check src tests
uv run ruff format --check src tests
```

Apply safe lint fixes and formatting:

```bash
uv run ruff check --fix src tests
uv run ruff format src tests
```

Mypy:

```bash
uv run mypy src
```

Run the backend CI checks locally:

```bash
uv run ruff check src tests
uv run mypy src
DEBUG=false APP_ENV=test \
CREWAI_TRACING_ENABLED=false CREWAI_DISABLE_TELEMETRY=true \
OTEL_SDK_DISABLED=true \
uv run pytest --cov=buildwise --cov-report=term-missing --cov-fail-under=70
```

## 11. Frontend checks

Run from `web/`:

```bash
cd web
npm install
npm run lint
npm run build
npm test
```

Type-check without emitting files:

```bash
cd web
npx tsc --noEmit
```

Run the production frontend locally:

```bash
cd web
npm run build
npm run start
```

## 12. Full Docker Compose stack

The Compose API listens on container port `8000` and publishes the host
`PORT` value. To keep the frontend default of port `8080`:

```bash
PORT=8080 docker compose up --build
```

Detached:

```bash
PORT=8080 docker compose up --build --detach
```

Build without starting:

```bash
docker compose build
```

Start an already-built stack:

```bash
PORT=8080 docker compose up --detach
```

Inspect services:

```bash
docker compose ps
docker compose images
```

Follow logs:

```bash
docker compose logs -f api
docker compose logs -f postgres
docker compose logs -f
```

Show recent logs:

```bash
docker compose logs --tail=100 api
docker compose logs --tail=100 postgres
```

Check the Compose API:

```bash
curl --fail --silent http://localhost:8080/health | python -m json.tool
curl --silent http://localhost:8080/ready | python -m json.tool
```

Inspect the non-root runtime user:

```bash
docker compose exec api whoami
```

Expected:

```text
buildwise
```

Open a shell in the API container:

```bash
docker compose exec api sh
```

Restart services:

```bash
docker compose restart api
docker compose restart postgres
```

Stop and remove containers while preserving the database volume:

```bash
docker compose down
```

Remove containers and the PostgreSQL volume:

```bash
docker compose down --volumes
```

The last command permanently deletes the Compose-managed local database.

## 13. Build and run only the API image

Build:

```bash
docker build --tag buildwise-ai:local .
```

Run with a local SQLite database for isolated image testing:

```bash
docker run --rm \
  --name buildwise-api \
  --publish 8080:8000 \
  --env-file .env \
  --env APP_ENV=local \
  --env DATABASE_URL=sqlite:///./data/buildwise.db \
  --env REPORT_STORAGE_BACKEND=filesystem \
  --volume buildwise-api-data:/app/data \
  buildwise-ai:local
```

In another terminal:

```bash
curl --fail --silent http://localhost:8080/health | python -m json.tool
docker exec buildwise-api whoami
docker logs --follow buildwise-api
```

Stop:

```bash
docker stop buildwise-api
```

## 14. Docker diagnostics

Inspect image metadata:

```bash
docker image inspect buildwise-ai:local
docker history buildwise-ai:local
```

Inspect a running container:

```bash
docker inspect buildwise-api
docker stats buildwise-api
docker top buildwise-api
```

Show Compose configuration after environment interpolation:

```bash
docker compose config
```

Rebuild without cache:

```bash
docker compose build --no-cache api
```

Pull the latest PostgreSQL base image:

```bash
docker compose pull postgres
```

## 15. Security and dependency checks

Export production requirements and audit them:

```bash
uv export --frozen --no-dev \
  --format requirements-txt \
  --output-file /tmp/buildwise-requirements-audit.txt
uvx pip-audit --requirement /tmp/buildwise-requirements-audit.txt
```

Build and scan the local image with Trivy when installed:

```bash
docker build --tag buildwise-ai:security .
trivy image --severity HIGH,CRITICAL --ignore-unfixed buildwise-ai:security
```

Scan the repository with Gitleaks when installed:

```bash
gitleaks detect --source . --redact
```

The automated equivalents live in:

- `.github/workflows/ci.yml`
- `.github/workflows/security.yml`

## 16. Useful cleanup commands

Remove Python caches and test outputs:

```bash
find src tests -type d -name __pycache__ -prune -exec rm -rf {} +
rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
```

These paths contain generated local data. Review them before removal:

```text
data/reports
data/buildwise.db
```

Stop Compose services without deleting data:

```bash
docker compose down
```

Remove the isolated API data volume created in section 13:

```bash
docker volume rm buildwise-api-data
```

Remove the PostgreSQL Compose volume only when the data is no longer needed:

```bash
docker compose down --volumes
```

## 17. Common issues

### Frontend cannot reach the API

- Run the backend on port `8080`, or set
  `NEXT_PUBLIC_BUILDWISE_API_URL` to the actual API URL.
- Confirm `curl http://localhost:8080/health` succeeds.
- Restart the frontend after changing `.env.local`.

### Readiness reports provider configuration as false

- Set `OPENAI_API_KEY` when active models use the `openai/` prefix.
- Restart the backend after editing `.env`.

### PostgreSQL connection fails

```bash
docker compose ps
docker compose logs --tail=100 postgres
docker compose exec postgres pg_isready -U buildwise -d buildwise
```

For a backend running outside Docker, the database host is `localhost`. Inside
Compose, it is `postgres`.

### Serper-backed tools are unavailable

- Add `SERPER_API_KEY` to `.env`.
- Restart the backend.
- The workflow can continue without Serper when the requesting Agent permits
  continuation with a limitation.

### CrewAI telemetry attempts network access during tests

Use:

```bash
CREWAI_TRACING_ENABLED=false \
CREWAI_DISABLE_TELEMETRY=true \
OTEL_SDK_DISABLED=true \
uv run pytest -q
```

### API returns HTTP 429

Review:

```env
API_RATE_LIMIT_REQUESTS=30
API_RATE_LIMIT_WINDOW_SECONDS=60
MAX_ACTIVE_CONSULTATIONS=10
```

For multiple workers or replicas, replace the process-local limiter with a
shared implementation rather than only increasing these values.
