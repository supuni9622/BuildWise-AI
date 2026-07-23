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

Phase 1 common-model test cases

Record these for the later Phase 1 test suite:

BuildWiseModel rejects unknown fields.
String fields trim surrounding whitespace.
CurrencyCode converts lowercase currency codes to uppercase.
Invalid currency codes are rejected.
Negative monetary values are rejected.
CostRange requires a shared currency.
Minimum cost cannot exceed expected cost.
Expected cost cannot exceed maximum cost.
TokenCounts calculates total_tokens when it is zero.
Provider-reported totals cannot be lower than input plus output tokens.
Naive timestamps are rejected.
Timezone-aware timestamps are normalized to UTC.
Completion timestamps cannot precede start timestamps.
UUID identifiers are generated when omitted.
Source metadata serializes URLs, enums, UUIDs, and timestamps to JSON.
Cost estimates preserve category ownership.
Mutable list and dictionary defaults are not shared between instances.
Validation issues and warnings reject empty messages.
Normalized scores reject values outside 0.0–1.0.
Percentages reject values outside 0–100.

Phase 1 session-model test cases

Record these scenarios for the later test implementation:

A new session defaults to CREATED and INTAKE.
Session and request UUIDs are generated automatically.
Metadata rejects duplicate tags.
Metadata trims optional identifier fields.
Session errors reject naive timestamps.
Resolved errors require both resolved_at and resolution.
Retry counts are rejected when retryable is false.
Completed sessions require the completed stage.
Completed sessions require completed_at.
Failed sessions require the failed stage.
Failed sessions require failed_at.
Non-terminal sessions reject terminal timestamps.
Awaiting-user-input sessions require the clarification stage.
Resuming sessions require the clarification stage.
Reviewing sessions require the lead-review stage.
Completed-with-limitations sessions require at least one warning.
record_activity() increments state_revision.
record_activity() updates updated_at.
add_error() stores an error and updates activity.
mark_completed() creates a valid terminal session.
mark_failed() creates a valid failed session.
All session models serialize to JSON.
Mutable metadata, error, warning, tag, and attribute defaults are isolated.
Unknown fields are rejected.
The session model contains no specialist artifacts or agent behavior.

Phase 1 intake-model test cases

Record these scenarios for later test implementation:

ProductIdeaRequest requires at least 20 characters for the original idea.
A title is optional at raw intake.
Raw intake accepts unresolved AI, security, and regulatory flags.
Duplicate target users are rejected.
Duplicate target platforms are rejected.
Existing products require an existing-product description.
New products reject an existing-product description.
Intake timestamps must be timezone-aware.
ValidatedProductIdea requires a title.
ValidatedProductIdea requires at least one target user.
ValidatedProductIdea requires at least one desired outcome.
Validated idea fields serialize into JSON.
Validated idea session IDs serialize correctly.
Clarification answers trim textual values.
Empty textual clarification answers are rejected.
Clarification list answers reject empty values.
Clarification list answers reject duplicates.
A skipped answer rejects a non-null answer.
A skipped answer requires a skip reason.
A non-skipped answer rejects a skip reason.
A non-skipped answer requires a meaningful value.
Clarification requests require at least one answer.
Clarification requests require a round greater than zero.
Clarification requests reject duplicate question IDs.
Product context requires matching session IDs.
Product context rejects duplicate clarification answers.
Product context rejects keys that are both resolved and unresolved.
Clarification answers require a positive clarification round.
A positive clarification round requires collected answers.
All intake models reject unknown fields.
Mutable list and dictionary defaults are isolated between instances.
Intake models do not contain Discovery results or specialist outputs.

# Phase 1 Discovery test cases

Record these for the later test implementation:

A user-provided fact requires a source reference.
A clarification fact requires a source reference.
A derived fact cannot be marked as user-confirmed.
Known-fact source references must be unique.
Assumptions requiring validation require a validation question.
Assumptions not requiring validation reject a validation question.
Assumption impact areas must be unique.
Unknowns require at least one impact area.
Blocking unknowns must require clarification.
Unknowns that permit assumptions require a recommended assumption.
Unknowns that prohibit assumptions reject recommended assumptions.
Discovery-risk capability references must be unique.
Completeness scores must be between zero and one.
Completeness percentages must be between zero and one hundred.
Completeness percentage must match the normalized score.
Complete results must meet the configured threshold.
Incomplete results cannot meet or exceed the threshold.
Blocking and non-blocking unknown keys cannot overlap.
Missing and satisfied completeness categories cannot overlap.
Blocking unknowns prevent continuation.
Blocking unknowns require clarification.
Complete results cannot require clarification.
Choice questions require at least two options.
Non-choice questions reject options.
allow_other is valid only for choice questions.
Clarification question unknown references must be unique.
Clarification sets require at least one question.
Clarification sets allow no more than ten questions.
Clarification question IDs must be unique.
Clarification question keys must be unique.
A blocking question set requires a required question.
Clarification expiry must be later than generation time.
Capability lists must be unique.
Primary capability must appear in the capability list.
AI capability classifications require ai_required=true.
RAG flags require the RAG capability.
Agent flags require the agentic-workflow capability.
Sensitive-data flags require the sensitive-data capability.
Regulated-domain flags require the regulated capability.
Real-time flags require the real-time capability.
Integration flags require the integration-heavy capability.
Discovery and idea-context session IDs must match.
Discovery and clarification-set session IDs must match.
Questions cannot reference unknowns absent from the Discovery result.
Clarification-required results require a question set.
Clarification-required results must route to clarification.
Product-definition routing requires can_continue=true.
Continuation with limitations requires at least one limitation.
Known-fact and assumption keys cannot overlap.
All Discovery models serialize successfully.
All Discovery models reject unknown fields.
Mutable collection defaults are isolated between instances.

# Phase 1 requirements-model test cases

Record these for later implementation:

Behavioral acceptance criteria must provide given, when, and then together.
Performance criteria require a measurable target.
Accessibility criteria require a measurable target.
Automated criteria must use automated testing or monitoring.
Non-automated criteria cannot use automated-test verification.
Business rules cannot depend on themselves.
Non-deterministic rules cannot be enforced only in the client.
Non-deterministic rules cannot be enforced only in the database.
Data requirements need at least one operation.
Required and optional data fields cannot overlap.
Fixed-period retention requires a retention period.
Legal retention requires a retention period.
Other retention types reject a retention period.
Personal data cannot be classified as public.
Sensitive data requires a protected classification.
Sensitive data requires encryption at rest.
Sensitive data requires encryption in transit.
Regulated data requires regulation names.
Non-regulated data rejects regulation names.
Delete operations require deletion behavior.
Edge cases requesting user action require a user message.
Retry behavior requires a recovery action.
Fallback behavior requires a recovery action.
Rollback behavior requires a recovery action.
Blocking edge cases cannot be ignored.
Functional requirements require a main flow.
Functional requirements require postconditions.
Functional requirements require acceptance criteria.
Functional requirements require feature references.
Functional requirements require persona references.
Functional requirements cannot depend on themselves.
Functional dependencies require a dependency type.
Dependency types cannot exist without dependencies.
Must-have functional requirements require blocking criteria.
Synchronous integrations require a timeout.
Asynchronous integrations reject synchronous timeouts.
Retry-enabled integrations require a retry count.
Retry-disabled integrations reject a retry count.
Rate-limited integrations require a rate-limit description.
Must-have integrations require fallback behavior.
Integration dependencies cannot reference themselves.
Non-functional requirements require metrics and targets.
Non-functional requirements require measurable acceptance criteria.
Must-have non-functional requirements require blocking criteria.
User journey step IDs must be unique.
User journey sequence numbers must be unique.
User journey sequences must start at one.
User journey sequences must be contiguous.
User story narratives must contain the actor.
User story narratives must contain the capability.
User story narratives must contain the benefit.
User stories cannot depend on themselves.
Must-have user stories require blocking criteria.
Specification timestamps must be timezone-aware.
Specification update time cannot precede generation time.
Requirement keys must be globally unique.
Functional business-rule references must exist.
Functional data-requirement references must exist.
Functional integration references must exist.
Functional non-functional references must exist.
Functional edge-case references must exist.
Functional dependencies must exist.
Non-functional functional-requirement references must exist.
Integration data-requirement references must exist.
Integration dependencies must exist.
Business-rule dependencies must exist.
Edge-case requirement references must exist.
Journey requirement references must exist.
Journey-step requirement references must exist.
User-story functional references must exist.
User-story non-functional references must exist.
User-story edge-case references must exist.
User-story dependencies must exist.
Every must-have functional requirement requires user-story coverage.
At least one must-have requirement requires journey coverage.
Approved specifications cannot contain open questions.
Approved-with-assumptions specifications require assumptions.
Clarification decisions require open questions.
Cannot-proceed decisions require limitations.
Specification and ProductDefinition session IDs must match.
Specification must reference the correct ProductDefinition.
Referenced feature IDs must exist in ProductDefinition.
Referenced persona IDs must exist in ProductDefinition.
Referenced goal IDs must exist in ProductDefinition.
All requirement models reject unknown fields.
All requirement models serialize to JSON.
Mutable list defaults are isolated across instances.

# Phase 1 architecture-model test cases

Record these for later test implementation:

Components require at least one responsibility.
Components require responsibility details.
Component responsibilities must be unique.
Components cannot depend on themselves.
Data-owning components require owned entities.
Non-data-owning components reject owned entities.
Internet-facing components must be externally accessible.
Single points of failure must be marked critical.
Connections cannot connect a component to itself.
Synchronous connections require timeouts.
Streaming connections require timeouts.
Asynchronous connections reject synchronous timeouts.
Batch connections reject synchronous timeouts.
Retry-enabled connections require maximum attempts.
Retry-disabled connections reject maximum attempts.
Public-network connections require authentication.
Public-network connections require encryption.
Third-party connections require authentication.
Third-party connections require encryption.
Asynchronous connections require a compatible mechanism.
Technology alternatives must be unique.
A selected technology cannot also appear as an alternative.
Rejected technologies cannot be assigned to components.
Deployment environments must be unique.
Deployment units require at least one component.
Deployment units cannot depend on themselves.
Containerized units require an image name.
Non-containerized units reject an image name.
Horizontally scaled units require minimum instances.
Horizontally scaled units require maximum instances.
Maximum instances cannot be lower than minimum instances.
Custom availability targets require a custom value.
Standard availability targets reject custom values.
Runtime units requiring health checks require a path.
Disabled health checks reject a health-check path.
Persistent storage requires a storage description.
Stateless units reject a storage description.
Environment variables and secret names cannot overlap.
Architecture decisions cannot supersede themselves.
Accepted decisions require positive consequences.
Rejected decisions cannot supersede decisions.
Superseded decisions require a decision-chain reference.
Accepted risks require acceptance rationale.
Non-accepted risks reject acceptance rationale.
Likely critical risks cannot be accepted.
High architecture risks require monitoring indicators.
Critical architecture risks require monitoring indicators.
Scalability plans cannot use the none strategy.
Scalability plans require at least one component.
Alerting requirements require alert conditions.
Non-alerting requirements reject alert conditions.
Dashboard requirements require dashboard descriptions.
Non-dashboard requirements reject dashboard descriptions.
Sensitive telemetry requires redaction.
Must-have observability requirements require thresholds.
Architecture timestamps must be timezone-aware.
Update timestamps cannot precede generation timestamps.
Artifact IDs must be unique within architecture collections.
Architecture keys must be globally unique.
Component dependencies must exist.
Connection source components must exist.
Connection target components must exist.
Duplicate connections must be rejected.
Deployment component references must exist.
Deployment-unit dependencies must exist.
Components cannot be assigned to multiple deployment units.
Every component must be assigned to a deployment unit.
Technology component references must exist.
Technology decision references must exist.
Decision component references must exist.
Superseded-decision references must exist.
Risk component references must exist.
Risk deployment-unit references must exist.
Risk decision references must exist.
Scalability component references must exist.
Scalability deployment-unit references must exist.
Observability component references must exist.
Observability deployment-unit references must exist.
Every critical component requires observability coverage.
At least one production deployment unit is required.
At least one accepted architecture decision is required.
At least one selected or approved technology is required.
Approved architectures cannot contain open questions.
Approved-with-assumptions architectures require assumptions.
Clarification decisions require open questions.
Cannot-proceed decisions require limitations.
Architecture and requirements session IDs must match.
Architecture must reference the correct requirements specification.
Architecture requirement references must exist.
Must-have functional requirements require component mappings.
Architecture models reject unknown fields.
Architecture models serialize to JSON.
Mutable collection defaults are isolated.
