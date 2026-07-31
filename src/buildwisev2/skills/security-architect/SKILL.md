---
name: security-architect
description: Methodology for threat modeling and designing security controls proportional to a system's actual risk.
---

# Security Architecture Methodology

## Step 1 — Map trust boundaries before threats

Identify where trust actually changes: client to API, service to
third-party integration, tenant to tenant. Threats without a clear trust
boundary are usually too vague to act on.

## Step 2 — Threat model with paired controls

Every threat you write must reference at least one control id that
mitigates it, and every control must be traceable to at least one threat
it addresses. A threat list with no controls is not a threat model — it's
a list of worries.

## Step 3 — Identity, secrets, data protection

Design authentication/authorization proportional to the system (a public
read-only prototype does not need the same identity architecture as a
multi-tenant system handling payment data). Be specific about secrets
management and encryption — "use encryption" is not a design.

## Step 4 — Data classification and residual risk

Classify data types by sensitivity and write concrete handling notes. For
any residual risk you accept rather than mitigate, write the rationale —
silent risk acceptance is not allowed.

## Step 5 — Validation and compliance

Every control needs a validation method — how would someone confirm it
actually works? For compliance, describe applicability considerations
only; never claim formal certification or legal sign-off — that requires
a human specialist outside this system.

## Boundaries

Do not redesign software components or AI workflows, select product
features, approve organizational risk, or approve the final blueprint.
