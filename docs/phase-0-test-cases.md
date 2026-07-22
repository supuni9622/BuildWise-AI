# Phase 0 Test Cases

Generate these tests with Claude Code.

## Settings

1. Defaults load with no `.env`.
2. Invalid log level fails validation.
3. API prefix without a leading slash fails validation.
4. OpenAI-backed model configuration is not ready without an API key.
5. Non-OpenAI model configuration can be ready without an OpenAI key.
6. Secret values are represented as `SecretStr` and never serialized into logs.

## API and middleware

1. `GET /health` returns HTTP 200 and `status=ok`.
2. `GET /ready` returns `ready` when database and provider configuration are valid.
3. `GET /ready` returns `not_ready` when a required provider key is absent.
4. `GET /api/v1` returns application and API version metadata.
5. A request without `X-Request-ID` receives a generated response header.
6. A supplied `X-Request-ID` is preserved.
7. Request logs contain request ID, stage, status, and duration.
8. Unknown routes return the canonical error shape.
9. Invalid request payloads return the canonical validation error shape.
10. Unhandled exceptions return a sanitized canonical internal error.

## Database

1. SQLite engine is created with `check_same_thread=False`.
2. PostgreSQL-compatible URL creates an engine without SQLite-only arguments.
3. Database readiness returns true on `SELECT 1`.
4. Database readiness returns false on connection failure.

## Usage models

1. Default counters are zero.
2. Negative token, cost, retry, or duration values fail validation.
3. Usage records serialize to JSON.
4. Usage summaries accept multiple records.

## CrewAI smoke Flow

1. Flow state starts with `completed=false`.
2. Start method sets the expected message.
3. Listener marks the Flow complete.
4. `kickoff()` returns the expected final string.
5. Smoke Flow executes without an LLM API key.

## Docker and CI

1. Image builds successfully.
2. Container runs as a non-root user.
3. `/health` passes the Docker health check.
4. API starts with SQLite.
5. Docker Compose starts API and PostgreSQL.
6. `/ready` detects PostgreSQL connectivity.
7. Ruff lint passes.
8. Ruff formatting check passes.
9. Mypy strict mode passes.
10. Pytest passes.
11. Application import smoke test passes.
