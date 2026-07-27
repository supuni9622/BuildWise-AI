# From Two-Minute Waits to Responsive AI Workflows

## How we reduced both perceived and actual latency in BuildWise AI

AI applications often feel fast in a prototype and painfully slow in a real
workflow.

The difference is rarely one slow model call. It is usually the architecture
around that call: synchronous APIs, repeated generation, validation retries,
and a frontend that cannot explain what is happening.

We encountered exactly this problem while building BuildWise AI, a
multi-stage product-consulting system powered by FastAPI, CrewAI, and
structured OpenAI outputs. A user could submit a product idea, answer
Discovery questions, and eventually receive a detailed product blueprint.
The results were useful, but moving from one stage to the next sometimes took
between 107 and 135 seconds.

This article explains why the original implementation behaved that way and
how we redesigned the workflow to feel responsive while also reducing the
amount of work performed after every clarification.

---

## The original implementation: one request did everything

The first version used a straightforward synchronous request lifecycle.

When a user started a consultation, the frontend called:

```text
POST /api/v1/consultations
```

The backend created a Flow and called `flow.kickoff()` before returning the
HTTP response.

Clarification answers followed the same pattern:

```text
POST /api/v1/consultations/{id}/clarifications
  → validate answers
  → persist answers
  → resume the CrewAI Flow
  → run Discovery again
  → validate the structured output
  → persist the new state
  → finally return the HTTP response
```

The browser remained attached to that request for the entire execution.

This design was simple. The endpoint returned the latest state, and the
frontend did not need a separate job system. But the simplicity came with a
significant user-experience cost.

### A long-running AI workflow looked like a frozen form

During an LLM call, the frontend received no new information. The button
displayed “Continuing…” while the same screen remained visible.

Even when the backend was actively:

- sending a request to OpenAI;
- retrying a transient failure;
- validating a structured response;
- re-running Discovery;
- or persisting a new clarification round,

the user saw no meaningful progress.

The application was working, but it looked stuck.

### Network requests inherited the latency of the entire Flow

An HTTP endpoint is a poor progress indicator for a multi-minute workflow.
Keeping the request open meant that reverse proxies, browsers, and users all
had to tolerate the full Flow duration.

In observed local runs, clarification requests took approximately:

```text
107 seconds
135 seconds
```

Those durations were not caused only by network latency. They represented the
combined cost of model generation, structured-output parsing, guardrail
validation, retries, tracing, and persistence.

### Every clarification regenerated the full Discovery artifact

The largest source of avoidable work was the resume path.

After receiving answers, the system sent the complete product context back to
the Discovery agent and requested another full `DiscoveryResult`. The model
regenerated:

- known facts;
- assumptions;
- unknowns;
- risks;
- interpretations;
- completeness;
- capability classification;
- source metadata;
- and clarification routing.

Most of those sections had already been accepted.

If the user answered a pricing question, there was no reason to regenerate
the product’s known features, risk inventory, source provenance, and
capability classification. Rebuilding the entire artifact consumed more
tokens, increased response time, and created more opportunities for an
otherwise unrelated field to fail validation.

### Validation retries multiplied the delay

BuildWise intentionally uses strict domain validation. For example:

- user-provided facts must reference provenance;
- blocking unknowns cannot allow downstream continuation;
- non-choice questions cannot contain selectable options;
- artifact session IDs must match the active Flow.

These rules protect downstream stages, but an LLM can return a JSON object
that satisfies the visible JSON Schema while violating a cross-field Pydantic
rule.

When that happened, CrewAI retried the task. A successful consultation could
therefore contain several alarming error messages in the middle and take
another full model call before advancing.

### Repeated clarification could become a loop

The state model already defined a maximum of three clarification rounds, but
the Discovery prompt did not know that it had reached the limit.

The model could continue finding useful questions indefinitely, while the
Flow rejected any round above the configured maximum. The limit existed in
code, but it was missing from the decision-making context.

---

## The optimization: separate acknowledgement from execution

The first architectural change was to stop treating a long-running Flow like
a normal request-response operation.

Both mutation endpoints now return:

```text
202 Accepted
```

The new start lifecycle is:

```text
POST /consultations
  → create typed state
  → persist the queued consultation
  → return 202 with the consultation ID
  → run the Flow in the background
```

Clarification submission works similarly:

```text
POST /consultations/{id}/clarifications
  → validate the active round and answers
  → persist the resumable state
  → return 202
  → resume the Flow in the background
```

The important detail is persistence before execution. Once the API says that
the request was accepted, the consultation and its submitted answers already
exist in durable storage.

The current implementation uses FastAPI’s in-process background-task
mechanism. This is appropriate for the present single-service architecture.
A production deployment that requires jobs to survive process termination
could replace this boundary with a durable worker queue without changing the
public API.

---

## Polling turns a black box into visible progress

After receiving `202 Accepted`, the frontend polls:

```text
GET /api/v1/consultations/{id}
```

every four seconds until the consultation:

- requests clarification;
- completes;
- completes with limitations;
- or fails.

The status response now includes an `active_operation` field. Instead of
displaying a generic spinner, the frontend can show messages such as:

- Queued for discovery
- Analyzing product discovery
- Re-evaluating discovery
- Defining product and MVP scope
- Selecting specialists
- Designing solution architecture
- Performing lead review
- Assembling product blueprint

Polling does not make an LLM respond faster, but it changes the experience
from “the form is frozen” to “the consultation is advancing through a known
operation.”

It also removes the entire model-execution duration from the mutation
request. The browser receives acknowledgement quickly and can recover the
latest state after a refresh.

---

## Incremental Discovery: regenerate decisions, not history

The second optimization reduces actual model work.

Initial Discovery still produces the full `DiscoveryResult`. That artifact is
the canonical baseline and contains all accepted facts, risks, provenance,
classification, and interpretations.

After clarification, however, the agent now returns a smaller
`DiscoveryRefinement` containing only:

- remaining unknowns;
- the updated completeness assessment;
- optional next clarification questions;
- the recommended next step;
- limitations;
- and updated confidence.

The prompt explicitly tells the agent not to regenerate:

- known facts;
- risks;
- capability classification;
- interpretations;
- or source metadata.

The application then performs a deterministic merge:

```text
Previous DiscoveryResult
        +
Accumulated clarification context
        +
DiscoveryRefinement
        ↓
Updated canonical DiscoveryResult
```

This keeps stable sections stable. It also ensures that system-owned session
identifiers remain authoritative and that every merged result still passes
the existing `DiscoveryResult` validators.

The improvement is more than token reduction. A smaller output has fewer
fields that can conflict, fewer opportunities for unrelated validation
errors, and a narrower task for the model to reason about.

---

## Clarification now has a visible, enforced boundary

The refinement task receives both:

```text
current clarification round
maximum clarification rounds
```

At the configured limit—three rounds in the current Flow—the prompt states:

- do not request another clarification round;
- return no clarification question set;
- continue with documented assumptions or limitations when responsible;
- otherwise fail Discovery explicitly.

The initial Discovery prompt also states that generated question-set round
numbers must never exceed the limit.

This aligns model behavior with deterministic Flow policy. The model decides
how to interpret unresolved product information, while the application
retains ownership of how many user-interaction cycles are permitted.

---

## Background failures must become state, not silence

Moving execution out of the HTTP request introduces an important failure
mode: an exception can no longer be returned directly as an HTTP 500 response.

Without additional handling, the frontend could poll a consultation that
remains “processing” forever.

The background runner therefore catches execution failures, reconstructs the
latest persisted state, records a normalized `SessionError`, and transitions
the consultation to `failed`.

The polling frontend can then stop and display a terminal failure rather than
spinning indefinitely.

This is a small implementation detail with a large operational effect:
asynchronous work needs an explicit terminal failure state.

---

## Before and after

| Concern | Previous implementation | Optimized implementation |
|---|---|---|
| Mutation response | Returned after Flow execution | Returns `202 Accepted` after persistence |
| Frontend feedback | One long loading state | Polling with active-operation messages |
| Clarification processing | Regenerated full Discovery | Generates a compact refinement |
| Stable Discovery sections | Rewritten by the LLM | Preserved deterministically |
| Clarification limit | Enforced only by state validation | Included in both prompt and state policy |
| Background failure | Not applicable; surfaced as HTTP failure | Persisted as terminal failed state |
| Refresh recovery | Depended on completed request | Reads latest persisted consultation |

---

## What this optimization does—and does not—solve

The redesign dramatically improves perceived responsiveness and reduces
clarification-time generation work.

It does not make every planning stage instantaneous. Product definition,
requirements, architecture, and lead review still involve substantial model
work. Their actual duration depends on provider response time, model choice,
output size, retries, and rate limits.

It also does not turn in-process background execution into a distributed job
system. If BuildWise is deployed across multiple instances or must guarantee
execution through server restarts, the next step is a durable queue with
worker ownership, leases, retry policy, and idempotency.

But the API and frontend no longer assume that work finishes inside one HTTP
request. That separation is the important foundation.

---

## The broader lesson

Latency in an AI product is not only a model-performance problem.

It is also an orchestration problem, a state-management problem, and a
communication problem.

The most effective changes in BuildWise came from asking three questions:

1. Does the user need the result now, or only confirmation that work started?
2. Are we regenerating information that has already been accepted?
3. Can the interface explain the operation currently in progress?

By returning early, polling durable state, narrowing the LLM’s refinement
task, and making workflow limits explicit, we transformed a two-minute frozen
request into a responsive, observable consultation.

The models still need time to think. The application no longer makes the user
wait in the dark.

![logs](image.png)
