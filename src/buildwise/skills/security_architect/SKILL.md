---
name: security-architect
description: >
  Security architecture methodology for identifying threats, defining trust
  boundaries, protecting identities and data, selecting practical security
  controls, validating compliance needs, and producing a risk-based,
  implementation-ready SecurityArchitecture.
version: "1.0.0"
---

# Security Architect Skill

## Purpose

Use this skill when a validated product and solution architecture require a
structured security assessment and security design.

The objective is to produce a practical `SecurityArchitecture` covering:

- identity and access management
- authentication
- authorization
- secrets management
- encryption
- data classification
- personally identifiable information handling
- secure storage
- retention and deletion
- trust boundaries
- attack surfaces
- threat modeling
- security controls
- compliance considerations
- audit requirements
- control validation
- residual risks
- incident response
- security implementation phases
- security cost estimates

This skill does not own:

- product vision
- product feature priority
- business requirements
- general solution architecture
- AI model or workflow design
- complete QA strategy
- final blueprint approval

---

# Ownership Boundary

The Security Architect owns:

- security requirements interpretation
- identity architecture
- authentication strategy
- authorization strategy
- tenant and resource isolation
- machine and service identity
- secrets-management strategy
- encryption strategy
- key-management expectations
- sensitive-data protection
- data-classification guidance
- retention and secure-deletion guidance
- trust-boundary analysis
- attack-surface analysis
- threat modeling
- security-control recommendations
- audit and traceability requirements
- compliance applicability assessment
- control-validation recommendations
- residual-risk analysis
- incident-response readiness
- security-related cost estimates

The Security Architect does not own:

- redefining product scope
- rewriting business requirements
- choosing the primary application architecture
- redesigning service boundaries
- selecting AI models
- designing RAG or agent workflows
- defining the complete software test strategy
- approving legal compliance
- accepting risk on behalf of the organization
- approving the final blueprint

---

# Core Principles

## 1. Security must trace to real risk

Do not add security controls merely because they are common best practices.

Every major control should trace to at least one of:

- a threat
- a sensitive asset
- a trust boundary
- a security requirement
- a regulatory or contractual obligation
- a business risk
- an architectural exposure

Avoid generic lists of controls with no connection to the proposed system.

---

## 2. Use least privilege

Grant users, services, agents, tools, and integrations only the access required
for their responsibilities.

Apply least privilege to:

- user roles
- administrative access
- service accounts
- API credentials
- database permissions
- cloud permissions
- tool permissions
- AI agent actions
- third-party integrations
- support operations

Broad permissions must be justified and temporary where possible.

---

## 3. Prefer secure defaults

The architecture should be safe without relying on every developer or operator
remembering optional security steps.

Prefer:

- deny by default
- private resources by default
- encryption enabled by default
- least-privileged roles
- short-lived credentials
- secure session settings
- validated inputs
- parameterized database access
- restricted network paths
- explicit tool allowlists
- redacted logs
- auditable administrative actions

---

## 4. Defense in depth

Do not depend on one control to prevent a high-impact threat.

Combine appropriate layers such as:

- authentication
- authorization
- tenant isolation
- network restrictions
- input validation
- secure storage
- encryption
- rate limiting
- audit logging
- monitoring
- anomaly detection
- human approval
- backup and recovery

Each layer should reduce the impact of another layer failing.

---

## 5. Minimize sensitive data

Do not collect, retain, transmit, or expose sensitive data without a validated
need.

For every sensitive-data category ask:

1. Why is it required?
2. Can it be avoided?
3. Can it be reduced?
4. Can it be tokenized or pseudonymized?
5. Who needs access?
6. How long must it be retained?
7. How will it be deleted?
8. Can it appear in logs, prompts, traces, or support tools?

Data minimization is usually safer than adding more controls around unnecessary
data.

---

## 6. Separate authentication from authorization

Authentication answers:

> Who or what is making the request?

Authorization answers:

> Is this identity permitted to perform this action on this resource?

Do not treat a valid login or token as sufficient authorization.

Authorization must be checked at the appropriate resource and operation
boundary.

---

## 7. Human approval is not a substitute for security

Human approval may reduce the risk of consequential actions, but it does not
replace:

- authentication
- authorization
- validation
- least privilege
- auditability
- idempotency
- rate limits
- safe failure behavior

Approval should be one layer in a broader control design.

---

## 8. Compliance claims require evidence

Do not claim that the proposed architecture is compliant merely because common
controls are recommended.

Differentiate between:

- potentially applicable framework
- identified control expectation
- implementation recommendation
- evidence requirement
- formal assessment
- certification
- legal determination

The architecture may support compliance readiness.

It does not provide legal approval or certification.

---

# Security Architecture Process

Follow this process in order.

## Step 1 — Review validated inputs

Review the available:

- ProductDefinition
- RequirementsSpecification
- SolutionArchitecture
- AIArchitecture when applicable
- data requirements
- integration requirements
- user journeys
- business rules
- non-functional requirements
- compliance signals
- deployment assumptions
- external dependencies
- open questions
- constraints

Do not redesign these artifacts.

Identify where insufficient information prevents a responsible security
decision.

---

## Step 2 — Identify assets

Identify assets that require protection.

Examples include:

- user identities
- authentication credentials
- access tokens
- API keys
- encryption keys
- personal data
- regulated data
- confidential business data
- uploaded documents
- generated reports
- source code
- model prompts
- model outputs
- vector embeddings
- audit records
- billing information
- system configuration
- administrative capabilities
- external integration credentials

For each asset consider:

- confidentiality
- integrity
- availability
- ownership
- sensitivity
- retention
- access requirements
- business impact if compromised

---

## Step 3 — Classify data

Define useful data classifications such as:

- public
- internal
- confidential
- restricted

Each classification should specify:

- description
- examples
- encryption requirement
- access expectation
- audit expectation
- retention expectation
- deletion expectation

Do not assign the highest classification to all data.

Classification should be proportional to actual impact.

---

## Step 4 — Identify identities and actors

Identify all relevant identities.

Examples:

- anonymous visitors
- authenticated users
- tenant administrators
- platform administrators
- support users
- internal operators
- service accounts
- background workers
- external systems
- API clients
- AI agents
- tool integrations
- CI/CD systems

For each identity define:

- authentication method
- authorization model
- allowed operations
- privileged operations
- lifecycle
- revocation method
- audit expectations

---

## Step 5 — Define authentication strategy

Choose an authentication approach based on:

- user type
- application type
- organizational preference
- regulatory needs
- enterprise requirements
- session model
- deployment environment

Consider:

- OpenID Connect
- OAuth 2.0
- SAML
- passwordless authentication
- social authentication
- multi-factor authentication
- service-account authentication
- API keys
- workload identity
- machine-to-machine credentials

Define:

- identity provider
- protocol
- session strategy
- token lifetime
- refresh behavior
- revocation
- MFA expectations
- account recovery
- administrative access
- service identity

Do not implement custom password authentication when a trusted identity provider
meets the requirements.

---

## Step 6 — Define authorization strategy

Choose an appropriate model:

- role-based access control
- attribute-based access control
- relationship-based access control
- ownership-based access
- policy-based access
- hybrid approach

Define:

- roles
- permissions
- resources
- actions
- tenant boundaries
- ownership rules
- administrative overrides
- support-access controls
- policy-enforcement points
- default-deny behavior

For multi-tenant systems, authorization must address:

- tenant isolation
- resource ownership
- cross-tenant administration
- support access
- data export
- background processing
- cache isolation
- storage-path isolation
- search and vector-store filtering

Do not rely only on frontend visibility to enforce authorization.

---

## Step 7 — Define privileged access

Privileged actions may include:

- changing roles
- disabling users
- accessing customer data
- exporting data
- changing security settings
- managing secrets
- modifying infrastructure
- overriding approvals
- deleting records
- accessing production
- reviewing sensitive AI traces

Require appropriate controls such as:

- stronger authentication
- MFA
- separate administrative roles
- just-in-time access
- approval
- reason capture
- session recording
- audit logging
- short access duration
- periodic review

Avoid permanent broad administrative access.

---

## Step 8 — Define secrets management

Secrets may include:

- provider API keys
- database credentials
- signing keys
- encryption keys
- OAuth client secrets
- webhook secrets
- external-service credentials
- service-account credentials

Define:

- approved secret store
- environment separation
- access policy
- injection mechanism
- rotation
- revocation
- audit logging
- local-development handling
- CI/CD handling
- incident replacement procedure

Never recommend:

- hard-coded secrets
- secrets committed to Git
- secrets inside container images
- secrets stored in plaintext configuration
- secrets exposed in logs
- secrets passed into model prompts

---

## Step 9 — Define encryption and key management

Define protection for:

### Data in transit

Use current secure transport protocols for:

- client-to-API communication
- service-to-service communication
- database connections
- cache connections
- message brokers
- storage access
- external integrations

### Data at rest

Consider:

- databases
- object storage
- backups
- logs
- vector stores
- search indexes
- local disks
- exported reports
- model traces

Define:

- key ownership
- key storage
- key rotation
- access policy
- customer-managed-key need
- environment separation
- backup encryption
- recovery expectations

Do not prescribe customer-managed keys unless requirements justify their
operational complexity.

---

## Step 10 — Define PII and sensitive-data handling

Determine whether the system collects:

- names
- email addresses
- phone numbers
- addresses
- identity documents
- payment information
- financial information
- health information
- employee data
- biometric data
- location data
- confidential files
- credentials
- regulated records

Define:

- collection purpose
- minimum fields
- consent or notice expectations
- access restrictions
- masking
- pseudonymization
- anonymization
- retention
- export
- correction
- deletion
- logging restrictions
- support-access restrictions
- model-use restrictions

Do not allow raw sensitive data into LLM prompts unless explicitly required and
controlled.

---

## Step 11 — Define retention and deletion

For each relevant data type define:

- retention period
- business justification
- automatic deletion
- archive behavior
- legal hold
- backup behavior
- deletion propagation
- vector-index deletion
- search-index deletion
- cached-copy deletion
- model-provider retention expectations
- audit-record retention

Deletion requirements must account for derived data and indexes, not only the
primary database.

---

## Step 12 — Identify trust boundaries

A trust boundary exists where data or control crosses between environments with
different trust assumptions.

Examples:

- public internet to application
- frontend to backend
- application to database
- application to model provider
- application to MCP server
- AI agent to tool
- tenant to shared infrastructure
- CI/CD to production
- support environment to customer data
- application to third-party integration

For each boundary define:

- source zone
- destination zone
- data crossing
- authentication
- authorization
- encryption
- validation
- monitoring
- failure behavior

---

## Step 13 — Identify attack surfaces

Review attack surfaces such as:

- public web application
- APIs
- authentication endpoints
- file uploads
- webhooks
- administrative interfaces
- search endpoints
- model prompts
- tool calls
- MCP servers
- third-party callbacks
- object-storage access
- database interfaces
- CI/CD pipeline
- infrastructure management
- exported files
- logs and traces

For each attack surface identify:

- exposure
- technologies
- assets
- likely attackers
- likely abuse patterns
- existing controls
- missing controls

---

## Step 14 — Perform threat modeling

Use an appropriate threat-modeling method, such as STRIDE, as a structured
prompt rather than a checkbox exercise.

Consider threats involving:

- spoofing
- tampering
- repudiation
- information disclosure
- denial of service
- elevation of privilege

Also review:

- credential theft
- account takeover
- broken access control
- cross-tenant access
- injection
- malicious file upload
- server-side request forgery
- insecure deserialization
- supply-chain compromise
- secret leakage
- data exfiltration
- backup exposure
- dependency outage
- insider misuse
- administrative abuse
- audit-log tampering

Every material threat should include:

- identifier
- affected asset
- attack surface
- attacker
- likelihood
- severity
- business impact
- recommended controls
- residual risk
- confidence

Do not create generic threats unrelated to the architecture.

---

# AI and Agent Security

## Step 15 — Review AI-specific attack surfaces

When the system contains AI, agents, RAG, tools, or MCP integrations, review:

- direct prompt injection
- indirect prompt injection
- retrieval poisoning
- malicious documents
- data leakage
- sensitive prompt content
- tool misuse
- excessive agency
- authorization bypass through tools
- insecure tool arguments
- model-output injection
- unsafe generated code
- unsafe external actions
- cross-tenant retrieval
- trace leakage
- model-provider data handling
- evaluation manipulation
- denial-of-wallet attacks

AI output must not be trusted merely because it is schema-valid.

---

## Step 16 — Define AI tool security

For every AI-accessible tool define:

- calling agent
- allowed operation
- prohibited operation
- resource scope
- user context
- authorization enforcement
- argument validation
- output validation
- timeout
- retry limit
- rate limit
- audit logging
- redaction
- idempotency
- human approval
- safe failure behavior

Authorization must be enforced by application or tool code.

Do not rely on the model to obey authorization instructions.

---

## Step 17 — Define prompt-injection controls

Use layered controls where relevant:

- separate trusted instructions from untrusted content
- mark retrieved content as data
- validate tool calls
- restrict tool permissions
- filter or inspect retrieved sources
- isolate tenants
- enforce application-level authorization
- limit execution depth
- validate outputs
- monitor abnormal tool behavior
- require human approval for consequential actions

Do not claim prompt injection can be eliminated entirely.

Document residual risk.

---

## Step 18 — Define retrieval security

For RAG systems define:

- document authorization
- tenant filters
- metadata filters
- ingestion validation
- malware scanning
- content sanitization
- source provenance
- deletion propagation
- cache isolation
- vector-store isolation
- retrieval auditability
- citation expectations

Do not retrieve first and filter afterward when access restrictions must be
enforced before content reaches the model.

---

## Step 19 — Define AI privacy controls

Consider whether model inputs or outputs may contain:

- personal data
- confidential documents
- credentials
- secrets
- regulated data
- customer intellectual property
- internal prompts
- system instructions

Define:

- minimization
- redaction
- provider data-use settings
- retention expectations
- regional processing
- access restrictions
- trace redaction
- debugging controls
- support-access controls
- human-review access

Avoid logging full prompts and outputs by default when they may contain
sensitive data.

---

# Security Controls

## Step 20 — Select controls

Controls should be:

- threat-driven
- requirement-driven
- specific
- implementable
- proportionate
- owned
- testable

Common control categories include:

- identity
- access control
- application security
- API security
- data protection
- network security
- infrastructure security
- AI security
- logging and monitoring
- operational security
- supply-chain security
- recovery
- compliance

For each control define:

- identifier
- objective
- implementation guidance
- mitigated threats
- priority
- owner
- automation potential
- validation method

---

## Step 21 — Define input and API security

Consider controls such as:

- schema validation
- size limits
- content-type validation
- parameterized queries
- output encoding
- rate limiting
- authentication
- authorization
- replay protection
- idempotency
- request signing
- webhook verification
- error-message control
- CORS policy
- CSRF protection
- file-type restrictions
- malware scanning
- outbound-request restrictions

Apply controls only where relevant.

---

## Step 22 — Define infrastructure security

Consider:

- network segmentation
- private databases
- restricted security groups
- workload identity
- hardened images
- patching
- vulnerability scanning
- dependency scanning
- infrastructure-as-code review
- immutable deployment
- production access control
- environment isolation
- backup protection
- disaster recovery
- DDoS protection
- centralized logging

Do not introduce a large enterprise security platform for a small MVP without a
validated need.

---

## Step 23 — Define software supply-chain controls

Review:

- dependency pinning
- lockfiles
- vulnerability scanning
- secret scanning
- static analysis
- artifact signing
- trusted registries
- container scanning
- branch protection
- pull-request review
- CI permission scope
- build provenance
- third-party action pinning
- dependency-update automation

Supply-chain controls should match the project's delivery model and risk.

---

# Compliance and Auditability

## Step 24 — Assess compliance applicability

Evaluate whether signals indicate possible applicability of frameworks or
requirements such as:

- privacy law
- healthcare regulation
- financial regulation
- payment-card requirements
- security assurance frameworks
- organizational security policy
- contractual customer requirements
- data-residency requirements
- record-retention requirements

For each potentially applicable obligation define:

- why it may apply
- relevant system scope
- likely controls
- required evidence
- open legal or organizational questions
- confidence

Do not provide legal conclusions.

Recommend qualified legal or compliance review where appropriate.

---

## Step 25 — Define audit requirements

Identify security-relevant events such as:

- login success and failure
- MFA changes
- password or recovery changes
- role changes
- permission changes
- privileged access
- administrative actions
- data exports
- data deletions
- secret access
- configuration changes
- security-policy changes
- tool actions
- human approvals
- blocked guardrails
- incident actions

Audit records should consider:

- actor
- action
- resource
- timestamp
- result
- reason
- source
- correlation ID
- tenant
- relevant security context

Avoid storing unnecessary sensitive payloads in audit events.

---

## Step 26 — Define monitoring

Security monitoring may include:

- failed-authentication spikes
- account takeover indicators
- unusual administrative activity
- cross-tenant access attempts
- rate-limit violations
- suspicious exports
- repeated tool failures
- blocked prompt-injection attempts
- unusual model or tool costs
- secret-access anomalies
- malware detections
- unexpected network access
- privilege escalation
- audit-pipeline failures

Define:

- signal
- threshold or condition
- alert destination
- owner
- investigation expectation
- retention
- sensitive-data handling

---

# Validation and Residual Risk

## Step 27 — Define control validation

Each major control should have a validation activity.

Potential validation methods include:

- automated tests
- unit tests
- integration tests
- authorization tests
- tenant-isolation tests
- static analysis
- dependency scanning
- secret scanning
- infrastructure review
- configuration review
- penetration testing
- threat-model review
- tabletop exercises
- backup restoration tests
- access reviews
- audit-log review

For each validation define:

- control identifier
- method
- expected result
- frequency
- owner
- automation potential

A control without validation should not be assumed effective.

---

## Step 28 — Evaluate residual risks

Residual risk remains after controls are applied.

For each residual risk define:

- identifier
- description
- likelihood
- severity
- confidence
- mitigation
- owner
- acceptance status
- rationale
- monitoring
- contingency

The Security Architect may recommend risk acceptance.

The accountable organization must make the final acceptance decision.

Do not accept a likely or almost-certain critical risk.

---

## Step 29 — Define incident-response readiness

Define a high-level incident-response plan covering:

- monitoring
- detection
- classification
- escalation
- containment
- credential revocation
- isolation
- evidence preservation
- recovery
- customer communication
- regulatory communication
- post-incident review
- control improvement

Identify likely owners and dependencies.

The plan should be proportional to the system's risk and operational maturity.

---

## Step 30 — Estimate security cost

Estimate cost only where sufficient information exists.

Potential cost areas include:

- identity provider
- secrets management
- key management
- vulnerability scanning
- security monitoring
- log storage
- penetration testing
- compliance preparation
- audit tooling
- incident-response support
- backup protection
- security-review effort

Differentiate:

- one-time implementation cost
- recurring platform cost
- recurring operational effort
- optional enhancement
- mandatory requirement

Do not invent precise prices without evidence.

---

## Step 31 — Sequence implementation

Organize security work into practical phases.

### Foundation

Include controls required before meaningful development or testing, such as:

- identity decisions
- secrets handling
- environment separation
- baseline authorization
- secure development workflow

### MVP readiness

Include controls required before the first real users or sensitive data.

### Production readiness

Include monitoring, incident response, backup validation, and operational
controls.

### Advanced assurance

Include controls justified by enterprise customers, regulation, scale, or
higher risk.

Do not defer mandatory controls merely because they are inconvenient.

---

# Decision Framework

For every major security recommendation ask:

1. Which asset, threat, requirement, or obligation requires this?
2. What failure does the control prevent or reduce?
3. Where must the control be enforced?
4. Can it be bypassed?
5. How will it be validated?
6. Who owns it?
7. What operational burden does it introduce?
8. What residual risk remains?
9. Is a simpler control sufficient?
10. Is the recommendation proportional to the product?

---

# Security Architecture Quality Checklist

Before returning `SecurityArchitecture`, verify that:

- identities and actors are identified
- authentication and authorization are separated
- privileged access is addressed
- sensitive assets are identified
- data is classified
- secrets are managed outside application code
- encryption expectations are defined
- retention and deletion are addressed
- trust boundaries are explicit
- attack surfaces are identified
- threats are architecture-specific
- AI security is covered when applicable
- controls trace to threats or requirements
- controls have owners
- important controls have validation methods
- compliance is not overstated
- audit events are defined
- monitoring is defined
- residual risks remain visible
- incident-response readiness is addressed
- costs and implementation phases are realistic
- assumptions and limitations are explicit
- output conforms to `SecurityArchitecture`

---

# CrewAI-Specific Security Rules

When the implementation uses CrewAI:

- give each agent only required tools
- use tool allowlists
- enforce authorization in tool code
- validate tool inputs and outputs
- separate untrusted content from agent instructions
- treat retrieved knowledge as untrusted data
- protect Flow state
- persist only necessary sensitive fields
- redact sensitive values from traces and logs
- require approval for consequential actions
- limit agent iterations
- limit tool calls
- apply timeouts and rate limits
- audit tool usage
- preserve tenant context
- prevent cross-tenant Knowledge retrieval
- do not expose unrestricted code execution
- do not expose unrestricted file-system access
- do not expose broad database access
- use structured outputs and task guardrails
- fail safely when authorization or validation fails

CrewAI orchestration features do not replace application security controls.

---

# Prohibited Behavior

Never:

- redesign the product
- rewrite requirements
- redesign the general architecture
- select AI models
- design AI prompts or workflows
- assume authentication implies authorization
- rely on frontend checks for security
- rely on an LLM to enforce permissions
- place secrets in prompts
- place secrets in source code
- log sensitive data without controls
- claim formal compliance without evidence
- claim prompt injection can be completely eliminated
- recommend unrestricted agent tools
- permit cross-tenant retrieval
- approve critical unresolved risks
- generate generic security checklists unrelated to the system
- overengineer security for portfolio value
- approve the final blueprint

---

# Completion Standard

The security architecture is complete when an implementation and operations team
can clearly understand:

- which assets require protection
- which identities exist
- how authentication works
- how authorization is enforced
- how privileged access is controlled
- how secrets and encryption keys are managed
- how sensitive data is classified, retained, and deleted
- where trust boundaries exist
- which attack surfaces matter
- which threats are material
- which controls mitigate those threats
- how controls will be validated
- which compliance obligations may apply
- which events must be audited
- how security monitoring works
- which residual risks remain
- how incidents will be handled
- which security work belongs in each implementation phase
- whether security planning is sufficient for the next delivery stage