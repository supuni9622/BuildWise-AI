# BuildWise AI — Development, Testing, and Docker Command Guide

## Purpose

This document contains the commands required to:

- install the project
- configure the environment
- run BuildWise locally
- run PostgreSQL
- run the CrewAI smoke Flow
- run linting and type checks
- run tests and coverage
- build and run Docker containers
- inspect logs and container health
- connect to PostgreSQL
- validate OpenAI and Anthropic integrations
- clean up the local environment

Run all commands from the project root, where these files are located:

```text
pyproject.toml
docker-compose.yml
Dockerfile
.env.example
```

---

# 1. Prerequisites

Ensure the following tools are installed:

```text
Python 3.12
uv
Docker Desktop
Docker Compose
Git
```

Verify them:

```bash
python3 --version
```

```bash
uv --version
```

```bash
docker --version
```

```bash
docker compose version
```

```bash
git --version
```

---

# 2. Install Python 3.12

Install Python 3.12 through `uv`:

```bash
uv python install 3.12
```

Verify the installed interpreter:

```bash
uv python list
```

---

# 3. Create the Environment File

Copy the committed environment template:

```bash
cp .env.example .env
```

Open `.env` and add the required provider keys:

```env
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

For initial development, keep Claude evaluation disabled:

```env
EVALUATION_ENABLED=false
CROSS_PROVIDER_EVALUATION_ENABLED=false
EVALUATION_SAMPLE_RATE=0.0
```

Keep automatic model fallback disabled until the fallback runtime has been implemented:

```env
MODEL_FALLBACK_ENABLED=false
```

The active workflow should initially use OpenAI:

```env
FAST_MODEL=openai/gpt-5-mini
PRIMARY_AGENT_MODEL=openai/gpt-5-mini
ARCHITECT_MODEL=openai/gpt-5.2
LEAD_REVIEWER_MODEL=openai/gpt-5.2
```

Claude remains configured for later evaluation:

```env
EVALUATION_MODEL=anthropic/claude-sonnet-5
STRONG_EVALUATION_MODEL=anthropic/claude-opus-4-8
```

---

# 4. Install Project Dependencies

Create or update the lock file:

```bash
uv lock
```

Install production and development dependencies:

```bash
uv sync --all-groups
```

For future installations using the committed lock file:

```bash
uv sync --frozen --all-groups
```

Verify that the project virtual environment exists:

```bash
ls -la .venv
```

---

# 5. Verify Installed Dependencies

## Verify Python

```bash
uv run python --version
```

## Verify CrewAI

```bash
uv run python -c "import crewai; print(crewai.__version__)"
```

## Verify FastAPI

```bash
uv run python -c "import fastapi; print(fastapi.__version__)"
```

## Verify OpenAI SDK

```bash
uv run python -c "import openai; print('OpenAI SDK installed successfully')"
```

## Verify Anthropic SDK

```bash
uv run python -c "import anthropic; print('Anthropic SDK installed successfully')"
```

## Verify both providers together

```bash
uv run python -c "import openai, anthropic; print('OpenAI and Anthropic SDKs installed successfully')"
```

## Verify the BuildWise package import

```bash
uv run python -c "import buildwise; print('BuildWise package imported successfully')"
```

## Verify the FastAPI application import

```bash
uv run python -c "from buildwise.main import app; print(app.title)"
```

---

# 6. Local Development with Docker PostgreSQL

The local `.env` uses PostgreSQL on:

```text
localhost:5432
```

Start only PostgreSQL through Docker:

```bash
docker compose up -d postgres
```

Check the container status:

```bash
docker compose ps
```

Check PostgreSQL health directly:

```bash
docker compose exec postgres \
  pg_isready -U buildwise -d buildwise
```

Follow PostgreSQL logs:

```bash
docker compose logs -f postgres
```

Show only the latest PostgreSQL logs:

```bash
docker compose logs --tail=100 postgres
```

---

# 7. Run the FastAPI Application Locally

Start PostgreSQL first:

```bash
docker compose up -d postgres
```

Then start the API outside Docker:

```bash
uv run uvicorn buildwise.main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000
```

The API should be available at:

```text
http://localhost:8000
```

Useful endpoints:

```text
http://localhost:8000/health
http://localhost:8000/ready
http://localhost:8000/docs
http://localhost:8000/redoc
```

Open Swagger documentation on macOS:

```bash
open http://localhost:8000/docs
```

Open ReDoc on macOS:

```bash
open http://localhost:8000/redoc
```

---

# 8. Test Health and Readiness Endpoints

## Health endpoint

```bash
curl http://localhost:8000/health
```

Pretty-print the response:

```bash
curl -s http://localhost:8000/health | python -m json.tool
```

## Readiness endpoint

```bash
curl http://localhost:8000/ready
```

Pretty-print the response:

```bash
curl -s http://localhost:8000/ready | python -m json.tool
```

## Show response headers

```bash
curl -i http://localhost:8000/health
```

```bash
curl -i http://localhost:8000/ready
```

Use this to verify that request or correlation IDs are included in response headers.

---

# 9. Run the CrewAI Smoke Flow

Run the Phase 0 CrewAI Flow:

```bash
uv run python -m buildwise.flows.smoke
```

This verifies:

- BuildWise package imports
- CrewAI initialization
- Flow state initialization
- `@start()` execution
- `@listen()` execution
- Flow completion
- no external LLM call is required

Run it with CrewAI tracing enabled:

```bash
CREWAI_TRACING_ENABLED=true \
uv run python -m buildwise.flows.smoke
```

Run it with tracing disabled:

```bash
CREWAI_TRACING_ENABLED=false \
uv run python -m buildwise.flows.smoke
```

---

# 10. CrewAI Tracing Commands

Check the CrewAI tracing status:

```bash
uv run crewai traces status
```

Enable CrewAI tracing:

```bash
uv run crewai traces enable
```

Disable CrewAI tracing:

```bash
uv run crewai traces disable
```

The application environment can also control tracing:

```env
CREWAI_TRACING_ENABLED=true
```

---

# 11. Ruff Linting Commands

Run Ruff against the source and test directories:

```bash
uv run ruff check src tests
```

Apply safe automatic fixes:

```bash
uv run ruff check src tests --fix
```

Show detailed lint output:

```bash
uv run ruff check src tests --show-fixes
```

Run Ruff against only the application source:

```bash
uv run ruff check src
```

Run Ruff against a specific file:

```bash
uv run ruff check src/buildwise/main.py
```

---

# 12. Ruff Formatting Commands

Check formatting without modifying files:

```bash
uv run ruff format --check src tests
```

Format all source and test files:

```bash
uv run ruff format src tests
```

Check one file:

```bash
uv run ruff format --check src/buildwise/main.py
```

Format one file:

```bash
uv run ruff format src/buildwise/main.py
```

---

# 13. Mypy Commands

Run strict type checking:

```bash
uv run mypy src
```

Run mypy against a specific package:

```bash
uv run mypy src/buildwise
```

Run mypy against a specific file:

```bash
uv run mypy src/buildwise/main.py
```

Show error codes:

```bash
uv run mypy src --show-error-codes
```

---

# 14. Pytest Commands

The project may initially contain no generated test files. In that case, pytest may report that no tests were collected.

## Run all tests

```bash
uv run pytest
```

## Run tests with verbose output

```bash
uv run pytest -v
```

## Run tests with very verbose output

```bash
uv run pytest -vv
```

## Stop after the first failure

```bash
uv run pytest -x
```

## Stop after a specific number of failures

```bash
uv run pytest --maxfail=3
```

## Show print statements and live output

```bash
uv run pytest -s
```

## Run one test file

```bash
uv run pytest tests/path/to/test_file.py -v
```

Example:

```bash
uv run pytest tests/unit/test_settings.py -v
```

## Run one test case

```bash
uv run pytest \
  tests/path/to/test_file.py::test_case_name \
  -v
```

Example:

```bash
uv run pytest \
  tests/unit/test_settings.py::test_default_settings \
  -v
```

## Run tests matching a keyword

```bash
uv run pytest -k "settings"
```

## Run unit tests

```bash
uv run pytest -m unit
```

## Run integration tests

```bash
uv run pytest -m integration
```

## Run slow tests

```bash
uv run pytest -m slow
```

## Exclude slow tests

```bash
uv run pytest -m "not slow"
```

## Run unit tests while excluding slow tests

```bash
uv run pytest -m "unit and not slow"
```

---

# 15. Coverage Commands

Run tests with terminal coverage:

```bash
uv run pytest \
  --cov=buildwise \
  --cov-report=term-missing
```

Generate both terminal and HTML coverage reports:

```bash
uv run pytest \
  --cov=buildwise \
  --cov-report=term-missing \
  --cov-report=html
```

Open the generated HTML report on macOS:

```bash
open htmlcov/index.html
```

Generate an XML coverage report for CI:

```bash
uv run pytest \
  --cov=buildwise \
  --cov-report=xml
```

Generate all common coverage reports:

```bash
uv run pytest \
  --cov=buildwise \
  --cov-report=term-missing \
  --cov-report=html \
  --cov-report=xml
```

---

# 16. Run All Local Quality Checks

Run linting, formatting, type checking, import verification, and the CrewAI smoke Flow:

```bash
uv run ruff check src tests && \
uv run ruff format --check src tests && \
uv run mypy src && \
uv run python -c "from buildwise.main import app; print(app.title)" && \
uv run python -m buildwise.flows.smoke
```

Once actual tests exist:

```bash
uv run ruff check src tests && \
uv run ruff format --check src tests && \
uv run mypy src && \
uv run pytest && \
uv run python -m buildwise.flows.smoke
```

Run the complete provider import verification:

```bash
uv run python -c "import openai, anthropic, crewai; print('Provider and CrewAI imports passed')"
```

---

# 17. Validate Docker Compose

Validate the Compose YAML and resolved configuration:

```bash
docker compose config
```

Validate without printing the resolved configuration:

```bash
docker compose config --quiet
```

Be careful when sharing `docker compose config` output because resolved environment values may include secrets.

List Compose services:

```bash
docker compose config --services
```

List Compose volumes:

```bash
docker compose config --volumes
```

---

# 18. Build Docker Images

Build all services:

```bash
docker compose build
```

Build only the API image:

```bash
docker compose build api
```

Build with updated dependencies:

```bash
docker compose build --pull
```

Force a clean build without cached layers:

```bash
docker compose build --no-cache
```

Force a clean API-only build:

```bash
docker compose build --no-cache api
```

---

# 19. Start the Full Docker Stack

Build and start all services:

```bash
docker compose up --build
```

Build and start all services in detached mode:

```bash
docker compose up -d --build
```

Start existing images without rebuilding:

```bash
docker compose up -d
```

Start only PostgreSQL:

```bash
docker compose up -d postgres
```

Start only the API:

```bash
docker compose up -d api
```

The API service depends on PostgreSQL being healthy.

---

# 20. Inspect Docker Service Status

Show service status:

```bash
docker compose ps
```

Show all containers, including stopped containers:

```bash
docker compose ps -a
```

Show Docker images used by the project:

```bash
docker compose images
```

Show currently running Docker containers:

```bash
docker ps
```

Show all Docker containers:

```bash
docker ps -a
```

---

# 21. Docker Log Commands

Follow all service logs:

```bash
docker compose logs -f
```

Follow API logs:

```bash
docker compose logs -f api
```

Follow PostgreSQL logs:

```bash
docker compose logs -f postgres
```

Show the last 100 API log lines:

```bash
docker compose logs --tail=100 api
```

Show the last 100 PostgreSQL log lines:

```bash
docker compose logs --tail=100 postgres
```

Show timestamps:

```bash
docker compose logs -f --timestamps api
```

Show logs generated during the last 10 minutes:

```bash
docker compose logs --since=10m api
```

---

# 22. Test the Dockerized Application

Start the stack:

```bash
docker compose up -d --build
```

Check container health:

```bash
docker compose ps
```

Test the health endpoint:

```bash
curl http://localhost:8000/health
```

Pretty-print the health response:

```bash
curl -s http://localhost:8000/health | python -m json.tool
```

Test the readiness endpoint:

```bash
curl http://localhost:8000/ready
```

Pretty-print the readiness response:

```bash
curl -s http://localhost:8000/ready | python -m json.tool
```

Open Swagger documentation on macOS:

```bash
open http://localhost:8000/docs
```

---

# 23. Execute Commands Inside the API Container

Open a shell inside the API container:

```bash
docker compose exec api sh
```

Check Python:

```bash
docker compose exec api python --version
```

Check CrewAI:

```bash
docker compose exec api \
  python -c "import crewai; print(crewai.__version__)"
```

Check the BuildWise application import:

```bash
docker compose exec api \
  python -c "from buildwise.main import app; print(app.title)"
```

Verify OpenAI:

```bash
docker compose exec api \
  python -c "import openai; print('OpenAI SDK installed')"
```

Verify Anthropic:

```bash
docker compose exec api \
  python -c "import anthropic; print('Anthropic SDK installed')"
```

Verify both providers:

```bash
docker compose exec api \
  python -c "import openai, anthropic; print('Both provider SDKs installed')"
```

Run the CrewAI smoke Flow:

```bash
docker compose exec api \
  python -m buildwise.flows.smoke
```

Print selected environment variables without printing API keys:

```bash
docker compose exec api \
  python -c "
import os
for name in [
    'APP_ENV',
    'DATABASE_URL',
    'FAST_MODEL',
    'PRIMARY_AGENT_MODEL',
    'ARCHITECT_MODEL',
    'LEAD_REVIEWER_MODEL',
    'EVALUATION_MODEL',
    'MODEL_FALLBACK_ENABLED',
    'EVALUATION_ENABLED',
]:
    print(f'{name}={os.getenv(name)}')
"
```

---

# 24. Run One-Off Docker Commands

Run the CrewAI smoke Flow in a temporary container:

```bash
docker compose run --rm api \
  python -m buildwise.flows.smoke
```

Verify the FastAPI application import:

```bash
docker compose run --rm api \
  python -c "from buildwise.main import app; print(app.title)"
```

Verify both provider SDKs:

```bash
docker compose run --rm api \
  python -c "import openai, anthropic; print('Provider SDKs available')"
```

The production Docker image may not contain development dependencies such as:

```text
pytest
ruff
mypy
```

Run those locally or in CI unless the Dockerfile explicitly installs the development dependency group.

---

# 25. Restart Docker Services

Restart all services:

```bash
docker compose restart
```

Restart only the API:

```bash
docker compose restart api
```

Restart only PostgreSQL:

```bash
docker compose restart postgres
```

Recreate the API container after configuration changes:

```bash
docker compose up -d --force-recreate api
```

Rebuild and recreate the API:

```bash
docker compose up -d --build --force-recreate api
```

---

# 26. Stop Docker Services

Stop services without removing containers:

```bash
docker compose stop
```

Stop only the API:

```bash
docker compose stop api
```

Stop only PostgreSQL:

```bash
docker compose stop postgres
```

Remove containers and the project network:

```bash
docker compose down
```

Remove orphaned containers:

```bash
docker compose down --remove-orphans
```

Remove local project images:

```bash
docker compose down --rmi local
```

Remove all project images:

```bash
docker compose down --rmi all
```

---

# 27. Remove PostgreSQL Data

Remove containers, networks, and named volumes:

```bash
docker compose down -v
```

This permanently deletes the local BuildWise PostgreSQL data.

Use this only when you intentionally want a clean database.

Recreate the environment afterward:

```bash
docker compose up -d --build
```

---

# 28. PostgreSQL Commands

Open a PostgreSQL shell:

```bash
docker compose exec postgres \
  psql -U buildwise -d buildwise
```

List databases:

```bash
docker compose exec postgres \
  psql -U buildwise -d buildwise -c "\l"
```

List schemas:

```bash
docker compose exec postgres \
  psql -U buildwise -d buildwise -c "\dn"
```

List tables:

```bash
docker compose exec postgres \
  psql -U buildwise -d buildwise -c "\dt"
```

Describe a table:

```bash
docker compose exec postgres \
  psql -U buildwise -d buildwise -c "\d table_name"
```

Check the current database user:

```bash
docker compose exec postgres \
  psql -U buildwise -d buildwise \
  -c "SELECT current_user;"
```

Check the PostgreSQL version:

```bash
docker compose exec postgres \
  psql -U buildwise -d buildwise \
  -c "SELECT version();"
```

Check database readiness:

```bash
docker compose exec postgres \
  pg_isready -U buildwise -d buildwise
```

---

# 29. Inspect Docker Environment Variables

View environment variables inside the API container:

```bash
docker compose exec api env
```

Filter only model-related variables:

```bash
docker compose exec api env | grep MODEL
```

Filter provider-related variables:

```bash
docker compose exec api env | grep -E "OPENAI|ANTHROPIC"
```

Do not copy or share output containing real API keys.

Check whether OpenAI is configured without printing the key:

```bash
docker compose exec api \
  python -c "
import os
print('OPENAI_API_KEY configured:', bool(os.getenv('OPENAI_API_KEY')))
"
```

Check whether Anthropic is configured without printing the key:

```bash
docker compose exec api \
  python -c "
import os
print('ANTHROPIC_API_KEY configured:', bool(os.getenv('ANTHROPIC_API_KEY')))
"
```

---

# 30. Dependency Maintenance Commands

Show the dependency tree:

```bash
uv tree
```

Show outdated packages:

```bash
uv tree --outdated
```

Recreate the lock file after changing `pyproject.toml`:

```bash
uv lock
```

Upgrade dependencies within the configured version constraints:

```bash
uv lock --upgrade
```

Synchronize the environment:

```bash
uv sync --all-groups
```

Synchronize strictly from the lock file:

```bash
uv sync --frozen --all-groups
```

Remove packages that are no longer declared:

```bash
uv sync --all-groups
```

---

# 31. Recommended Daily Development Workflow

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Start the application locally:

```bash
uv run uvicorn buildwise.main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000
```

Run the CrewAI smoke Flow when Flow-related code changes:

```bash
uv run python -m buildwise.flows.smoke
```

Before committing:

```bash
uv run ruff check src tests
```

```bash
uv run ruff format --check src tests
```

```bash
uv run mypy src
```

```bash
uv run pytest
```

```bash
uv run python -m buildwise.flows.smoke
```

Stop PostgreSQL when finished:

```bash
docker compose stop postgres
```

---

# 32. Recommended Full Local Verification

Run:

```bash
uv sync --frozen --all-groups
```

```bash
docker compose up -d postgres
```

```bash
uv run ruff check src tests
```

```bash
uv run ruff format --check src tests
```

```bash
uv run mypy src
```

```bash
uv run pytest
```

```bash
uv run python -c "from buildwise.main import app; print(app.title)"
```

```bash
uv run python -m buildwise.flows.smoke
```

Start the API:

```bash
uv run uvicorn buildwise.main:app \
  --host 0.0.0.0 \
  --port 8000
```

Then, from another terminal:

```bash
curl -s http://localhost:8000/health | python -m json.tool
```

```bash
curl -s http://localhost:8000/ready | python -m json.tool
```

---

# 33. Recommended Full Docker Verification

Validate Compose:

```bash
docker compose config --quiet
```

Build the stack:

```bash
docker compose build
```

Start all services:

```bash
docker compose up -d
```

Check status:

```bash
docker compose ps
```

Inspect API logs:

```bash
docker compose logs --tail=100 api
```

Inspect PostgreSQL logs:

```bash
docker compose logs --tail=100 postgres
```

Test the health endpoint:

```bash
curl -s http://localhost:8000/health | python -m json.tool
```

Test the readiness endpoint:

```bash
curl -s http://localhost:8000/ready | python -m json.tool
```

Run the CrewAI smoke Flow inside Docker:

```bash
docker compose exec api \
  python -m buildwise.flows.smoke
```

Verify the application import:

```bash
docker compose exec api \
  python -c "from buildwise.main import app; print(app.title)"
```

Verify provider SDKs:

```bash
docker compose exec api \
  python -c "import openai, anthropic; print('Provider SDKs installed')"
```

Stop the stack:

```bash
docker compose down
```

---

# 34. Fresh Installation Sequence

Use this sequence on a new development machine.

Install Python:

```bash
uv python install 3.12
```

Create the environment file:

```bash
cp .env.example .env
```

Add API keys to `.env`.

Create the lock file:

```bash
uv lock
```

Install dependencies:

```bash
uv sync --all-groups
```

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Run quality checks:

```bash
uv run ruff check src tests
```

```bash
uv run ruff format --check src tests
```

```bash
uv run mypy src
```

Run the CrewAI smoke Flow:

```bash
uv run python -m buildwise.flows.smoke
```

Start the application:

```bash
uv run uvicorn buildwise.main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000
```

Verify the application:

```bash
curl -s http://localhost:8000/health | python -m json.tool
```

```bash
curl -s http://localhost:8000/ready | python -m json.tool
```

---

# 35. Quick Command Reference

## Install

```bash
cp .env.example .env
uv lock
uv sync --all-groups
```

## Run locally

```bash
docker compose up -d postgres
```

```bash
uv run uvicorn buildwise.main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000
```

## Run smoke Flow

```bash
uv run python -m buildwise.flows.smoke
```

## Run checks

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
uv run pytest
```

## Run Docker

```bash
docker compose up -d --build
```

## Check Docker

```bash
docker compose ps
docker compose logs --tail=100 api
```

## Test API

```bash
curl -s http://localhost:8000/health | python -m json.tool
curl -s http://localhost:8000/ready | python -m json.tool
```

## Stop Docker

```bash
docker compose down
```

## Reset Docker and database

```bash
docker compose down -v
```

---

# 36. Important Operational Notes

## API Keys

Never commit the real `.env` file.

The repository should commit:

```text
.env.example
```

The repository should ignore:

```text
.env
.env.local
.env.*.local
```

## Claude Evaluation

Claude evaluation remains disabled during the first development phases:

```env
EVALUATION_ENABLED=false
CROSS_PROVIDER_EVALUATION_ENABLED=false
```

Enable evaluation only after the main OpenAI workflow is stable.

## Model Fallbacks

Fallback model environment variables do not implement fallback behavior by themselves.

Keep:

```env
MODEL_FALLBACK_ENABLED=false
```

until the application implements:

- failure classification
- eligible fallback conditions
- structured fallback logs
- usage accounting
- cost tracking
- validation after fallback
- maximum fallback attempts

## Docker Development Dependencies

The production Docker image may not contain Ruff, mypy, or pytest.

Run those locally or in CI unless a dedicated development Docker stage is added.

## Database Reset

This command deletes local PostgreSQL data:

```bash
docker compose down -v
```

Do not run it when you need to preserve existing consultations, artifacts, usage records, or evaluation results.