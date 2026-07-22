# BuildWise AI — Full Architecture Flow

## 1. Overview

BuildWise AI is a CrewAI-powered product consulting board that transforms vague product ideas into build-ready product blueprints.

The system combines:

* FastAPI for the API layer
* CrewAI Flows for orchestration
* CrewAI Crews for specialist collaboration
* Human-in-the-loop clarification
* Dynamic specialist routing
* Structured outputs
* Guardrails
* Tool controls
* Cost tracking
* Structured logging
* CrewAI tracing
* Session persistence
* Docker-based deployment
* GitHub Actions for CI/CD

The workflow is designed to remain production-minded without introducing unnecessary infrastructure such as authentication, Kubernetes, distributed queues, or external monitoring platforms.

---

# 2. Full End-to-End Architecture Flow

```text
┌──────────────────────────────────────────────────────────────┐
│                       USER IDEA INPUT                        │
│                                                              │
│ Example:                                                     │
│ "I want to build an AI platform for customer support."       │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                      FASTAPI API LAYER                       │
│                                                              │
│ Responsibilities:                                            │
│                                                              │
│ - Validate request schema                                    │
│ - Validate idea length and required fields                   │
│ - Run semantic input checks                                  │
│ - Detect possible prompt injection                           │
│ - Detect secrets or credentials                              │
│ - Create consulting session                                  │
│ - Generate request ID and session ID                         │
│ - Apply rate limits                                          │
│ - Initialize token and cost budgets                          │
│ - Initialize structured logging context                      │
│ - Start CrewAI trace                                         │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
╔══════════════════════════════════════════════════════════════╗
║                    CREWAI FLOW ORCHESTRATOR                  ║
║                                                              ║
║ Controls:                                                    ║
║                                                              ║
║ - Workflow state                                             ║
║ - Stage transitions                                          ║
║ - Conditional routing                                        ║
║ - Pause and resume                                            ║
║ - Human feedback                                             ║
║ - Specialist selection                                       ║
║ - Parallel execution                                         ║
║ - Review loops                                                ║
║ - Final report generation                                    ║
╚══════════════════════════════════════════════════════════════╝
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                STAGE 1 — DISCOVERY AND INTAKE                │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │      Discovery Analyst       │
                 └──────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                    IDEA INTERPRETATION                       │
│                                                              │
│ The Discovery Analyst produces:                              │
│                                                              │
│ - Interpreted product idea                                   │
│ - Problem statement                                          │
│ - Initial target users                                       │
│ - Product category                                           │
│ - Industry or domain                                         │
│ - Initial business objective                                 │
│ - Known facts                                                │
│ - Inferred assumptions                                       │
│ - Unknown information                                        │
│ - Initial risks                                              │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │   Completeness Evaluator     │
                 └──────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                REQUIREMENT COMPLETENESS CHECK                │
│                                                              │
│ Evaluates whether enough information exists for:             │
│                                                              │
│ - Product definition                                         │
│ - Target users                                               │
│ - Core workflows                                             │
│ - Business goals                                             │
│ - AI involvement                                             │
│ - Data sensitivity                                           │
│ - Integrations                                               │
│ - Delivery constraints                                       │
│ - Expected scale                                             │
│ - Budget assumptions                                         │
└──────────────────────────────────────────────────────────────┘
                                │
                   ┌────────────┴────────────┐
                   │                         │
                   ▼                         ▼
        ┌────────────────────┐     ┌────────────────────────┐
        │ Information Enough │     │ Information Incomplete │
        └────────────────────┘     └────────────────────────┘
                   │                         │
                   │                         ▼
                   │           ┌────────────────────────────┐
                   │           │    Question Generator      │
                   │           └────────────────────────────┘
                   │                         │
                   │                         ▼
                   │     ┌──────────────────────────────────┐
                   │     │ Dynamic Clarification Questions  │
                   │     │                                  │
                   │     │ Questions may cover:             │
                   │     │                                  │
                   │     │ - Primary user                   │
                   │     │ - Core problem                   │
                   │     │ - User workflow                  │
                   │     │ - Data sources                   │
                   │     │ - AI expectations                │
                   │     │ - Integrations                   │
                   │     │ - Security constraints           │
                   │     │ - Scale                          │
                   │     │ - Timeline                       │
                   │     │ - Budget                         │
                   │     └──────────────────────────────────┘
                   │                         │
                   │                         ▼
                   │     ┌──────────────────────────────────┐
                   │     │       HUMAN-IN-THE-LOOP          │
                   │     │                                  │
                   │     │ - Persist current Flow state     │
                   │     │ - Pause execution                │
                   │     │ - Return questions through API   │
                   │     │ - Wait for user answers          │
                   │     └──────────────────────────────────┘
                   │                         │
                   │                         ▼
                   │     ┌──────────────────────────────────┐
                   │     │       USER SUBMITS ANSWERS       │
                   │     │                                  │
                   │     │ POST /sessions/{id}/answers      │
                   │     └──────────────────────────────────┘
                   │                         │
                   │                         ▼
                   │     ┌──────────────────────────────────┐
                   │     │         RESUME FLOW              │
                   │     │                                  │
                   │     │ - Validate answers               │
                   │     │ - Update confirmed facts         │
                   │     │ - Update assumptions             │
                   │     │ - Re-evaluate completeness       │
                   │     └──────────────────────────────────┘
                   │                         │
                   └─────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│              STAGE 2 — SPECIALIST PLANNING FLOW              │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │      Specialist Planner      │
                 └──────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                  SPECIALIST SELECTION LOGIC                  │
│                                                              │
│ Always selected:                                             │
│                                                              │
│ - Product Manager                                            │
│ - Business Analyst                                           │
│ - Solution Architect                                         │
│ - Lead Reviewer                                              │
│                                                              │
│ Conditionally selected:                                      │
│                                                              │
│ - Market Analyst                                             │
│ - AI Architect                                               │
│ - Security Architect                                         │
│ - Engineering Lead                                           │
│ - QA and Evaluation Architect                                │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                 SPECIALIST ROUTING EXAMPLES                  │
│                                                              │
│ Run Market Analyst when:                                     │
│                                                              │
│ - Market validation is required                              │
│ - Competitor research is useful                              │
│ - Current trends affect the recommendation                   │
│ - Product positioning is unclear                             │
│                                                              │
│ Run AI Architect when:                                       │
│                                                              │
│ - AI is part of the product                                  │
│ - AI may create meaningful value                             │
│ - Model, RAG, agent, or automation decisions are needed      │
│                                                              │
│ Run Security Architect when:                                 │
│                                                              │
│ - Sensitive data is involved                                 │
│ - External integrations exist                                │
│ - Autonomous actions exist                                   │
│ - Regulated domains are involved                             │
│                                                              │
│ Run Engineering Lead when:                                   │
│                                                              │
│ - Delivery complexity is high                                │
│ - Integration complexity is high                             │
│ - Migration constraints exist                                │
│ - Maintainability requires separate review                   │
│                                                              │
│ Run QA and Evaluation Architect when:                        │
│                                                              │
│ - AI quality requires evaluation                             │
│ - Safety-critical workflows exist                            │
│ - Reliability requirements are significant                  │
│ - Acceptance criteria are complex                            │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│              STAGE 3 — PRODUCT AND REQUIREMENTS CREW         │
└──────────────────────────────────────────────────────────────┘
                                │
                  ┌─────────────┴─────────────┐
                  │                           │
                  ▼                           ▼
       ┌──────────────────────┐    ┌────────────────────────┐
       │   Product Manager    │    │    Business Analyst    │
       └──────────────────────┘    └────────────────────────┘
                  │                           │
                  └─────────────┬─────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                 PRODUCT CREW DELIVERABLES                    │
│                                                              │
│ Product Manager:                                             │
│                                                              │
│ - Product vision                                             │
│ - Value proposition                                          │
│ - Target users                                               │
│ - User personas                                              │
│ - Product goals                                              │
│ - Success metrics                                            │
│ - MVP scope                                                  │
│ - Future scope                                               │
│ - Feature prioritization                                     │
│                                                              │
│ Business Analyst:                                            │
│                                                              │
│ - Business workflows                                         │
│ - Functional requirements                                    │
│ - Non-functional requirements                                │
│ - Business rules                                              │
│ - User stories                                                │
│ - Acceptance criteria                                         │
│ - Edge cases                                                   │
│ - Integration requirements                                   │
│ - Data requirements                                           │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│             PRODUCT OUTPUT VALIDATION GATE                   │
│                                                              │
│ Checks:                                                       │
│                                                              │
│ - Required sections exist                                    │
│ - Requirements match the confirmed idea                      │
│ - Assumptions are explicit                                   │
│ - Requirements are not contradictory                         │
│ - Acceptance criteria are testable                           │
│ - MVP scope is realistic                                     │
│                                                              │
│ On failure:                                                   │
│                                                              │
│ - Perform one targeted repair attempt                         │
│ - Record validation failure                                  │
│ - Stop if the repair fails                                   │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│               STAGE 4 — SPECIALIST DESIGN CREW               │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
╔══════════════════════════════════════════════════════════════╗
║                      PARALLEL EXECUTION                      ║
╚══════════════════════════════════════════════════════════════╝
                                │
        ┌───────────────────────┼────────────────────────┐
        │                       │                        │
        ▼                       ▼                        ▼
┌──────────────────┐  ┌──────────────────┐    ┌──────────────────┐
│ Solution         │  │ AI Architect     │    │ Security         │
│ Architect        │  │ Conditional      │    │ Architect        │
│ Always Runs      │  │                  │    │ Conditional      │
└──────────────────┘  └──────────────────┘    └──────────────────┘
        │                       │                        │
        │                       │                        │
        ▼                       ▼                        ▼
┌──────────────────┐  ┌──────────────────┐    ┌──────────────────┐
│ System           │  │ AI Suitability   │    │ Threat Model     │
│ Architecture     │  │ Model Strategy   │    │ Data Security    │
│ Components       │  │ RAG / Agents     │    │ Privacy          │
│ APIs             │  │ Prompts          │    │ Guardrails       │
│ Data Flow        │  │ Evaluation       │    │ Access Controls  │
│ Deployment       │  │ Cost Strategy    │    │ AI Security      │
│ Reliability      │  │ Fallbacks        │    │ Abuse Risks      │
└──────────────────┘  └──────────────────┘    └──────────────────┘

        ┌───────────────────────┼────────────────────────┐
        │                       │                        │
        ▼                       ▼                        ▼
┌──────────────────┐  ┌──────────────────┐    ┌──────────────────┐
│ Engineering      │  │ QA and           │    │ Market Analyst   │
│ Lead             │  │ Evaluation       │    │ Conditional      │
│ Conditional      │  │ Architect        │    │                  │
└──────────────────┘  └──────────────────┘    └──────────────────┘
        │                       │                        │
        ▼                       ▼                        ▼
┌──────────────────┐  ┌──────────────────┐    ┌──────────────────┐
│ Delivery Plan    │  │ Test Strategy    │    │ Market Context   │
│ Dependencies     │  │ AI Evaluation    │    │ Competitors      │
│ Complexity       │  │ Quality Metrics  │    │ Trends           │
│ Maintainability  │  │ Safety Tests     │    │ Positioning      │
│ Tech Debt        │  │ Failure Tests    │    │ Differentiation  │
│ Team Skills      │  │ Acceptance Plan  │    │ Market Risks     │
└──────────────────┘  └──────────────────┘    └──────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                    CONTROLLED TOOL LAYER                     │
│                                                              │
│ Tool access is restricted by agent.                          │
│                                                              │
│ Market Analyst tools:                                        │
│                                                              │
│ - Web search                                                 │
│ - Competitor research                                        │
│ - Market trend lookup                                        │
│                                                              │
│ Solution Architect tools:                                    │
│                                                              │
│ - Official technical documentation search                    │
│ - Technology capability verification                         │
│                                                              │
│ AI Architect tools:                                          │
│                                                              │
│ - Official model documentation search                         │
│ - Model capability and pricing lookup                         │
│                                                              │
│ Security Architect tools:                                    │
│                                                              │
│ - Approved security reference lookup                          │
│                                                              │
│ Every tool includes:                                         │
│                                                              │
│ - Typed input schema                                          │
│ - Timeout                                                     │
│ - Retry policy                                                │
│ - Maximum result count                                        │
│ - Maximum output size                                         │
│ - Allowed domain controls                                     │
│ - Output sanitization                                         │
│ - Invocation logging                                          │
│ - Cost tracking                                               │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                SPECIALIST OUTPUT VALIDATION                  │
│                                                              │
│ Checks:                                                       │
│                                                              │
│ - Pydantic schema compliance                                  │
│ - Required recommendations present                            │
│ - Recommendations tied to requirements                        │
│ - Assumptions explicitly identified                           │
│ - Risks include mitigations                                   │
│ - Confidence is within valid bounds                           │
│ - Sources are not fabricated                                  │
│ - Tool results are treated as untrusted data                  │
│                                                              │
│ On failure:                                                   │
│                                                              │
│ - Attempt one structured repair                               │
│ - Mark specialist result as partial if repair fails           │
│ - Continue when safe                                          │
│ - Surface missing analysis in the final report                │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                 STAGE 5 — REVIEW AND REFLECTION              │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │        Lead Reviewer         │
                 └──────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                    REVIEWER RESPONSIBILITIES                 │
│                                                              │
│ - Detect contradictions                                      │
│ - Detect missing requirements                                │
│ - Detect unsupported assumptions                             │
│ - Detect unrealistic technology choices                      │
│ - Detect excessive complexity                                │
│ - Detect missing security controls                           │
│ - Detect weak AI evaluation plans                            │
│ - Detect missing cost considerations                         │
│ - Detect market recommendation gaps                          │
│ - Validate MVP feasibility                                   │
│ - Validate architecture-to-requirement alignment             │
│ - Validate delivery roadmap                                  │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Review Decision     │
                    └───────────────────────┘
                                │
              ┌─────────────────┴─────────────────┐
              │                                   │
              ▼                                   ▼
   ┌────────────────────────┐          ┌────────────────────────┐
   │        Approved        │          │  Refinement Required   │
   └────────────────────────┘          └────────────────────────┘
              │                                   │
              │                                   ▼
              │                     ┌────────────────────────────┐
              │                     │ Targeted Specialist Repair │
              │                     │                            │
              │                     │ - Specific issue only      │
              │                     │ - Selected agent only      │
              │                     │ - Maximum one iteration    │
              │                     │ - No endless discussion    │
              │                     └────────────────────────────┘
              │                                   │
              │                                   ▼
              │                     ┌────────────────────────────┐
              │                     │       Final Re-Review      │
              │                     └────────────────────────────┘
              │                                   │
              └───────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                STAGE 6 — BLUEPRINT GENERATION                │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                    FINAL PRODUCT BLUEPRINT                   │
│                                                              │
│ 1. Executive Summary                                         │
│ 2. Original Idea                                             │
│ 3. Interpreted Problem                                       │
│ 4. Confirmed Facts                                           │
│ 5. Assumptions                                               │
│ 6. Open Questions                                            │
│ 7. Target Users                                              │
│ 8. Market Context                                            │
│ 9. Value Proposition                                         │
│ 10. Product Vision                                           │
│ 11. MVP Scope                                                │
│ 12. Future Scope                                             │
│ 13. User Journeys                                            │
│ 14. Functional Requirements                                  │
│ 15. Non-Functional Requirements                              │
│ 16. Business Rules                                           │
│ 17. Acceptance Criteria                                      │
│ 18. Proposed System Architecture                             │
│ 19. Component Design                                         │
│ 20. API and Integration Design                               │
│ 21. Data Architecture                                        │
│ 22. AI Suitability Assessment                                │
│ 23. AI Architecture                                          │
│ 24. Model Strategy                                           │
│ 25. RAG or Agent Strategy                                    │
│ 26. Prompt and Tool Strategy                                 │
│ 27. AI Evaluation Strategy                                   │
│ 28. Security Architecture                                    │
│ 29. AI Security Controls                                     │
│ 30. Privacy Considerations                                   │
│ 31. Reliability and Failure Handling                         │
│ 32. Testing Strategy                                         │
│ 33. Deployment Architecture                                  │
│ 34. Observability Requirements                               │
│ 35. Cost Drivers                                             │
│ 36. Cost Optimization Recommendations                        │
│ 37. Risks and Mitigations                                    │
│ 38. Trade-Offs                                               │
│ 39. Delivery Roadmap                                         │
│ 40. Final Recommendation                                     │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                   FINAL OUTPUT VALIDATION                    │
│                                                              │
│ Checks:                                                       │
│                                                              │
│ - All mandatory sections exist                               │
│ - No unresolved placeholders remain                          │
│ - Confirmed user facts are respected                         │
│ - Assumptions remain visible                                 │
│ - Architecture supports product requirements                 │
│ - AI recommendations include evaluation                      │
│ - Security risks include controls                            │
│ - Costs are clearly estimates                                │
│ - Sources are attached where external research was used      │
│ - Failed specialist analyses are disclosed                   │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                     OUTPUT DELIVERY                          │
│                                                              │
│ Formats:                                                      │
│                                                              │
│ - Structured JSON blueprint                                  │
│ - Markdown product blueprint                                 │
│ - Architecture recommendations                               │
│ - Delivery roadmap                                           │
│ - Session usage summary                                      │
│ - Trace identifier                                           │
│                                                              │
│ API endpoints:                                                │
│                                                              │
│ - GET /sessions/{id}                                         │
│ - GET /sessions/{id}/blueprint                               │
│ - GET /sessions/{id}/report                                  │
│ - GET /sessions/{id}/usage                                   │
└──────────────────────────────────────────────────────────────┘
```

---

# 3. High-Level System Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                         FRONTEND                             │
│                                                              │
│ Built separately using Claude Code                           │
│                                                              │
│ Responsibilities:                                            │
│                                                              │
│ - Idea submission                                            │
│ - Clarification question UI                                  │
│ - Human feedback submission                                  │
│ - Progress visualization                                     │
│ - Session status                                             │
│ - Blueprint rendering                                        │
│ - Markdown export                                            │
│ - Cost and usage summary                                     │
└──────────────────────────────────────────────────────────────┘
                                │
                                │ HTTPS / JSON
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                       FASTAPI BACKEND                        │
│                                                              │
│ Responsibilities:                                            │
│                                                              │
│ - API routing                                                │
│ - Request validation                                         │
│ - Rate limiting                                              │
│ - Session lifecycle                                          │
│ - Error handling                                             │
│ - Logging                                                    │
│ - Response serialization                                     │
│ - Health and readiness checks                                │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                  APPLICATION SERVICE LAYER                   │
│                                                              │
│ - Session Service                                            │
│ - Flow Execution Service                                     │
│ - Human Feedback Service                                     │
│ - Blueprint Service                                          │
│ - Usage and Cost Service                                     │
│ - Validation Service                                         │
│ - Guardrail Service                                          │
│ - Tool Execution Service                                     │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                     CREWAI FLOW LAYER                        │
│                                                              │
│ - Intake                                                     │
│ - Discovery                                                  │
│ - Completeness routing                                       │
│ - Human feedback                                             │
│ - Specialist planning                                        │
│ - Crew execution                                             │
│ - Review                                                     │
│ - Refinement                                                 │
│ - Blueprint generation                                       │
└──────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                     CREWAI CREW LAYER                        │
│                                                              │
│ Crews:                                                       │
│                                                              │
│ - Discovery Crew                                             │
│ - Product and Requirements Crew                              │
│ - Technical Specialist Crew                                  │
│ - Review Crew                                                │
│                                                              │
│ Agents:                                                      │
│                                                              │
│ - Discovery Analyst                                          │
│ - Product Manager                                            │
│ - Business Analyst                                           │
│ - Solution Architect                                         │
│ - Market Analyst                                             │
│ - AI Architect                                               │
│ - Security Architect                                         │
│ - Engineering Lead                                           │
│ - QA and Evaluation Architect                                │
│ - Lead Reviewer                                              │
└──────────────────────────────────────────────────────────────┘
             │                  │                  │
             ▼                  ▼                  ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ TOOL LAYER       │  │ LLM PROVIDER     │  │ PERSISTENCE      │
│                  │  │                  │  │                  │
│ - Web search     │  │ - Main model     │  │ - Sessions       │
│ - Docs lookup    │  │ - Repair model   │  │ - Flow state     │
│ - Cost lookup    │  │ - Embeddings not │  │ - Questions      │
│ - Security refs  │  │   required       │  │ - Answers        │
│                  │  │                  │  │ - Outputs        │
└──────────────────┘  └──────────────────┘  └──────────────────┘
             │                  │                  │
             └──────────────────┼──────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                  OBSERVABILITY AND CONTROL                   │
│                                                              │
│ - CrewAI Tracing                                             │
│ - Structured application logs                                │
│ - Request IDs                                                │
│ - Session IDs                                                │
│ - Token usage                                                │
│ - Cost estimates                                             │
│ - Tool invocation tracking                                   │
│ - Retry tracking                                             │
│ - Error tracking                                             │
│ - Metrics summary                                            │
└──────────────────────────────────────────────────────────────┘
```

---

# 4. CrewAI Responsibility Boundaries

## CrewAI Flows

CrewAI Flows control the workflow.

Flows are responsible for:

* Maintaining canonical state
* Deciding the next workflow stage
* Routing between branches
* Pausing for human feedback
* Resuming from persisted state
* Selecting specialists
* Starting crews
* Aggregating results
* Triggering review
* Triggering one bounded refinement cycle
* Generating the final blueprint

Flows should not contain large specialist prompts or complex domain reasoning.

---

## CrewAI Crews

CrewAI Crews perform collaborative specialist work.

Crews are responsible for:

* Product definition
* Business analysis
* Technical architecture
* AI architecture
* Security analysis
* Market analysis
* Quality and evaluation planning
* Engineering feasibility
* Review and synthesis

Crews should not control API sessions, rate limits, persistence, or HTTP lifecycle behavior.

---

## Application Layer

The application owns operational concerns.

The application layer is responsible for:

* FastAPI requests and responses
* Session creation
* Session lookup
* Persistence
* Rate limiting
* Logging
* Error handling
* Usage calculation
* Cost tracking
* Guardrail execution
* Tool policy enforcement
* Health endpoints
* Configuration

---

# 5. Canonical Flow State

The CrewAI Flow should use a structured state model.

```text
SolutionDesignState
│
├── identifiers
│   ├── request_id
│   ├── session_id
│   ├── flow_id
│   └── trace_id
│
├── intake
│   ├── original_idea
│   ├── additional_context
│   ├── preferred_output
│   └── submitted_at
│
├── discovery
│   ├── interpreted_idea
│   ├── problem_statement
│   ├── product_category
│   ├── industry
│   ├── target_users
│   ├── known_facts
│   ├── assumptions
│   ├── unknowns
│   └── completeness_score
│
├── human_feedback
│   ├── clarification_round
│   ├── pending_questions
│   ├── answered_questions
│   ├── skipped_questions
│   └── waiting_for_user
│
├── planning
│   ├── selected_specialists
│   ├── skipped_specialists
│   ├── specialist_reasons
│   ├── execution_order
│   └── estimated_execution_cost
│
├── product_design
│   ├── product_vision
│   ├── value_proposition
│   ├── personas
│   ├── user_journeys
│   ├── mvp_scope
│   ├── future_scope
│   ├── functional_requirements
│   ├── non_functional_requirements
│   ├── business_rules
│   └── acceptance_criteria
│
├── specialist_outputs
│   ├── market_analysis
│   ├── solution_architecture
│   ├── ai_architecture
│   ├── security_architecture
│   ├── engineering_plan
│   └── qa_evaluation_plan
│
├── review
│   ├── contradictions
│   ├── missing_sections
│   ├── unsupported_assumptions
│   ├── overengineering_findings
│   ├── required_refinements
│   ├── review_status
│   └── refinement_count
│
├── final_output
│   ├── blueprint
│   ├── markdown_report
│   ├── output_status
│   └── generated_at
│
└── usage
    ├── input_tokens
    ├── output_tokens
    ├── estimated_cost_usd
    ├── tool_calls
    ├── agent_runs
    ├── retries
    ├── started_at
    └── completed_at
```

---

# 6. API Architecture

## Session Creation

```http
POST /api/v1/sessions
```

Purpose:

* Accept the vague idea
* Validate the request
* Create a session
* Start the discovery Flow

Possible responses:

* `PROCESSING`
* `AWAITING_USER_INPUT`
* `COMPLETED`
* `FAILED`

---

## Retrieve Session

```http
GET /api/v1/sessions/{session_id}
```

Returns:

* Current status
* Current stage
* Pending questions
* Progress summary
* Usage summary
* Error details when applicable

---

## Submit Clarification Answers

```http
POST /api/v1/sessions/{session_id}/answers
```

Purpose:

* Validate answers
* Save human feedback
* Resume the CrewAI Flow

---

## Retrieve Final Blueprint

```http
GET /api/v1/sessions/{session_id}/blueprint
```

Returns:

* Structured JSON blueprint
* Metadata
* Usage and cost summary
* Trace identifier

---

## Retrieve Markdown Report

```http
GET /api/v1/sessions/{session_id}/report
```

Returns:

* Markdown report
* Report metadata
* Generation status

---

## Retrieve Usage

```http
GET /api/v1/sessions/{session_id}/usage
```

Returns:

* Token usage
* Estimated cost
* Agent runs
* Tool calls
* Retries
* Execution duration

---

## Health Endpoints

```http
GET /health
GET /ready
GET /metrics/summary
```

---

# 7. Validation Architecture

```text
Incoming Request
       │
       ▼
Pydantic Schema Validation
       │
       ▼
Deterministic Input Validation
       │
       ▼
Semantic Input Validation
       │
       ▼
Prompt Injection Check
       │
       ▼
Secret Detection
       │
       ▼
Request Accepted
```

Output validation:

```text
Agent Output
       │
       ▼
Pydantic Schema Validation
       │
       ▼
Domain Validation
       │
       ▼
Requirement Consistency Check
       │
       ▼
Assumption Check
       │
       ▼
Source and Evidence Check
       │
       ▼
One Repair Attempt
       │
       ▼
Accept or Mark Partial
```

---

# 8. Guardrail Architecture

## Input Guardrails

* Maximum input length
* Empty or meaningless idea detection
* Prompt injection pattern detection
* Secret and API key detection
* Unsupported or unsafe request detection
* Excessive payload rejection
* Request rate enforcement

## Tool Guardrails

* Agent-specific tool allowlist
* Typed tool inputs
* Domain allowlists
* Result limits
* Timeouts
* Bounded retries
* Output sanitization
* No arbitrary code execution
* No uncontrolled filesystem access
* No unrestricted network access

## Agent Output Guardrails

* Structured output validation
* No fabricated sources
* Facts separated from assumptions
* Recommendations include rationale
* Risks include mitigations
* Cost estimates labeled as estimates
* Confidence values validated
* No unsupported guarantees

## Final Blueprint Guardrails

* Requirement and architecture alignment
* Security coverage
* AI evaluation coverage
* Operational coverage
* Cost consideration coverage
* Open questions preserved
* Failed analyses disclosed
* No unresolved placeholders

---

# 9. AI Security Architecture

The system must protect against:

* Direct prompt injection
* Indirect prompt injection from web results
* Sensitive information exposure
* Cross-session data leakage
* Excessive tool permissions
* Untrusted external content
* Fabricated citations
* Unsafe autonomous recommendations
* Retry-based cost exhaustion
* Oversized requests
* Tool output manipulation
* Hidden instruction attacks

Security principle:

> All user input, external content, and tool output must be treated as untrusted data.

External content must never override:

* System instructions
* Agent role instructions
* Tool policies
* Output schemas
* Guardrails

---

# 10. Error Handling Architecture

```text
Failure
  │
  ├── Input Validation Error
  │       └── Return 422
  │
  ├── Rate Limit Error
  │       └── Return 429
  │
  ├── Session Not Found
  │       └── Return 404
  │
  ├── Session State Conflict
  │       └── Return 409
  │
  ├── LLM Temporary Error
  │       └── Retry with backoff
  │
  ├── Tool Timeout
  │       └── Retry once or mark partial
  │
  ├── Structured Output Failure
  │       └── One repair attempt
  │
  ├── Specialist Failure
  │       └── Continue with partial result
  │
  ├── Persistence Failure
  │       └── Stop safely
  │
  └── Unknown Failure
          └── Return normalized internal error
```

Canonical error response:

```json
{
  "code": "SPECIALIST_EXECUTION_FAILED",
  "message": "The security review could not be completed.",
  "recoverable": true,
  "stage": "specialist_design",
  "session_id": "session-id",
  "request_id": "request-id"
}
```

---

# 11. Retry Policy

| Failure Type                     |                     Retry Policy |
| -------------------------------- | -------------------------------: |
| Temporary LLM provider failure   |                Maximum 2 retries |
| LLM rate limit                   |   Maximum 2 retries with backoff |
| Tool timeout                     |                  Maximum 1 retry |
| Invalid structured output        |         Maximum 1 repair attempt |
| Deterministic validation failure |                   No blind retry |
| Unsafe input                     |                         No retry |
| Invalid configuration            |                         No retry |
| Persistence failure              | No retry unless transaction-safe |
| Specialist refinement            |              Maximum 1 iteration |

---

# 12. Cost Control Architecture

Each session should define:

```text
Maximum Session Tokens
Maximum Session Cost
Maximum Agent Runs
Maximum Tool Calls
Maximum Clarification Rounds
Maximum Refinement Rounds
```

Track:

* Input tokens
* Output tokens
* Agent-level usage
* Task-level usage
* Tool calls
* Retry usage
* Estimated cost
* Total execution duration

When the session budget approaches its limit:

* Skip low-priority market research
* Reduce tool search depth
* Reduce optional specialist execution
* Use a smaller model for repair tasks
* Preserve architecture and final review
* Record that analysis depth was reduced

---

# 13. Logging Architecture

Use structured JSON logs.

Every relevant log entry should contain:

```text
timestamp
log_level
request_id
session_id
flow_id
trace_id
stage
agent_name
task_name
tool_name
status
duration_ms
retry_count
input_tokens
output_tokens
estimated_cost_usd
error_code
```

Do not log:

* API keys
* Credentials
* Raw secrets
* Complete system prompts
* Hidden chain-of-thought
* Sensitive user data unnecessarily
* Full unredacted tool responses

---

# 14. CrewAI Tracing Architecture

CrewAI tracing should capture:

* Flow execution
* Flow stage transitions
* Conditional routes
* Human feedback pauses
* Crew executions
* Agent executions
* Task executions
* LLM calls
* Tool calls
* Latency
* Token usage
* Failures
* Refinement loops

Use CrewAI tracing for agent behavior visibility.

Use structured application logs for:

* API behavior
* Validation
* Persistence
* Rate limiting
* Session lifecycle
* Application errors

---

# 15. Persistence Architecture

For the first deployable version:

* SQLite may be used locally.
* PostgreSQL should be supported for hosted deployment.

Persist:

* Sessions
* Flow status
* Flow stage
* Clarification questions
* User answers
* Specialist selection
* Specialist results
* Review findings
* Final blueprint
* Markdown report
* Usage summary
* Error details

Persistence is required because human feedback pauses the workflow between requests.

---

# 16. Deployment Architecture

```text
Developer Push
      │
      ▼
GitHub Repository
      │
      ▼
GitHub Actions
      │
      ├── Ruff
      ├── Mypy
      ├── Pytest
      ├── Security Checks
      ├── Docker Build
      └── Container Smoke Test
      │
      ▼
Container Registry
      │
      ▼
Deployment Platform
      │
      ├── BuildWise API Container
      └── PostgreSQL Database
```

The backend should include:

* Multi-stage Dockerfile
* Non-root user
* Health check
* Production ASGI server
* Environment-based settings
* `.dockerignore`
* Pinned dependencies
* Startup validation

---

# 17. GitHub Actions Architecture

## CI Workflow

Run on:

* Pull requests
* Pushes to main

Steps:

* Install `uv`
* Install dependencies
* Run Ruff lint
* Run Ruff format check
* Run mypy
* Run pytest
* Run coverage
* Run application startup smoke test

## Docker Workflow

Run on:

* Push to main
* Version tags

Steps:

* Build Docker image
* Start container
* Call `/health`
* Call `/ready`
* Publish image when configured

## Security Workflow

Run:

* Dependency audit
* Secret scanning
* Static security checks
* Container image scanning

---

# 18. Explicitly Excluded Architecture

The first version will not include:

* Authentication
* User accounts
* Organization management
* Multi-tenancy
* Role-based authorization
* Billing
* Kubernetes
* Distributed workers
* Message brokers
* External monitoring platforms
* Prometheus
* Grafana
* OpenTelemetry infrastructure
* Vector databases
* Long-term memory
* Complex model routing
* Enterprise compliance automation
* Plugin systems
* Unbounded autonomous agent loops

These exclusions keep the project focused on CrewAI orchestration and practical AI engineering.

---

# 19. Final Architecture Summary

```text
User provides vague idea
          │
          ▼
FastAPI validates and creates session
          │
          ▼
CrewAI Flow starts discovery
          │
          ▼
Discovery Analyst interprets the idea
          │
          ▼
Completeness Evaluator checks missing information
          │
          ├── Enough information
          │
          └── Ask questions and pause
                         │
                         ▼
                  Human answers
                         │
                         ▼
                    Resume Flow
          │
          ▼
Specialist Planner selects required agents
          │
          ▼
Product Manager and Business Analyst define product
          │
          ▼
Technical specialists execute in parallel
          │
          ▼
Outputs pass validation and guardrails
          │
          ▼
Lead Reviewer detects gaps and contradictions
          │
          ├── Approve
          │
          └── One targeted refinement
          │
          ▼
Generate build-ready Product Blueprint
          │
          ▼
Validate final output
          │
          ▼
Return JSON, Markdown, usage and trace metadata
```

---

# 20. Core Architecture Principle

> CrewAI Flows own orchestration. CrewAI Crews own specialist reasoning. FastAPI and application services own operational control.

This separation prevents CrewAI agents from becoming responsible for API lifecycle, persistence, security, rate limiting, and platform concerns that belong in the application layer.

# 21. Full architecture diagram 

```mermaid
flowchart TD

    %% =========================================================
    %% USER AND API ENTRY
    %% =========================================================

    USER["User submits a vague product idea"]

    API["FastAPI API Layer<br/><br/>
    • Request schema validation<br/>
    • Rate limiting<br/>
    • Request and session IDs<br/>
    • Structured logging context<br/>
    • Session cost/token budget<br/>
    • CrewAI trace initialization"]

    INPUT_GUARDRAILS{"Input guardrails passed?"}

    INPUT_REJECT["Reject request<br/><br/>
    • Validation error<br/>
    • Unsafe request<br/>
    • Prompt injection detected<br/>
    • Secret or credential detected<br/>
    • Rate limit exceeded"]

    SESSION["Create Consulting Session<br/><br/>
    Status: PROCESSING"]

    INIT_STATE["Initialize Solution Design State<br/><br/>
    • Original idea<br/>
    • Known context<br/>
    • Assumptions<br/>
    • Clarification round = 0<br/>
    • Refinement count = 0<br/>
    • Usage and cost counters"]

    USER --> API
    API --> INPUT_GUARDRAILS
    INPUT_GUARDRAILS -- No --> INPUT_REJECT
    INPUT_GUARDRAILS -- Yes --> SESSION
    SESSION --> INIT_STATE

    %% =========================================================
    %% DISCOVERY FLOW
    %% =========================================================

    subgraph DISCOVERY["Stage 1 — Discovery Flow"]

        DISCOVERY_AGENT["Discovery Analyst<br/><br/>
        • Interpret product idea<br/>
        • Identify problem<br/>
        • Classify domain<br/>
        • Identify target users<br/>
        • Extract known facts<br/>
        • Generate explicit assumptions<br/>
        • Identify unknowns"]

        DISCOVERY_VALIDATE{"Discovery output valid?"}

        DISCOVERY_REPAIR["Targeted discovery output repair<br/><br/>
        Maximum: 1 attempt"]

        DISCOVERY_REPAIR_VALID{"Repair successful?"}

        DISCOVERY_FAIL["Fail session safely<br/><br/>
        Error: DISCOVERY_OUTPUT_INVALID"]

        COMPLETENESS["Completeness Evaluator<br/><br/>
        Evaluate:<br/>
        • Product goal<br/>
        • Target users<br/>
        • Core workflow<br/>
        • Business constraints<br/>
        • Data requirements<br/>
        • AI expectations<br/>
        • Integrations<br/>
        • Security sensitivity<br/>
        • Scale<br/>
        • Timeline and budget"]

        INFO_COMPLETE{"Enough information<br/>to continue?"}

        ROUND_LIMIT{"Clarification round<br/>limit reached?"}

        QUESTION_GENERATOR["Dynamic Question Generator<br/><br/>
        Generate 3–5 focused questions<br/>
        only for high-impact unknowns"]

        QUESTIONS_VALIDATE{"Questions valid<br/>and non-duplicated?"}

        QUESTIONS_REPAIR["Repair clarification questions<br/><br/>
        Maximum: 1 attempt"]

        QUESTIONS_REPAIR_VALID{"Repair successful?"}

        USE_ASSUMPTIONS["Continue using explicit assumptions<br/><br/>
        Mark unanswered information<br/>
        as uncertain"]

        SAVE_CHECKPOINT["Persist Flow State<br/><br/>
        • Questions<br/>
        • Current stage<br/>
        • Assumptions<br/>
        • Usage metadata"]

        PAUSE["Pause CrewAI Flow<br/><br/>
        Session status:<br/>
        AWAITING_USER_INPUT"]

        RETURN_QUESTIONS["Return clarification questions<br/>to frontend"]

        HUMAN["Human answers questions"]

        ANSWER_API["POST /sessions/{id}/answers"]

        ANSWER_VALIDATE{"Answers valid<br/>for current session?"}

        ANSWER_REJECT["Return answer validation error<br/><br/>
        Session remains paused"]

        UPDATE_STATE["Update Flow State<br/><br/>
        • Confirmed facts<br/>
        • Rejected assumptions<br/>
        • New constraints<br/>
        • Skipped questions<br/>
        • Clarification round + 1"]

        RESUME["Resume CrewAI Flow"]

        RECHECK["Re-run completeness evaluation"]
    end

    INIT_STATE --> DISCOVERY_AGENT
    DISCOVERY_AGENT --> DISCOVERY_VALIDATE

    DISCOVERY_VALIDATE -- No --> DISCOVERY_REPAIR
    DISCOVERY_REPAIR --> DISCOVERY_REPAIR_VALID
    DISCOVERY_REPAIR_VALID -- No --> DISCOVERY_FAIL
    DISCOVERY_REPAIR_VALID -- Yes --> COMPLETENESS
    DISCOVERY_VALIDATE -- Yes --> COMPLETENESS

    COMPLETENESS --> INFO_COMPLETE

    INFO_COMPLETE -- Yes --> SPECIALIST_PLANNING
    INFO_COMPLETE -- No --> ROUND_LIMIT

    ROUND_LIMIT -- Yes --> USE_ASSUMPTIONS
    USE_ASSUMPTIONS --> SPECIALIST_PLANNING

    ROUND_LIMIT -- No --> QUESTION_GENERATOR
    QUESTION_GENERATOR --> QUESTIONS_VALIDATE

    QUESTIONS_VALIDATE -- No --> QUESTIONS_REPAIR
    QUESTIONS_REPAIR --> QUESTIONS_REPAIR_VALID
    QUESTIONS_REPAIR_VALID -- No --> USE_ASSUMPTIONS
    QUESTIONS_REPAIR_VALID -- Yes --> SAVE_CHECKPOINT
    QUESTIONS_VALIDATE -- Yes --> SAVE_CHECKPOINT

    SAVE_CHECKPOINT --> PAUSE
    PAUSE --> RETURN_QUESTIONS
    RETURN_QUESTIONS --> HUMAN
    HUMAN --> ANSWER_API
    ANSWER_API --> ANSWER_VALIDATE

    ANSWER_VALIDATE -- No --> ANSWER_REJECT
    ANSWER_REJECT --> HUMAN

    ANSWER_VALIDATE -- Yes --> UPDATE_STATE
    UPDATE_STATE --> RESUME
    RESUME --> RECHECK
    RECHECK --> COMPLETENESS

    %% =========================================================
    %% SPECIALIST PLANNING
    %% =========================================================

    subgraph PLANNING["Stage 2 — Specialist Planning"]

        SPECIALIST_PLANNING["Specialist Planner<br/><br/>
        Analyze product complexity,<br/>
        domain, risk, AI needs,<br/>
        market needs and budget"]

        ALWAYS_SELECTED["Always Select<br/><br/>
        • Product Manager<br/>
        • Business Analyst<br/>
        • Solution Architect<br/>
        • Lead Reviewer"]

        MARKET_DECISION{"Market validation<br/>or current trend research needed?"}

        AI_DECISION{"AI capability,<br/>RAG, agent, model or<br/>automation decision needed?"}

        SECURITY_DECISION{"Sensitive data,<br/>external integrations,<br/>autonomous actions or<br/>regulated domain?"}

        ENGINEERING_DECISION{"High delivery,<br/>migration, integration or<br/>maintainability complexity?"}

        QA_DECISION{"Complex acceptance,<br/>AI evaluation, safety or<br/>reliability requirements?"}

        SELECT_MARKET["Select Market Analyst"]
        SKIP_MARKET["Skip Market Analyst"]

        SELECT_AI["Select AI Architect"]
        SKIP_AI["Skip AI Architect"]

        SELECT_SECURITY["Select Security Architect"]
        SKIP_SECURITY["Skip Security Architect"]

        SELECT_ENGINEERING["Select Engineering Lead"]
        SKIP_ENGINEERING["Skip Engineering Lead"]

        SELECT_QA["Select QA and Evaluation Architect"]
        SKIP_QA["Skip QA and Evaluation Architect"]

        PLAN_VALIDATE{"Specialist plan valid?"}

        PLAN_REPAIR["Repair specialist plan<br/><br/>
        Maximum: 1 attempt"]

        PLAN_REPAIR_VALID{"Repair successful?"}

        FALLBACK_PLAN["Use safe fallback plan<br/><br/>
        Product Manager<br/>
        Business Analyst<br/>
        Solution Architect<br/>
        Security Architect<br/>
        Lead Reviewer"]

        COST_PRECHECK{"Estimated execution within<br/>session cost/token budget?"}

        REDUCE_PLAN["Reduce optional specialists<br/>and research depth<br/><br/>
        Preserve:<br/>
        • Product analysis<br/>
        • Solution architecture<br/>
        • Security review<br/>
        • Final review"]

        EXECUTION_PLAN["Persist Specialist Execution Plan<br/><br/>
        • Selected specialists<br/>
        • Skipped specialists<br/>
        • Selection reasons<br/>
        • Parallel execution groups<br/>
        • Estimated cost"]
    end

    SPECIALIST_PLANNING --> ALWAYS_SELECTED

    ALWAYS_SELECTED --> MARKET_DECISION
    MARKET_DECISION -- Yes --> SELECT_MARKET
    MARKET_DECISION -- No --> SKIP_MARKET

    SELECT_MARKET --> AI_DECISION
    SKIP_MARKET --> AI_DECISION

    AI_DECISION -- Yes --> SELECT_AI
    AI_DECISION -- No --> SKIP_AI

    SELECT_AI --> SECURITY_DECISION
    SKIP_AI --> SECURITY_DECISION

    SECURITY_DECISION -- Yes --> SELECT_SECURITY
    SECURITY_DECISION -- No --> SKIP_SECURITY

    SELECT_SECURITY --> ENGINEERING_DECISION
    SKIP_SECURITY --> ENGINEERING_DECISION

    ENGINEERING_DECISION -- Yes --> SELECT_ENGINEERING
    ENGINEERING_DECISION -- No --> SKIP_ENGINEERING

    SELECT_ENGINEERING --> QA_DECISION
    SKIP_ENGINEERING --> QA_DECISION

    QA_DECISION -- Yes --> SELECT_QA
    QA_DECISION -- No --> SKIP_QA

    SELECT_QA --> PLAN_VALIDATE
    SKIP_QA --> PLAN_VALIDATE

    PLAN_VALIDATE -- No --> PLAN_REPAIR
    PLAN_REPAIR --> PLAN_REPAIR_VALID
    PLAN_REPAIR_VALID -- No --> FALLBACK_PLAN
    PLAN_REPAIR_VALID -- Yes --> COST_PRECHECK
    FALLBACK_PLAN --> COST_PRECHECK
    PLAN_VALIDATE -- Yes --> COST_PRECHECK

    COST_PRECHECK -- No --> REDUCE_PLAN
    REDUCE_PLAN --> EXECUTION_PLAN
    COST_PRECHECK -- Yes --> EXECUTION_PLAN

    %% =========================================================
    %% PRODUCT AND REQUIREMENTS CREW
    %% =========================================================

    subgraph PRODUCT_CREW["Stage 3 — Product and Requirements Crew"]

        PRODUCT_MANAGER["Product Manager<br/><br/>
        • Product vision<br/>
        • Value proposition<br/>
        • Target users<br/>
        • Personas<br/>
        • MVP scope<br/>
        • Future scope<br/>
        • Priorities<br/>
        • Success metrics"]

        BUSINESS_ANALYST["Business Analyst<br/><br/>
        • User journeys<br/>
        • Functional requirements<br/>
        • Non-functional requirements<br/>
        • Business rules<br/>
        • User stories<br/>
        • Acceptance criteria<br/>
        • Edge cases<br/>
        • Integration requirements"]

        PRODUCT_AGGREGATE["Aggregate Product Outputs"]

        PRODUCT_VALIDATE{"Product output valid<br/>and internally consistent?"}

        PRODUCT_REPAIR["Targeted Product Crew repair<br/><br/>
        Maximum: 1 attempt"]

        PRODUCT_REPAIR_VALID{"Repair successful?"}

        PRODUCT_PARTIAL["Continue with partial product output<br/><br/>
        Record missing or invalid sections"]

        PRODUCT_READY["Validated Product Definition"]
    end

    EXECUTION_PLAN --> PRODUCT_MANAGER
    EXECUTION_PLAN --> BUSINESS_ANALYST

    PRODUCT_MANAGER --> PRODUCT_AGGREGATE
    BUSINESS_ANALYST --> PRODUCT_AGGREGATE

    PRODUCT_AGGREGATE --> PRODUCT_VALIDATE

    PRODUCT_VALIDATE -- No --> PRODUCT_REPAIR
    PRODUCT_REPAIR --> PRODUCT_REPAIR_VALID
    PRODUCT_REPAIR_VALID -- No --> PRODUCT_PARTIAL
    PRODUCT_REPAIR_VALID -- Yes --> PRODUCT_READY
    PRODUCT_VALIDATE -- Yes --> PRODUCT_READY
    PRODUCT_PARTIAL --> PRODUCT_READY

    %% =========================================================
    %% TECHNICAL SPECIALIST CREW
    %% =========================================================

    subgraph TECHNICAL_CREW["Stage 4 — Technical Specialist Crew"]

        SOLUTION_ARCHITECT["Solution Architect<br/><br/>
        • System architecture<br/>
        • Components<br/>
        • APIs<br/>
        • Data flow<br/>
        • Integration design<br/>
        • Reliability<br/>
        • Deployment architecture"]

        MARKET_SELECTED{"Market Analyst selected?"}
        MARKET_ANALYST["Market Analyst<br/><br/>
        • Current market context<br/>
        • Competitors<br/>
        • Trends<br/>
        • Positioning<br/>
        • Differentiation<br/>
        • Market risks"]

        AI_SELECTED{"AI Architect selected?"}
        AI_ARCHITECT["AI Architect<br/><br/>
        • AI suitability<br/>
        • Model strategy<br/>
        • RAG or agent design<br/>
        • Prompt strategy<br/>
        • Tool strategy<br/>
        • AI fallback design<br/>
        • AI cost controls"]

        SECURITY_SELECTED{"Security Architect selected?"}
        SECURITY_ARCHITECT["Security Architect<br/><br/>
        • Threat model<br/>
        • Data protection<br/>
        • Privacy<br/>
        • Prompt injection controls<br/>
        • Tool security<br/>
        • Abuse prevention<br/>
        • AI security"]

        ENGINEERING_SELECTED{"Engineering Lead selected?"}
        ENGINEERING_LEAD["Engineering Lead<br/><br/>
        • Delivery feasibility<br/>
        • Dependencies<br/>
        • Team skills<br/>
        • Maintainability<br/>
        • Technical debt<br/>
        • Implementation phases"]

        QA_SELECTED{"QA Architect selected?"}
        QA_ARCHITECT["QA and Evaluation Architect<br/><br/>
        • Test strategy<br/>
        • AI evaluation<br/>
        • Quality metrics<br/>
        • Failure testing<br/>
        • Security testing<br/>
        • Acceptance plan"]

        MARKET_SKIP_NODE["Market analysis skipped"]
        AI_SKIP_NODE["AI architecture skipped"]
        SECURITY_SKIP_NODE["Security covered by<br/>Solution Architect baseline"]
        ENGINEERING_SKIP_NODE["Engineering review skipped"]
        QA_SKIP_NODE["QA covered by<br/>baseline test strategy"]

        TOOL_POLICY["Controlled Tool Layer<br/><br/>
        • Agent-specific allowlists<br/>
        • Typed inputs<br/>
        • Domain restrictions<br/>
        • Timeouts<br/>
        • Retry limits<br/>
        • Result limits<br/>
        • Output sanitization<br/>
        • Tool-call logging"]

        TOOL_REQUIRED{"Selected specialist<br/>requires external tool?"}

        TOOL_EXECUTE["Execute approved tool"]

        TOOL_SUCCESS{"Tool call successful?"}

        TOOL_RETRY_ALLOWED{"Retry allowed?"}

        TOOL_RETRY["Retry tool with backoff"]

        TOOL_FALLBACK["Continue without tool result<br/><br/>
        Mark analysis as limited"]

        TOOL_OUTPUT_GUARDRAIL{"Tool output passed<br/>security and injection checks?"}

        TOOL_REJECT["Discard unsafe tool output<br/><br/>
        Continue with limited evidence"]

        SPECIALIST_EXECUTE["Execute Specialist Analysis"]

        SPECIALIST_OUTPUT_VALIDATE{"Specialist output valid?"}

        SPECIALIST_REPAIR["Targeted structured output repair<br/><br/>
        Maximum: 1 attempt"]

        SPECIALIST_REPAIR_VALID{"Repair successful?"}

        SPECIALIST_PARTIAL["Mark specialist output partial<br/><br/>
        Record failure reason"]

        SPECIALIST_COMPLETE["Store specialist result"]

        AGGREGATE_SPECIALISTS["Aggregate all available<br/>specialist outputs"]
    end

    PRODUCT_READY --> SOLUTION_ARCHITECT

    PRODUCT_READY --> MARKET_SELECTED
    MARKET_SELECTED -- Yes --> MARKET_ANALYST
    MARKET_SELECTED -- No --> MARKET_SKIP_NODE

    PRODUCT_READY --> AI_SELECTED
    AI_SELECTED -- Yes --> AI_ARCHITECT
    AI_SELECTED -- No --> AI_SKIP_NODE

    PRODUCT_READY --> SECURITY_SELECTED
    SECURITY_SELECTED -- Yes --> SECURITY_ARCHITECT
    SECURITY_SELECTED -- No --> SECURITY_SKIP_NODE

    PRODUCT_READY --> ENGINEERING_SELECTED
    ENGINEERING_SELECTED -- Yes --> ENGINEERING_LEAD
    ENGINEERING_SELECTED -- No --> ENGINEERING_SKIP_NODE

    PRODUCT_READY --> QA_SELECTED
    QA_SELECTED -- Yes --> QA_ARCHITECT
    QA_SELECTED -- No --> QA_SKIP_NODE

    SOLUTION_ARCHITECT --> TOOL_REQUIRED
    MARKET_ANALYST --> TOOL_REQUIRED
    AI_ARCHITECT --> TOOL_REQUIRED
    SECURITY_ARCHITECT --> TOOL_REQUIRED
    ENGINEERING_LEAD --> TOOL_REQUIRED
    QA_ARCHITECT --> TOOL_REQUIRED

    TOOL_REQUIRED -- Yes --> TOOL_POLICY
    TOOL_POLICY --> TOOL_EXECUTE
    TOOL_EXECUTE --> TOOL_SUCCESS

    TOOL_SUCCESS -- No --> TOOL_RETRY_ALLOWED
    TOOL_RETRY_ALLOWED -- Yes --> TOOL_RETRY
    TOOL_RETRY --> TOOL_EXECUTE
    TOOL_RETRY_ALLOWED -- No --> TOOL_FALLBACK

    TOOL_SUCCESS -- Yes --> TOOL_OUTPUT_GUARDRAIL
    TOOL_OUTPUT_GUARDRAIL -- No --> TOOL_REJECT
    TOOL_OUTPUT_GUARDRAIL -- Yes --> SPECIALIST_EXECUTE

    TOOL_FALLBACK --> SPECIALIST_EXECUTE
    TOOL_REJECT --> SPECIALIST_EXECUTE
    TOOL_REQUIRED -- No --> SPECIALIST_EXECUTE

    SPECIALIST_EXECUTE --> SPECIALIST_OUTPUT_VALIDATE

    SPECIALIST_OUTPUT_VALIDATE -- No --> SPECIALIST_REPAIR
    SPECIALIST_REPAIR --> SPECIALIST_REPAIR_VALID
    SPECIALIST_REPAIR_VALID -- No --> SPECIALIST_PARTIAL
    SPECIALIST_REPAIR_VALID -- Yes --> SPECIALIST_COMPLETE
    SPECIALIST_OUTPUT_VALIDATE -- Yes --> SPECIALIST_COMPLETE

    SPECIALIST_PARTIAL --> AGGREGATE_SPECIALISTS
    SPECIALIST_COMPLETE --> AGGREGATE_SPECIALISTS

    MARKET_SKIP_NODE --> AGGREGATE_SPECIALISTS
    AI_SKIP_NODE --> AGGREGATE_SPECIALISTS
    SECURITY_SKIP_NODE --> AGGREGATE_SPECIALISTS
    ENGINEERING_SKIP_NODE --> AGGREGATE_SPECIALISTS
    QA_SKIP_NODE --> AGGREGATE_SPECIALISTS

    %% =========================================================
    %% COST AND EXECUTION CONTROL
    %% =========================================================

    subgraph CONTROL["Cross-Cutting Execution Controls"]

        USAGE_TRACKER["Usage and Cost Tracker<br/><br/>
        • Input tokens<br/>
        • Output tokens<br/>
        • Agent runs<br/>
        • Tool calls<br/>
        • Retry count<br/>
        • Estimated cost<br/>
        • Execution duration"]

        BUDGET_CHECK{"Session budget exceeded?"}

        BUDGET_STOP["Stop optional work<br/><br/>
        Preserve final review and reporting"]

        RATE_CHECK{"Provider rate limit hit?"}

        BACKOFF["Bounded exponential backoff"]

        RETRY_EXHAUSTED{"Retry limit exhausted?"}

        PARTIAL_CONTINUE["Continue with partial results"]

        TRACE["CrewAI Tracing<br/><br/>
        • Flow stages<br/>
        • Routing decisions<br/>
        • Agent runs<br/>
        • Task execution<br/>
        • Tool calls<br/>
        • Human feedback<br/>
        • Errors and latency"]

        LOGGING["Structured Application Logs<br/><br/>
        • Request ID<br/>
        • Session ID<br/>
        • Flow ID<br/>
        • Agent and task<br/>
        • Status<br/>
        • Duration<br/>
        • Error code"]
    end

    API -.-> TRACE
    API -.-> LOGGING
    DISCOVERY_AGENT -.-> USAGE_TRACKER
    PRODUCT_MANAGER -.-> USAGE_TRACKER
    BUSINESS_ANALYST -.-> USAGE_TRACKER
    SOLUTION_ARCHITECT -.-> USAGE_TRACKER
    MARKET_ANALYST -.-> USAGE_TRACKER
    AI_ARCHITECT -.-> USAGE_TRACKER
    SECURITY_ARCHITECT -.-> USAGE_TRACKER
    ENGINEERING_LEAD -.-> USAGE_TRACKER
    QA_ARCHITECT -.-> USAGE_TRACKER
    TOOL_EXECUTE -.-> USAGE_TRACKER

    USAGE_TRACKER --> BUDGET_CHECK
    BUDGET_CHECK -- Yes --> BUDGET_STOP
    BUDGET_CHECK -- No --> AGGREGATE_SPECIALISTS
    BUDGET_STOP --> AGGREGATE_SPECIALISTS

    RATE_CHECK -- Yes --> BACKOFF
    BACKOFF --> RETRY_EXHAUSTED
    RETRY_EXHAUSTED -- Yes --> PARTIAL_CONTINUE
    RETRY_EXHAUSTED -- No --> RATE_CHECK
    PARTIAL_CONTINUE --> AGGREGATE_SPECIALISTS

    %% =========================================================
    %% REVIEW AND REFINEMENT
    %% =========================================================

    subgraph REVIEW["Stage 5 — Review and Reflection"]

        LEAD_REVIEWER["Lead Reviewer<br/><br/>
        Review:<br/>
        • Requirement coverage<br/>
        • Architecture alignment<br/>
        • Contradictions<br/>
        • Unsupported assumptions<br/>
        • Overengineering<br/>
        • AI suitability<br/>
        • AI evaluation<br/>
        • Security gaps<br/>
        • Cost gaps<br/>
        • Market gaps<br/>
        • Delivery feasibility"]

        REVIEW_VALIDATE{"Reviewer output valid?"}

        REVIEW_REPAIR["Repair reviewer output<br/><br/>
        Maximum: 1 attempt"]

        REVIEW_REPAIR_VALID{"Repair successful?"}

        REVIEW_FALLBACK["Use deterministic review checks<br/><br/>
        Mark AI review as incomplete"]

        REVIEW_DECISION{"Blueprint approved?"}

        CRITICAL_MISSING_INFO{"Critical issue requires<br/>new human clarification?"}

        REFINEMENT_LIMIT{"Refinement count<br/>already reached 1?"}

        CREATE_REFINEMENT["Create targeted refinement plan<br/><br/>
        • Specific issue<br/>
        • Responsible specialist<br/>
        • Required correction<br/>
        • No full crew restart"]

        TARGET_SPECIALIST["Re-run selected specialist only"]

        UPDATE_OUTPUTS["Update specialist output<br/><br/>
        Refinement count + 1"]

        FINAL_REVIEW["Final bounded re-review"]

        APPROVED["Blueprint approved"]

        APPROVED_WITH_LIMITATIONS["Approve with documented<br/>limitations and unresolved risks"]
    end

    AGGREGATE_SPECIALISTS --> LEAD_REVIEWER
    LEAD_REVIEWER --> REVIEW_VALIDATE

    REVIEW_VALIDATE -- No --> REVIEW_REPAIR
    REVIEW_REPAIR --> REVIEW_REPAIR_VALID
    REVIEW_REPAIR_VALID -- No --> REVIEW_FALLBACK
    REVIEW_REPAIR_VALID -- Yes --> REVIEW_DECISION
    REVIEW_FALLBACK --> REVIEW_DECISION
    REVIEW_VALIDATE -- Yes --> REVIEW_DECISION

    REVIEW_DECISION -- Yes --> APPROVED
    REVIEW_DECISION -- No --> CRITICAL_MISSING_INFO

    CRITICAL_MISSING_INFO -- Yes --> ROUND_LIMIT
    CRITICAL_MISSING_INFO -- No --> REFINEMENT_LIMIT

    REFINEMENT_LIMIT -- Yes --> APPROVED_WITH_LIMITATIONS
    REFINEMENT_LIMIT -- No --> CREATE_REFINEMENT
    CREATE_REFINEMENT --> TARGET_SPECIALIST
    TARGET_SPECIALIST --> SPECIALIST_OUTPUT_VALIDATE
    SPECIALIST_COMPLETE --> UPDATE_OUTPUTS
    SPECIALIST_PARTIAL --> UPDATE_OUTPUTS
    UPDATE_OUTPUTS --> FINAL_REVIEW
    FINAL_REVIEW --> REVIEW_DECISION

    %% =========================================================
    %% BLUEPRINT GENERATION
    %% =========================================================

    subgraph REPORT["Stage 6 — Product Blueprint Generation"]

        BLUEPRINT_GENERATOR["Blueprint Generator<br/><br/>
        Produce build-ready artifact covering:<br/>
        • Executive summary<br/>
        • Problem and users<br/>
        • Market context<br/>
        • Product vision<br/>
        • MVP and future scope<br/>
        • Requirements<br/>
        • Architecture<br/>
        • Data design<br/>
        • AI design<br/>
        • Security<br/>
        • Testing and evaluation<br/>
        • Deployment<br/>
        • Observability<br/>
        • Cost considerations<br/>
        • Risks and trade-offs<br/>
        • Delivery roadmap"]

        BLUEPRINT_VALIDATE{"Final blueprint valid?"}

        BLUEPRINT_REPAIR["Targeted final blueprint repair<br/><br/>
        Maximum: 1 attempt"]

        BLUEPRINT_REPAIR_VALID{"Repair successful?"}

        FINAL_PARTIAL["Generate partial blueprint<br/><br/>
        Include explicit limitations"]

        SERIALIZE["Serialize Outputs<br/><br/>
        • Structured JSON blueprint<br/>
        • Markdown report<br/>
        • Usage summary<br/>
        • Trace ID<br/>
        • Warnings and limitations"]

        PERSIST_FINAL["Persist Final Session State<br/><br/>
        Status: COMPLETED or PARTIAL"]

        RETURN_FINAL["Return build-ready Product Blueprint<br/>to frontend"]
    end

    APPROVED --> BLUEPRINT_GENERATOR
    APPROVED_WITH_LIMITATIONS --> BLUEPRINT_GENERATOR

    BLUEPRINT_GENERATOR --> BLUEPRINT_VALIDATE

    BLUEPRINT_VALIDATE -- No --> BLUEPRINT_REPAIR
    BLUEPRINT_REPAIR --> BLUEPRINT_REPAIR_VALID
    BLUEPRINT_REPAIR_VALID -- No --> FINAL_PARTIAL
    BLUEPRINT_REPAIR_VALID -- Yes --> SERIALIZE
    BLUEPRINT_VALIDATE -- Yes --> SERIALIZE
    FINAL_PARTIAL --> SERIALIZE

    SERIALIZE --> PERSIST_FINAL
    PERSIST_FINAL --> RETURN_FINAL

    %% =========================================================
    %% PERSISTENCE, OBSERVABILITY AND DEPLOYMENT
    %% =========================================================

    subgraph INFRA["Infrastructure and Operational Components"]

        DATABASE[("SQLite / PostgreSQL<br/><br/>
        • Sessions<br/>
        • Flow state<br/>
        • Questions<br/>
        • Answers<br/>
        • Specialist plans<br/>
        • Specialist outputs<br/>
        • Review findings<br/>
        • Final blueprints<br/>
        • Usage summaries<br/>
        • Errors")]

        HEALTH["Operational Endpoints<br/><br/>
        GET /health<br/>
        GET /ready<br/>
        GET /metrics/summary"]

        DOCKER["Docker Runtime<br/><br/>
        • Multi-stage build<br/>
        • Non-root user<br/>
        • Health check<br/>
        • Production ASGI server<br/>
        • Environment configuration"]

        CI["GitHub Actions<br/><br/>
        • Ruff<br/>
        • Formatting<br/>
        • Mypy<br/>
        • Pytest<br/>
        • Coverage<br/>
        • Security scan<br/>
        • Docker build<br/>
        • Container smoke test"]
    end

    SESSION -.-> DATABASE
    SAVE_CHECKPOINT -.-> DATABASE
    UPDATE_STATE -.-> DATABASE
    EXECUTION_PLAN -.-> DATABASE
    PRODUCT_READY -.-> DATABASE
    SPECIALIST_COMPLETE -.-> DATABASE
    SPECIALIST_PARTIAL -.-> DATABASE
    PERSIST_FINAL -.-> DATABASE

    API -.-> HEALTH
    HEALTH -.-> DOCKER
    CI -.-> DOCKER
```
