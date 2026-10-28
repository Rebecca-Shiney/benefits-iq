"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { CopilotKitProvider, CopilotChat } from "@copilotkit/react-core/v2";
import { ActivitySchema, api, type Aggregate, type Case, type Field, type Session } from "@/lib/contracts";

const personas = [
  ["reviewer-a", "Clinical reviewer · Employer A"], ["reviewer-b", "Clinical reviewer · Employer B"],
  ["contact-a", "Contact centre · Employer A"], ["employer-a", "Account manager · Employer A"],
  ["employer-b", "Account manager · Employer B"],
];

export default function Workspace() {
  const [session, setSession] = useState<Session | null>(null);
  const [selectedUser, setSelectedUser] = useState("reviewer-a");
  const [cases, setCases] = useState<Case[]>([]);
  const [current, setCurrent] = useState<Case | null>(null);
  const [aggregate, setAggregate] = useState<Aggregate | null>(null);
  const [renewals, setRenewals] = useState<(Case & { draft: string })[]>([]);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");
  const [activities, setActivities] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [fields, setFields] = useState<Record<string, Field>>({});
  const [reason, setReason] = useState("");
  const [outcome, setOutcome] = useState("information_requested");
  const [confirmed, setConfirmed] = useState(false);
  const [draft, setDraft] = useState("");
  const [sendConfirmed, setSendConfirmed] = useState(false);
  const [notice, setNotice] = useState("");
  const [showChat, setShowChat] = useState(false);
  const controller = useRef<AbortController | null>(null);
  const decisionKey = useRef<string | null>(null);

  const openCase = useCallback(async (id: string) => {
    const data = await api<Case>(`cases/${id}`);
    setCurrent(data); setFields(data.member360?.fields || {});
    setDraft(data.missing_information_draft || data.update_draft); setSendConfirmed(false); setConfirmed(false);
    setReason(""); setNotice(""); setActivities([]); setShowChat(false);
    decisionKey.current = null;
  }, []);

  const refresh = useCallback(async (id?: string) => {
    const user = await api<Session>("session");
    setSession(user);
    if (user.role === "employer") {
      setAggregate(await api<Aggregate>(`employers/${user.employer}/aggregate`));
      setCurrent(null); setCases([]); setRenewals([]);
    } else {
      const list = await api<Case[]>("cases");
      setCases(list); setAggregate(null);
      setRenewals(user.role === "reviewer" && user.features.renewal ? await api<(Case & { draft: string })[]>("renewals?window=30") : []);
      if (id || list[0]?.id) await openCase(id || list[0].id);
    }
  }, [openCase]);

  useEffect(() => {
    return () => controller.current?.abort();
  }, []);

  async function login() {
    setError(""); setCurrent(null); setSession(null); setAggregate(null);
    try {
      const response = await fetch("/api/session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ user: selectedUser }) });
      if (!response.ok) throw new Error("Unable to create local demo session.");
      await refresh();
    } catch (e) { setError(String(e)); }
  }

  async function run(intent: "intake" | "evidence" | "status") {
    if (!current) return;
    const id = current.id;
    controller.current = new AbortController();
    setRunning(true); setError(""); setActivities([]); setNotice("");
    let finished = false;
    const seen = new Set<string>();
    const activityLog: string[] = [];
    function logActivity(message: string) {
      activityLog.push(message);
      setActivities([...activityLog]);
    }
    try {
      const response = await fetch(`/api/backend/cases/${id}/run`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ intent, version: current.version }), signal: controller.current.signal,
      });
      if (!response.ok) {
        const body = await response.json();
        throw new Error(`${body.error?.code || "RUN_FAILED"} · ${body.error?.traceId || response.status}`);
      }
      const reader = response.body?.getReader();
      if (!reader) throw new Error("Streaming response unavailable.");
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const chunk = await reader.read();
        if (chunk.done) break;
        buffer += decoder.decode(chunk.value, { stream: true });
        const parts = buffer.split("\n\n"); buffer = parts.pop() || "";
        for (const part of parts) {
          const eventId = part.split("\n").find(x => x.startsWith("id: "))?.slice(4);
          if (eventId && seen.has(eventId)) continue;
          if (eventId) seen.add(eventId);
          const line = part.split("\n").find(x => x.startsWith("data: "));
          if (!line) continue;
          const event: { type: string; stepName?: string; message?: string; value?: unknown } = JSON.parse(line.slice(6));
          if (event.type === "STEP_STARTED") logActivity(`Running ${event.stepName}`);
          if (event.type === "CUSTOM") {
            const parsed = ActivitySchema.safeParse(event.value);
            logActivity(parsed.success && parsed.data.caseId === id
              ? `${parsed.data.activity} · trace ${parsed.data.traceId}`
              : "Unsupported activity received; refresh authoritative state.");
          }
          if (event.type === "RUN_ERROR") throw new Error(event.message || "Workflow error");
          if (event.type === "RUN_FINISHED") finished = true;
          // Streamed snapshots are deliberately not assigned to case state.
        }
      }
      if (!finished) throw new Error("Stream interrupted. Outcome unknown; refresh before retrying.");
      await refresh(id);
      setActivities(activityLog);
      setNotice("Workflow saved. Display refreshed from the authoritative case API.");
    } catch (e) {
      setError(e instanceof Error && e.name === "AbortError"
        ? "Run cancelled or connection interrupted. Refresh to check whether a final atomic save completed."
        : String(e));
    } finally { setRunning(false); controller.current = null; }
  }

  async function saveDecision() {
    if (!current?.brief || !confirmed) return;
    setError(""); setNotice(""); setRunning(true);
    decisionKey.current ||= crypto.randomUUID();
    try {
      await api(`cases/${current.id}/decision`, {
        version: current.version, brief_version: current.brief.version,
        outcome, reason, confirmed, idempotency_key: decisionKey.current,
      });
      await refresh(current.id); setNotice("Your decision was saved with your identity, evidence version and audit history.");
    } catch (e) { setError(String(e)); } finally { setRunning(false); }
  }

  async function verifyForm() {
    if (!current) return;
    setRunning(true); setError("");
    try {
      await api(`cases/${current.id}/form`, { version: current.version, fields });
      await refresh(current.id); setNotice("Human-verified form saved. Previous evidence was invalidated; prepare a new brief.");
    } catch (e) { setError(String(e)); } finally { setRunning(false); }
  }

  async function saveDraft() {
    if (!current || !sendConfirmed) return;
    setRunning(true); setError("");
    try {
      await api(`cases/${current.id}/communication`, { text: draft, confirmed: true });
      await refresh(current.id); setNotice("Confirmed draft stored in the local demo outbox. Nothing was sent externally.");
    } catch (e) { setError(String(e)); } finally { setRunning(false); }
  }

  return <main>
    <header className="topbar"><a className="brand" href="/">B<span>IQ</span><small>BENEFITS IQ</small></a>
      <div className="header-note">BENEFITS OPERATIONS <span>/</span> HUMAN-LED REVIEW</div>
      <span className="pill synthetic">SYNTHETIC DATA ONLY</span>
    </header>
    <div className="hero"><div><p className="eyebrow">CLARITY FOR EVERY CASE</p>
      <h1>Better evidence.<br /><span>Human decisions.</span></h1>
      <p className="subtitle">A governed workspace for special authorization and Member 360.</p></div>
      <section className="session-card" aria-label="Local demo session">
        <label htmlFor="persona">LOCAL DEMO PERSONA</label>
        <select id="persona" value={selectedUser} disabled={running} onChange={e => setSelectedUser(e.target.value)}>
          {personas.map(([id, label]) => <option value={id} key={id}>{label}</option>)}
        </select>
        <button onClick={login} disabled={running}>Open workspace <span aria-hidden>→</span></button>
        <small>Explicit demo identity switcher, not production authentication.</small>
      </section>
    </div>
    <div className="safety-strip"><span className="dot" /><strong>People decide. Agents prepare.</strong>
      <span>No autonomous clinical decisions, real health data or external sends.</span></div>
    {error && <div role="alert" className="error">{error} {current && <button disabled={running} onClick={() => refresh(current.id).catch(e => setError(String(e)))}>Refresh case</button>}</div>}
    {notice && <p role="status" className="notice">{notice}</p>}
    {!session && <section className="welcome card"><p className="eyebrow">YOUR REVIEW DESK, CONNECTED</p><h2>One case. Every relevant source.</h2>
      <p>Choose a synthetic persona to explore intake, cited evidence, human checkpoints and role-safe updates.</p>
      <div className="welcome-grid"><div><b>01</b><h3>Check completeness</h3><p>Uncertain fields stay uncertain.</p></div>
        <div><b>02</b><h3>Prepare evidence</h3><p>Versioned sources, explicit gaps.</p></div><div><b>03</b><h3>Decide with context</h3><p>Your decision. Recorded and traceable.</p></div></div></section>}
    {session && <div className="workspace-meta"><strong>{session.role === "reviewer" ? "Clinical review workspace" : session.role === "contact" ? "Contact centre" : "Employer insights"}</strong>
      <span>{session.id} / {session.employer} / {session.mode === "live" ? "Configured model chat" : "Deterministic synthetic agents"}</span></div>}
    {aggregate && <section className="card"><p className="eyebrow">PORTFOLIO VIEW / AGGREGATES ONLY</p><h2>Specialty utilization trends</h2>
      <p>This separate fictional portfolio is not computed from the five workflow members.</p>
      <div className="trend-grid">{aggregate.rows.map(r => <article className="trend" key={r.period}><h3>{r.period}</h3>
        <strong>{r.members ?? "Suppressed"}</strong><p>covered members</p><p>{r.specialty_utilizers ?? "Suppressed"} specialty utilizers</p>
        <p>{r.cost === null ? "Suppressed" : `$${r.cost.toLocaleString()}`} synthetic cost</p></article>)}</div>
      <p>{aggregate.suppression}</p><small>Source: {aggregate.dataset} · {aggregate.as_of}. No causal conclusions or employee rankings.</small></section>}
    {session && session.role !== "employer" && <div className="workspace">
      <aside className="queue card"><div className="section-heading"><h2>Case queue</h2><span className="count">{cases.length}</span></div>
        <label className="sr-only" htmlFor="filter">Filter cases</label><input id="filter" placeholder="Filter by case or status" value={filter} onChange={e => setFilter(e.target.value)} />
        {cases.filter(c => `${c.id} ${c.state}`.toLowerCase().includes(filter.toLowerCase())).map(c => <button disabled={running} key={c.id}
          className={`case-item ${current?.id === c.id ? "selected" : ""}`} onClick={() => openCase(c.id).catch(e => setError(String(e)))}>
          <strong>{c.id}</strong><span>{c.state.replaceAll("_", " ")}</span><small>Record v{c.version}</small></button>)}
        {renewals.length > 0 && <div className="renewal"><h3>Renewal watch · 30 days</h3>{renewals.map(r => <div key={r.id}><b>{r.id}</b><p>Expires {r.expiry}</p><small>{r.draft}</small></div>)}</div>}
      </aside>
      {current && <div className="case-workspace"><section className="card case-header"><div><p className="eyebrow">SPECIAL AUTHORIZATION</p><h2>{current.id}</h2><p>{current.member360?.name || "Authorized case status"} {current.scenario && `· ${current.scenario}`}</p></div>
        <span className="pill">{current.state.replaceAll("_", " ")}</span><small>Authoritative record v{current.version}</small></section>
        {session.role === "reviewer" && <>
          <section className="card"><div className="section-heading"><h2>Intake & Member 360</h2><button className="secondary" disabled={running || !!current.decision || !session.features.intake} onClick={() => run("intake")}>Run intake</button></div>
            <p>Plan {current.member360?.plan} · Coverage {current.member360?.coverage} · Values below 85% confidence require human verification.</p>
            <div className="form-grid">{Object.entries(fields).map(([name, field]) => <label key={name}>{name.replaceAll("_", " ")}
              <input value={field.value || ""} readOnly={name === "member_id"} disabled={running || !!current.decision}
                onChange={e => setFields(f => ({ ...f, [name]: { ...field, value: e.target.value || null, confidence: 1 } }))} />
              <small className={field.confidence < .85 || !field.value ? "warning-text" : ""}>{Math.round(field.confidence * 100)}% confidence · {field.source}</small>
            </label>)}</div><button className="secondary" disabled={running || !!current.decision} onClick={verifyForm}>Confirm verified form fields</button>
            <details><summary>Prior therapy claims</summary>{current.member360?.claims.map(c => <p key={c.id}>{c.id} · {c.therapy} · {c.date}</p>)}</details>
          </section>
          <section className="card"><div className="section-heading"><div><p className="eyebrow">GROUNDED, NOT DECIDED</p><h2>Criteria evidence matrix</h2></div>
            <button disabled={running || !!current.decision || !session.features.evidence} onClick={() => run("evidence")}>Prepare evidence</button></div>
            {!current.brief ? <p className="empty">Prepare a brief to see versioned citations, gaps and conflicts.</p> : <>
              <p>Brief v{current.brief.version} · Criteria {current.brief.criteria_version || "SOURCE GAP"} · Deterministic synthetic preparation</p>
              <table><thead><tr><th>Criterion</th><th>Evidence state</th><th>Sources & explanation</th></tr></thead><tbody>
                {current.brief.items.map(item => <tr key={item.criterion}><td>{item.criterion}</td><td><span className={`state ${item.state}`}>{item.state}</span></td>
                  <td><p>{item.explanation}</p>{item.sources.map(source => <details key={source.id}><summary>{source.id} / {source.version}</summary>
                    <p>{source.title} · {source.as_of}</p><p>{source.passage}</p></details>)}</td></tr>)}</tbody></table>
              {current.brief.gaps.length > 0 && <p className="warning-text">Gaps: {current.brief.gaps.join("; ")}</p>}
              {current.brief.conflicts.length > 0 && <p className="warning-text">Conflicts: {current.brief.conflicts.join("; ")}</p>}
            </>}
          </section>
          <section className="card decision"><p className="eyebrow">AUTHORIZED HUMAN CHECKPOINT</p><h2>Reviewer decision</h2>
            {current.decision ? <><p><strong>{current.decision.outcome}</strong> · {current.decision.reviewer} · {new Date(current.decision.timestamp).toLocaleString()}</p><p>{current.decision.reason}</p><small>Evidence brief v{current.decision.brief_version}. Saved decisions are immutable in this demo.</small></> : <>
              <p>Evidence states are not clinical outcomes. Review all gaps and conflicts before deciding.</p>
              <label>Outcome<select value={outcome} onChange={e => { setOutcome(e.target.value); decisionKey.current = null; }} disabled={running}>
                <option value="information_requested">Request more information</option><option value="approved">Approve</option><option value="declined">Decline</option></select></label>
              <label>Rationale<textarea value={reason} onChange={e => { setReason(e.target.value); decisionKey.current = null; }} minLength={10} maxLength={1000} disabled={running} /></label>
              <label className="checkbox"><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} disabled={running} />I reviewed the current evidence and am explicitly recording this decision.</label>
              <button disabled={running || !current.brief || !confirmed || reason.trim().length < 10} onClick={saveDecision}>Record my decision</button>
            </>}
          </section>
        </>}
        <section className="card"><p className="eyebrow">PLAIN LANGUAGE / MINIMUM NECESSARY</p><h2>Case status & next step</h2><p>{current.message}</p><p>Next owner: {current.next_owner}. No decision date is promised.</p>
          <label>{current.missing_information_draft ? "Unsaved missing-information draft" : "Unsaved member-update draft"}<textarea value={draft} maxLength={2000} onChange={e => setDraft(e.target.value)} disabled={running} /></label>
          <label className="checkbox"><input type="checkbox" checked={sendConfirmed} onChange={e => setSendConfirmed(e.target.checked)} disabled={running} />Confirm this draft for the local outbox only.</label>
          <button className="secondary" disabled={running || !sendConfirmed || !draft.trim()} onClick={saveDraft}>Confirm local draft (no external send)</button>
        </section>
        <section className="card"><h2>Audit timeline</h2><ol className="timeline">{current.timeline.map(t => <li key={t.id}><b>{t.event.replaceAll("_", " ")}</b>
          <small>{new Date(t.created).toLocaleString()} · trace {t.trace}</small></li>)}</ol></section>
      </div>}
      <aside className="assistant card"><p className="eyebrow">BENEFITS IQ ASSISTANT</p><h2>Your review companion</h2>
        <p>{session.mode === "live" ? "Configured model-backed chat. Capability data remains synthetic." : "Deterministic synthetic agent behind Microsoft Agent Framework + AG-UI. No live AI call."}</p>
        <div className="activity" role="status" aria-live="polite">{running ? <strong>Workflow in progress…</strong> : <strong>Ready for a human-led workflow</strong>}
          {activities.map((a, i) => <p key={`${i}-${a}`}>{a}</p>)}</div>
        {running && <button className="secondary" onClick={() => controller.current?.abort()}>Cancel workflow</button>}
        <p className="small">Interrupted runs are never silently replayed. Refresh the case before retrying; streamed state is provisional.</p>
        {current && session.features.chat && <><button className="secondary" disabled={running} onClick={() => setShowChat(c => !c)}>{showChat ? "Close chat" : "Open case-bound chat"}</button>
          {showChat && <CopilotKitProvider runtimeUrl="/api/copilotkit" useSingleEndpoint={false}
            headers={{ "X-Benefits-Case": current.id }} showDevConsole={false}
            onError={(event) => setError(`Chat unavailable: ${event.code}. Refresh before retrying.`)}>
            <CopilotChat agentId="health_benefits_orchestrator" input={{
              textArea: { "aria-label": "Case-bound chat message" },
              sendButton: { "aria-label": "Send message or stop current response" },
              addMenuButton: { "aria-label": "Attachments unavailable in this demo", disabled: true },
            }} labels={{
              welcomeMessageText: "Ask about intake completeness, criteria evidence or case status. Decisions stay in the reviewer panel.",
              chatDisclaimerText: "Synthetic evidence only. A human must decide.",
            }} />
          </CopilotKitProvider>}</>}
      </aside>
    </div>}
    <footer>BENEFITS IQ <span>Independent October SE Build demo · Synthetic fixtures · No production integrations</span></footer>
  </main>;
}
