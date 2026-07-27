"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type Question = {
  id: string;
  category: string;
  question: string;
  question_type: "free_text" | "single_choice" | "multiple_choice" | "boolean" | "integer" | "decimal";
  rationale: string;
  required: boolean;
  options: string[];
  placeholder?: string | null;
  help_text?: string | null;
};

type Consultation = {
  consultation_id: string;
  status: string;
  stage: string;
  clarification_round: number;
  questions: Question[];
};

type BlueprintSection = {
  section: string;
  title: string;
  summary: string;
  markdown: string;
};

type Blueprint = {
  title: string;
  executive_summary: string;
  sections: BlueprintSection[];
  open_questions: string[];
  limitations: string[];
  generated_markdown: string;
  version: string;
};

const defaultApi = process.env.NEXT_PUBLIC_BUILDWISE_API_URL || "http://localhost:8080/api/v1";

const stages = [
  "intake",
  "discovery",
  "product_definition",
  "requirements",
  "specialist_planning",
  "specialist_execution",
  "lead_review",
  "blueprint_assembly",
  "completed",
];

const stageLabels: Record<string, string> = {
  intake: "Intake",
  discovery: "Discovery",
  clarification: "Clarification",
  product_definition: "Product",
  requirements: "Requirements",
  specialist_planning: "Planning",
  specialist_execution: "Architecture",
  lead_review: "Lead review",
  blueprint_assembly: "Blueprint",
  completed: "Complete",
  failed: "Failed",
};

function splitList(value: string) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function pretty(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function Home() {
  const [apiBase, setApiBase] = useState(defaultApi);
  const [showSettings, setShowSettings] = useState(false);
  const [consultation, setConsultation] = useState<Consultation | null>(null);
  const [blueprint, setBlueprint] = useState<Blueprint | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [answers, setAnswers] = useState<Record<string, string | string[] | boolean>>({});
  const [activeSection, setActiveSection] = useState("");
  const [idea, setIdea] = useState({
    title: "",
    idea: "",
    targetUsers: "",
    features: "",
    platform: "web",
    delivery: "mvp",
    timeline: "",
    budget: "",
    ai: "unknown",
    sensitive: "unknown",
  });

  useEffect(() => {
    const savedApi = localStorage.getItem("buildwise-api");
    const savedId = localStorage.getItem("buildwise-consultation");
    const restore = window.setTimeout(() => {
      if (savedApi) setApiBase(savedApi);
      if (savedId) void loadConsultation(savedId, savedApi || defaultApi);
    }, 0);
    return () => window.clearTimeout(restore);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!consultation || ["completed", "completed_with_limitations", "failed", "awaiting_user_input"].includes(consultation.status)) return;
    const timer = window.setInterval(() => void loadConsultation(consultation.consultation_id), 4000);
    return () => window.clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [consultation?.consultation_id, consultation?.status]);

  const progress = useMemo(() => {
    if (!consultation) return 0;
    if (consultation.stage === "clarification") return 18;
    const index = stages.indexOf(consultation.stage);
    return index < 0 ? 10 : Math.round((index / (stages.length - 1)) * 100);
  }, [consultation]);

  async function request<T>(path: string, options?: RequestInit, base = apiBase): Promise<T> {
    const response = await fetch(`${base.replace(/\/$/, "")}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...options?.headers },
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => null);
      throw new Error(payload?.detail || `Request failed (${response.status})`);
    }
    return response.json() as Promise<T>;
  }

  async function loadConsultation(id: string, base = apiBase) {
    try {
      setError("");
      const current = await request<Consultation>(`/consultations/${id}`, undefined, base);
      setConsultation(current);
      if (["completed", "completed_with_limitations"].includes(current.status)) {
        const result = await request<{ result: Blueprint }>(`/consultations/${id}/result`, undefined, base);
        setBlueprint(result.result);
        setActiveSection(result.result.sections[0]?.section || "");
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load the consultation.");
      if ((caught as Error).message.toLowerCase().includes("not found")) {
        localStorage.removeItem("buildwise-consultation");
      }
    }
  }

  async function startConsultation(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const result = await request<Consultation>("/consultations", {
        method: "POST",
        body: JSON.stringify({
          title: idea.title || null,
          idea: idea.idea,
          target_users: splitList(idea.targetUsers),
          known_features: splitList(idea.features),
          target_platforms: idea.platform === "not_decided" ? [] : [idea.platform],
          delivery_expectation: idea.delivery,
          preferred_timeline: idea.timeline || null,
          estimated_budget: idea.budget || null,
          requests_ai_capabilities: idea.ai === "unknown" ? null : idea.ai === "yes",
          handles_sensitive_data: idea.sensitive === "unknown" ? null : idea.sensitive === "yes",
          submission_channel: "web",
        }),
      });
      localStorage.setItem("buildwise-consultation", result.consultation_id);
      setConsultation(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to start the consultation.");
    } finally {
      setBusy(false);
    }
  }

  async function submitAnswers(event: FormEvent) {
    event.preventDefault();
    if (!consultation) return;
    setBusy(true);
    setError("");
    try {
      const result = await request<Consultation>(
        `/consultations/${consultation.consultation_id}/clarifications`,
        {
          method: "POST",
          body: JSON.stringify({
            clarification_round: consultation.clarification_round,
            answers: consultation.questions.map((question) => ({
              question_id: question.id,
              answer: answers[question.id],
            })),
          }),
        },
      );
      setConsultation(result);
      setAnswers({});
      if (["completed", "completed_with_limitations"].includes(result.status)) {
        await loadConsultation(result.consultation_id);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to submit your answers.");
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    localStorage.removeItem("buildwise-consultation");
    setConsultation(null);
    setBlueprint(null);
    setAnswers({});
    setError("");
  }

  function saveApi() {
    localStorage.setItem("buildwise-api", apiBase.replace(/\/$/, ""));
    setApiBase(apiBase.replace(/\/$/, ""));
    setShowSettings(false);
  }

  function downloadMarkdown() {
    if (!blueprint) return;
    const url = URL.createObjectURL(new Blob([blueprint.generated_markdown], { type: "text/markdown" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "blueprint.md";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <button className="brand" onClick={reset} aria-label="BuildWise home">
          <span className="brand-mark">W</span>
          <span>BuildWise</span>
        </button>
        <div className="topbar-right">
          <span className="api-status"><i /> API connected</span>
          <button className="icon-button" onClick={() => setShowSettings(!showSettings)} aria-label="API settings">⚙</button>
          {consultation && <button className="ghost-button" onClick={reset}>New consultation</button>}
        </div>
        {showSettings && (
          <div className="settings-popover">
            <label htmlFor="api-url">BuildWise API URL</label>
            <input id="api-url" value={apiBase} onChange={(event) => setApiBase(event.target.value)} />
            <button className="primary small" onClick={saveApi}>Save connection</button>
          </div>
        )}
      </header>

      {!consultation && (
        <section className="intake-layout">
          <div className="intro-panel">
            <span className="eyebrow">AI product planning studio</span>
            <h1>Turn an idea into a blueprint your team can build.</h1>
            <p className="lede">Describe the product you have in mind. BuildWise coordinates product, market, architecture, security, AI, and quality specialists into one reviewed plan.</p>
            <div className="promise-grid">
              <div><b>01</b><span>Clarify the product</span></div>
              <div><b>02</b><span>Select the right specialists</span></div>
              <div><b>03</b><span>Deliver a build-ready blueprint</span></div>
            </div>
            <blockquote>“Good products start with sharp questions, not premature answers.”</blockquote>
          </div>

          <form className="intake-card" onSubmit={startConsultation}>
            <div className="form-heading">
              <div><span className="step-label">New consultation</span><h2>What are you building?</h2></div>
              <span className="time-chip">~ 8 min setup</span>
            </div>
            <label>Product name <span>optional</span>
              <input value={idea.title} onChange={(event) => setIdea({ ...idea, title: event.target.value })} placeholder="e.g. Atlas for field teams" />
            </label>
            <label>Describe your idea
              <textarea required minLength={20} value={idea.idea} onChange={(event) => setIdea({ ...idea, idea: event.target.value })} placeholder="What problem does it solve, for whom, and what should the first version make possible?" />
              <small>{idea.idea.length}/20,000</small>
            </label>
            <div className="two-col">
              <label>Target users <span>comma-separated</span>
                <input value={idea.targetUsers} onChange={(event) => setIdea({ ...idea, targetUsers: event.target.value })} placeholder="Operations leads, field staff" />
              </label>
              <label>Known features <span>comma-separated</span>
                <input value={idea.features} onChange={(event) => setIdea({ ...idea, features: event.target.value })} placeholder="Scheduling, alerts, analytics" />
              </label>
              <label>Primary platform
                <select value={idea.platform} onChange={(event) => setIdea({ ...idea, platform: event.target.value })}>
                  <option value="web">Web application</option><option value="mobile">Mobile</option><option value="api">API</option><option value="internal_tool">Internal tool</option><option value="multi_platform">Multi-platform</option><option value="not_decided">Not decided</option>
                </select>
              </label>
              <label>Delivery target
                <select value={idea.delivery} onChange={(event) => setIdea({ ...idea, delivery: event.target.value })}>
                  <option value="prototype">Prototype</option><option value="mvp">MVP</option><option value="production_v1">Production v1</option><option value="modernization">Modernization</option><option value="not_decided">Not decided</option>
                </select>
              </label>
              <label>Preferred timeline <span>optional</span>
                <input value={idea.timeline} onChange={(event) => setIdea({ ...idea, timeline: event.target.value })} placeholder="e.g. 12 weeks" />
              </label>
              <label>Estimated budget <span>optional</span>
                <input value={idea.budget} onChange={(event) => setIdea({ ...idea, budget: event.target.value })} placeholder="e.g. $40k–$60k" />
              </label>
              <label>AI capabilities
                <select value={idea.ai} onChange={(event) => setIdea({ ...idea, ai: event.target.value })}><option value="unknown">Not sure yet</option><option value="yes">Yes</option><option value="no">No</option></select>
              </label>
              <label>Sensitive data
                <select value={idea.sensitive} onChange={(event) => setIdea({ ...idea, sensitive: event.target.value })}><option value="unknown">Not sure yet</option><option value="yes">Yes</option><option value="no">No</option></select>
              </label>
            </div>
            {error && <div className="error-banner">{error}</div>}
            <button className="primary submit" disabled={busy || idea.idea.length < 20}>{busy ? "Starting consultation…" : "Build my blueprint"} <span>→</span></button>
            <p className="privacy-note">No account required. Your consultation ID is saved on this device.</p>
          </form>
        </section>
      )}

      {consultation && !blueprint && (
        <section className="workspace">
          <aside className="progress-panel">
            <span className="eyebrow">Consultation in progress</span>
            <h2>{idea.title || "Your product blueprint"}</h2>
            <code>{consultation.consultation_id.slice(0, 12)}</code>
            <div className="progress-track"><span style={{ height: `${Math.max(progress, 7)}%` }} /></div>
            <ol className="stage-list">
              {stages.map((stage) => {
                const stageProgress = stages.indexOf(stage) <= stages.indexOf(consultation.stage);
                const isCurrent = stage === consultation.stage || (consultation.stage === "clarification" && stage === "discovery");
                return <li key={stage} className={`${stageProgress ? "done" : ""} ${isCurrent ? "current" : ""}`}><i>{stageProgress ? "✓" : ""}</i><span>{stageLabels[stage]}</span></li>;
              })}
            </ol>
          </aside>

          <div className="work-panel">
            {consultation.status === "awaiting_user_input" ? (
              <form className="questions-card" onSubmit={submitAnswers}>
                <div className="round-badge">Clarification round {consultation.clarification_round}</div>
                <h1>A few details will sharpen your blueprint.</h1>
                <p>These questions resolve decisions that materially affect scope, architecture, or delivery.</p>
                <div className="questions">
                  {consultation.questions.map((question, index) => (
                    <div className="question" key={question.id}>
                      <div className="question-number">{String(index + 1).padStart(2, "0")}</div>
                      <div className="question-content">
                        <label>{question.question}{question.required && <b>*</b>}</label>
                        <p>{question.help_text || question.rationale}</p>
                        {question.question_type === "single_choice" && (
                          <div className="choice-grid">{question.options.map((option) => <button type="button" className={answers[question.id] === option ? "selected" : ""} key={option} onClick={() => setAnswers({ ...answers, [question.id]: option })}>{option}</button>)}</div>
                        )}
                        {question.question_type === "multiple_choice" && (
                          <div className="choice-grid">{question.options.map((option) => {
                            const selected = (answers[question.id] as string[] || []).includes(option);
                            return <button type="button" className={selected ? "selected" : ""} key={option} onClick={() => setAnswers({ ...answers, [question.id]: selected ? (answers[question.id] as string[]).filter((item) => item !== option) : [...(answers[question.id] as string[] || []), option] })}>{option}</button>;
                          })}</div>
                        )}
                        {question.question_type === "boolean" && (
                          <div className="choice-grid"><button type="button" className={answers[question.id] === true ? "selected" : ""} onClick={() => setAnswers({ ...answers, [question.id]: true })}>Yes</button><button type="button" className={answers[question.id] === false ? "selected" : ""} onClick={() => setAnswers({ ...answers, [question.id]: false })}>No</button></div>
                        )}
                        {!["single_choice", "multiple_choice", "boolean"].includes(question.question_type) && (
                          <input type={question.question_type === "integer" || question.question_type === "decimal" ? "number" : "text"} step={question.question_type === "decimal" ? "any" : undefined} required={question.required} placeholder={question.placeholder || "Type your answer"} value={(answers[question.id] as string) || ""} onChange={(event) => setAnswers({ ...answers, [question.id]: event.target.value })} />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                {error && <div className="error-banner">{error}</div>}
                <button className="primary submit" disabled={busy || consultation.questions.some((question) => question.required && answers[question.id] === undefined)}>{busy ? "Continuing…" : "Continue consultation"} <span>→</span></button>
              </form>
            ) : consultation.status === "failed" ? (
              <div className="state-card"><div className="state-symbol error">!</div><h1>The consultation stopped.</h1><p>{error || "The planning flow could not complete. Start a new consultation or check the API logs."}</p><button className="primary" onClick={reset}>Start again</button></div>
            ) : (
              <div className="state-card"><div className="orbit"><i /><i /><i /><span>W</span></div><span className="eyebrow">Specialists at work</span><h1>{stageLabels[consultation.stage] || pretty(consultation.stage)}</h1><p>BuildWise is coordinating the next planning stage. This page updates automatically.</p><div className="activity-line"><span /> Reviewing structured outputs and dependencies</div></div>
            )}
          </div>
        </section>
      )}

      {blueprint && (
        <section className="blueprint-layout">
          <aside className="blueprint-nav">
            <button className="back-link" onClick={reset}>← New consultation</button>
            <span className="eyebrow">Blueprint v{blueprint.version}</span>
            <h2>{blueprint.title}</h2>
            <nav>{blueprint.sections.map((section, index) => <button key={section.section} className={activeSection === section.section ? "active" : ""} onClick={() => { setActiveSection(section.section); document.getElementById(section.section)?.scrollIntoView({ behavior: "smooth" }); }}><span>{String(index + 1).padStart(2, "0")}</span>{section.title}</button>)}</nav>
          </aside>
          <article className="blueprint-document">
            <div className="document-hero">
              <div><span className="completion-pill">✓ Lead review approved</span><h1>{blueprint.title}</h1><p>{blueprint.executive_summary}</p></div>
              <button className="primary download" onClick={downloadMarkdown}>Download .md ↓</button>
            </div>
            <div className="document-meta"><span>17 structured sections</span><span>{blueprint.open_questions.length} open questions</span><span>{blueprint.limitations.length} limitations</span></div>
            {blueprint.sections.map((section, index) => (
              <section id={section.section} className="document-section" key={section.section}>
                <div className="section-index">{String(index + 1).padStart(2, "0")}</div>
                <div><span className="section-type">{pretty(section.section)}</span><h2>{section.title}</h2><p className="section-summary">{section.summary}</p><MarkdownBody markdown={section.markdown} /></div>
              </section>
            ))}
          </article>
        </section>
      )}
    </main>
  );
}

function MarkdownBody({ markdown }: { markdown: string }) {
  const lines = markdown.split("\n").filter((line) => !line.startsWith("## "));
  return <div className="markdown-body">{lines.map((line, index) => {
    if (line.startsWith("### ")) return <h3 key={index}>{line.slice(4)}</h3>;
    if (line.startsWith("- ")) return <div className="md-bullet" key={index}><i />{line.slice(2).replaceAll("**", "")}</div>;
    if (!line.trim()) return <br key={index} />;
    return <p key={index}>{line.replaceAll("**", "")}</p>;
  })}</div>;
}
