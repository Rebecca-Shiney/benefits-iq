"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { CaseChat } from "@/components/case-chat";
import { DashboardTour } from "@/components/dashboard-tour";
import { ActivitySchema, api, type Aggregate, type Case, type CaseOperations, type Field, type Session, type Task, type TaskKind, type Workbench } from "@/lib/contracts";
import { dateTime, Documents, label, Metrics, Overview, TaskPanel } from "@/components/operations";
import { authorizationHeaders, initializeAuth, signIn, signOut } from "@/lib/browser-auth";
import { reasons } from "@/agents/showcase-options.json";

const personas = [
  ["reviewer-a", "Clinical reviewer · Employer A"], ["reviewer-b", "Clinical reviewer · Employer B"],
  ["contact-a", "Contact centre · Employer A"], ["employer-a", "Account manager · Employer A"],
  ["employer-b", "Account manager · Employer B"],
];

export default function Workspace() {
  const [session, setSession] = useState<Session | null>(null);
  const [selectedUser, setSelectedUser] = useState("reviewer-a");
  const [workbench, setWorkbench] = useState<Workbench | null>(null);
  const [operations, setOperations] = useState<CaseOperations | null>(null);
  const [current, setCurrent] = useState<Case | null>(null);
  const [aggregate, setAggregate] = useState<Aggregate | null>(null);
  const [renewals, setRenewals] = useState<(Case & { draft: string })[]>([]);
  const [filter, setFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [ownerFilter, setOwnerFilter] = useState("all");
  const [sort, setSort] = useState("target");
  const [queueLoading, setQueueLoading] = useState(false);
  const [opening, setOpening] = useState(false);
  const [view, setView] = useState("cases");
  const [tab, setTab] = useState("overview");
  const [owner, setOwner] = useState("unassigned");
  const [priority, setPriority] = useState("standard");
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
  const [authProfile, setAuthProfile] = useState<"local" | "starter" | "showcase" | null>(null);
  const controller = useRef<AbortController | null>(null);
  const decisionKey = useRef<string | null>(null);
  const caseRequest = useRef(0);
  const filtersRef = useRef("");
  const loadedQueueQuery = useRef("");
  filtersRef.current = new URLSearchParams({ search: filter, state: statusFilter, priority: priorityFilter, owner: ownerFilter, sort }).toString();

  const openCase = useCallback(async (id: string, resetTab = true) => {
    const request = ++caseRequest.current;
    setOpening(true); setError(""); setShowChat(false);
    try {
      const [data, ops] = await Promise.all([api<Case>(`cases/${id}`), api<CaseOperations>(`cases/${id}/operations`)]);
      if (request !== caseRequest.current) return;
      setCurrent(data); setOperations(ops); setOwner(ops.owner); setPriority(ops.priority);
      setFields(data.member360?.fields || {});
      setDraft(data.missing_information_draft || data.update_draft); setSendConfirmed(false); setConfirmed(false);
      setReason(""); setNotice(""); setActivities([]); setShowChat(false); setView("cases");
      if (resetTab) setTab("overview");
      decisionKey.current = null;
    } finally { if (request === caseRequest.current) setOpening(false); }
  }, []);

  const refresh = useCallback(async (id?: string) => {
    const user = await api<Session>("session");
    const query = filtersRef.current;
    loadedQueueQuery.current = `${user.id}?${query}`;
    setSession(user);
    if (user.role === "employer") {
      setAggregate(await api<Aggregate>(`employers/${user.employer}/aggregate`));
      setCurrent(null); setWorkbench(null); setOperations(null); setRenewals([]);
    } else {
      const data = await api<Workbench>(`workbench?${query}`).catch(error => {
        loadedQueueQuery.current = "";
        throw error;
      });
      setWorkbench(data); setAggregate(null); setQueueLoading(false);
      setRenewals(user.role === "reviewer" && user.features.renewal ? await api<(Case & { draft: string })[]>("renewals?window=30") : []);
      if (id || data.items[0]?.id) await openCase(id || data.items[0].id, false);
    }
  }, [openCase]);

  useEffect(() => {
    if (!session || session.role === "employer") return;
    const query = filtersRef.current;
    const key = `${session.id}?${query}`;
    if (loadedQueueQuery.current === key) { setQueueLoading(false); return; }
    const abort = new AbortController();
    setQueueLoading(true);
    const timer = setTimeout(async () => {
      try {
        const data = await api<Workbench>(`workbench?${query}`, undefined, abort.signal);
        if (!abort.signal.aborted) { loadedQueueQuery.current = key; setWorkbench(data); }
      }
      catch (e) { if (!abort.signal.aborted) { loadedQueueQuery.current = ""; setWorkbench(null); setError(String(e)); } }
      finally { if (!abort.signal.aborted) setQueueLoading(false); }
    }, 250);
    return () => { clearTimeout(timer); abort.abort(); };
  }, [filter, statusFilter, priorityFilter, ownerFilter, sort, session?.id, session?.role]);

  useEffect(() => {
    return () => controller.current?.abort();
  }, []);

  useEffect(() => {
    let active = true;
    initializeAuth().then(({ config }) => {
      if (active) setAuthProfile(config.profile);
    }).catch(() => { if (active) setError("Authentication configuration unavailable. Reload after resolving setup."); });
    return () => { active = false; };
  }, []);

  async function login() {
    ++caseRequest.current;
    setRunning(true); setError(""); setCurrent(null); setSession(null); setAggregate(null); setWorkbench(null); setOperations(null);
    setView("cases"); setTab("overview"); setFilter(""); setStatusFilter("all"); setPriorityFilter("all"); setOwnerFilter("all");
    filtersRef.current = new URLSearchParams({ search: "", state: "all", priority: "all", owner: "all", sort }).toString();
    try {
      if (authProfile === "starter") {
        await signIn();
      } else {
        const response = await fetch("/api/session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ user: selectedUser }) });
        if (!response.ok) throw new Error("Unable to create local demo session.");
      }
      await refresh();
    } catch (e) { setError(String(e)); } finally { setRunning(false); }
  }

  async function logout() {
    setRunning(true); setError(""); setShowChat(false);
    try { await signOut(); }
    catch { setError("Entra sign-out did not finish. Close this tab to discard its in-memory tokens."); }
    finally {
      setSession(null); setCurrent(null); setOperations(null); setWorkbench(null); setAggregate(null);
      setRenewals([]); setFields({}); setDraft(""); setReason(""); setRunning(false);
    }
  }

  async function toggleChat() {
    if (showChat) { setShowChat(false); return; }
    try {
      await authorizationHeaders();
      setShowChat(true);
    } catch { setError("Chat authentication expired or unavailable. Sign in again before retrying."); }
  }

  async function downloadSource() {
    if (!current) return;
    setRunning(true); setError("");
    try {
      const response = await fetch(`/api/backend/cases/${current.id}/document`, {
        headers: await authorizationHeaders(), cache: "no-store",
      });
      if (!response.ok) {
        const body = await response.json();
        throw new Error(body.error?.code || "SOURCE_DOCUMENT_UNAVAILABLE");
      }
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = url; link.download = `${current.id}-synthetic-intake.pdf`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 30_000);
    } catch (e) { setError(String(e)); }
    finally { setRunning(false); }
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
        method: "POST", headers: { "Content-Type": "application/json", ...await authorizationHeaders() },
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

  async function saveRouting() {
    if (!current) return;
    setRunning(true); setError(""); setNotice("");
    try {
      await api(`cases/${current.id}/assignment`, { version: current.version, owner, priority });
      await refresh(current.id); setNotice("Operational routing saved and audited. No clinical outcome changed.");
    } catch (e) { setError(String(e)); } finally { setRunning(false); }
  }

  async function createTask(kind: TaskKind) {
    if (!current) return;
    setRunning(true); setError(""); setNotice("");
    try {
      await api(`cases/${current.id}/tasks`, { kind });
      await refresh(current.id); setNotice("Team handoff saved locally. Nothing was sent externally.");
    } catch (e) { setError(String(e)); } finally { setRunning(false); }
  }

  async function updateTask(task: Task, state: Task["state"]) {
    setRunning(true); setError(""); setNotice("");
    try {
      await api(`cases/${task.case_id}/tasks/${task.id}`, { version: task.version, state });
      await refresh(current?.id); setNotice("Task updated and audited. Clinical status is unchanged.");
    } catch (e) { setError(String(e)); } finally { setRunning(false); }
  }

  function navigateCase(id: string, nextTab = "overview") {
    openCase(id, false).then(() => setTab(nextTab)).catch(e => setError(String(e)));
  }

  async function reload() {
    setRunning(true); setError(""); setNotice("");
    try { await refresh(current?.id); setNotice("Selected view refreshed from the durable case store."); }
    catch (e) { setError(String(e)); } finally { setRunning(false); }
  }

  const busy = running || opening;
  const tabs = session?.role === "reviewer"
    ? ["overview", "intake", "documents", "evidence", "decision", "tasks", "status", "activity"]
    : ["overview", "tasks", "status", "activity"];

  return <main className={session ? "dashboard" : ""}>
    <header className="topbar"><a className="brand" href="/">B<span>IQ</span><small>BENEFITS IQ</small></a>
      <div className="header-note">BENEFITS OPERATIONS <span>/</span> HUMAN-LED REVIEW</div>
      <DashboardTour context={{
        session: session?.id || null, role: session?.role || null, demo: authProfile !== "starter",
        view, tab, caseId: !opening && operations ? current?.id || null : null, busy, ready: authProfile !== null,
        chat: !!session?.features.chat, intake: !!session?.features.intake, evidence: !!session?.features.evidence, renewal: !!session?.features.renewal,
      }} onNavigate={setTab} />
      <span className="pill synthetic">SYNTHETIC DATA ONLY</span>
    </header>
    {authProfile === "showcase" && <section className="safety-strip" aria-label="Public showcase limitations">
      <strong>PUBLIC SYNTHETIC SHOWCASE / NO SIGN-IN</strong>
      <span>Anyone can switch every demo view and perform enabled synthetic actions. Roles are not authenticated access.
        Never enter health or personal data. Shared decisions are anonymous, persistent demo records, not clinical advice or healthcare compliance.</span>
    </section>}
    {!session && <div className="hero"><div><p className="eyebrow">CLARITY FOR EVERY CASE</p>
      <h1>Better evidence.<br /><span>Human decisions.</span></h1>
      <p className="subtitle">A governed workspace for special authorization and Member 360.</p></div>
      <section className="session-card" data-tour="workspace" aria-label={authProfile === "starter" ? "Microsoft Entra sign-in" : "Local demo session"}>
        {authProfile !== null && authProfile !== "starter" && <><label htmlFor="persona">{authProfile === "showcase" ? "PUBLIC DEMO VIEW" : "LOCAL DEMO PERSONA"}</label>
        <select id="persona" value={selectedUser} disabled={running} onChange={e => setSelectedUser(e.target.value)}>
          {personas.map(([id, label]) => <option value={id} key={id}>{label}</option>)}
        </select></>}
        <button onClick={login} disabled={running || !authProfile}>{authProfile === "starter" ? "Sign in with Microsoft Entra" : "Open workspace"} <span aria-hidden>→</span></button>
        <small>{authProfile === "starter" ? "Azure-native synthetic data. Access is assigned by approved role and employer." :
          authProfile === "showcase" ? "No credentials. All demo views are available to everyone; no verified user identity." : "Explicit demo identity switcher, not production authentication."}</small>
      </section>
    </div>}
    {session && <div className="dashboard-heading"><div><p className="eyebrow">BENEFITS OPERATIONS / {workbench?.employer.name || session.employer}</p>
      <h1>{session.role === "reviewer" ? "Review desk" : session.role === "contact" ? "Member support" : "Employer portfolio"}</h1>
      <p>{session.role === "employer" ? "Fictional group-level trends. No employee drill-through." : "A clear view of your workload, evidence and next handoff."}</p></div>
      {authProfile === "starter" ? <div className="persona-switch" data-tour="workspace"><button className="secondary" disabled={busy} onClick={login}>Sign in again</button>
        <button className="secondary" disabled={busy} onClick={logout}>Sign out</button></div> :
      <div className="persona-switch" data-tour="workspace"><label htmlFor="persona">Demo workspace<select id="persona" value={selectedUser} disabled={busy} onChange={e => setSelectedUser(e.target.value)}>
        {personas.map(([id, name]) => <option value={id} key={id}>{name}</option>)}</select></label>
        <button className="secondary" disabled={busy} onClick={login}>Switch workspace</button></div>}
    </div>}
    <div className="safety-strip" data-tour="safety"><span className="dot" /><strong>People decide. Agents prepare.</strong>
      <span>No autonomous clinical decisions, real health data or external sends.</span></div>
    {error && <div role="alert" className="error">{error} {session && <button disabled={busy} onClick={reload}>Refresh case</button>}</div>}
    {notice && <p role="status" className="notice">{notice}</p>}
    {!session && <section className="welcome card" data-tour="welcome"><p className="eyebrow">YOUR REVIEW DESK, CONNECTED</p><h2>One case. Every relevant source.</h2>
      <p>{authProfile === "starter" ? "Sign in to your approved synthetic-data role to explore intake, cited evidence and human checkpoints." : "Choose a synthetic persona to explore intake, cited evidence, human checkpoints and role-safe updates."}</p>
      <div className="welcome-grid"><div><b>01</b><h3>Check completeness</h3><p>Uncertain fields stay uncertain.</p></div>
        <div><b>02</b><h3>Prepare evidence</h3><p>Versioned sources, explicit gaps.</p></div><div><b>03</b><h3>Decide with context</h3><p>Your decision. Recorded and traceable.</p></div></div></section>}
    {session && <div className="workspace-meta"><strong>{session.role === "reviewer" ? "Clinical review workspace" : session.role === "contact" ? "Contact centre" : "Employer insights"}</strong>
      <span>{session.id} / {session.employer} / {session.profile !== "local" && session.profile ? "Azure-native synthetic sources / regional model" : session.mode === "live" ? "Configured model chat" : "Deterministic synthetic agents"}</span></div>}
    {aggregate && <section className="card" data-tour="portfolio"><p className="eyebrow">PORTFOLIO VIEW / AGGREGATES ONLY</p><h2>Specialty utilization trends</h2>
      <p>This separate fictional portfolio is not computed from the individual workflow members.</p>
      <div className="trend-grid">{aggregate.rows.map(r => <article className="trend" key={r.period}><h3>{r.period}</h3>
        <strong>{r.members ?? "Suppressed"}</strong><p>covered members</p><p>{r.specialty_utilizers ?? "Suppressed"} specialty utilizers</p>
        <p>{r.cost === null ? "Suppressed" : `$${r.cost.toLocaleString()}`} synthetic cost</p></article>)}</div>
      <p data-tour="suppression">{aggregate.suppression}</p><small>Source: {aggregate.dataset} · {aggregate.as_of}. No causal conclusions or employee rankings.</small></section>}
    {session && session.role !== "employer" && <>
      {workbench && <Metrics data={workbench} />}<div className="data-note"><span>{workbench ? `Snapshot ${dateTime(workbench.as_of)} · ${workbench.employer.id} · ${authProfile === "showcase" ? "Selected synthetic group, not authenticated access" : "Only your authorized group"}` : "No operational snapshot available."}</span>
        <button className="text-button" disabled={busy} onClick={reload}>Refresh data</button></div>
      <nav className="workbench-nav" data-tour="operations-nav" aria-label="Operations views">
        <button aria-current={view === "cases" ? "page" : undefined} disabled={busy} onClick={() => setView("cases")}>Case queue <span>{workbench?.summary.total ?? "—"}</span></button>
        <button aria-current={view === "tasks" ? "page" : undefined} disabled={busy} onClick={() => setView("tasks")}>Team tasks <span>{workbench?.summary.open_tasks ?? "—"}</span></button>
        {session.role === "reviewer" && session.features.renewal && <button aria-current={view === "renewals" ? "page" : undefined} disabled={busy} onClick={() => setView("renewals")}>Renewal watch <span>{renewals.length}</span></button>}
      </nav>
      {view === "tasks" && <section className="card team-board" data-tour="team-tasks"><p className="eyebrow">ROLE-SAFE WORK PLAN</p><h2>Team tasks</h2><p>Open a case to manage the handoff. Internal clinical tasks are excluded from contact-centre responses.</p>
        {workbench?.tasks.length ? <div className="table-scroll"><table><thead><tr><th>Task / case</th><th>Responsible team</th><th>Due</th><th>Status</th><th>Action</th></tr></thead><tbody>
          {workbench.tasks.map(t => <tr key={t.id}><td><strong>{t.title}</strong><small className="block">{t.case_id}</small></td><td>{t.team}</td><td>{dateTime(t.due)}</td><td><span className={`state ${t.state}`}>{label(t.state)}</span></td>
            <td><button className="secondary" disabled={busy} onClick={() => navigateCase(t.case_id, "tasks")}>Open case</button></td></tr>)}</tbody></table></div> : <p className="empty">No team tasks visible to your role.</p>}</section>}
      {view === "renewals" && <section className="card" data-tour="renewals"><p className="eyebrow">PREPARATION, NOT AUTO-RENEWAL</p><h2>Renewal watch / next 30 days</h2><p>Recorded expiries from your authorized group. Opening a renewal does not extend coverage.</p>
        <div className="renewal-grid">{renewals.map(r => <article className="renewal-item" key={r.id}><span className="state due_soon">Expires {r.expiry}</span><h3>{r.id}</h3><p>{r.draft}</p>
          <button className="secondary" disabled={busy} onClick={() => navigateCase(r.id)}>Open renewal</button></article>)}</div>
        {!renewals.length && <p className="empty">No authorized renewals fall in this 30-day window.</p>}</section>}
      {view === "cases" && <div className="operations-layout">
      <aside className="queue card operational-queue" data-tour="queue" aria-busy={queueLoading}><div className="section-heading"><div><p className="eyebrow">YOUR AUTHORIZED GROUP</p><h2>Case queue</h2></div><span className="count">{workbench?.matched ?? "—"}</span></div>
        <label className="sr-only" htmlFor="filter">Search cases</label>{authProfile === "showcase" ?
          <select id="filter" value={filter} disabled={busy} onChange={e => setFilter(e.target.value)}>
            <option value="">All synthetic cases in this view</option>
            {Array.from({ length: 12 }, (_, i) => `SYN-CASE-${String(i + 1).padStart(3, "0")}`).map(id => <option key={id}>{id}</option>)}
          </select> : <input id="filter" maxLength={100} placeholder={session.role === "reviewer" ? "Search case, fictional member or ID" : "Search case ID"} value={filter} disabled={busy} onChange={e => setFilter(e.target.value)} />}
        <div className="queue-filters"><label>Status<select value={statusFilter} disabled={busy} onChange={e => setStatusFilter(e.target.value)}>
          <option value="all">All statuses</option>{["received", "intake_checked", "intake_incomplete", "review_ready", "information_requested", "approved", "declined"].map(s => <option key={s} value={s}>{label(s)}</option>)}</select></label>
          <label>Priority<select value={priorityFilter} disabled={busy} onChange={e => setPriorityFilter(e.target.value)}><option value="all">All priorities</option><option value="priority">Priority</option><option value="standard">Standard</option></select></label>
          <label>Ownership<select value={ownerFilter} disabled={busy} onChange={e => setOwnerFilter(e.target.value)}><option value="all">All owners</option>{session.role === "reviewer" && <option value="mine">Assigned to me</option>}<option value="unassigned">Unassigned</option></select></label>
          <label>Sort by<select value={sort} disabled={busy} onChange={e => setSort(e.target.value)}><option value="target">Service target</option><option value="oldest">Oldest first</option><option value="newest">Newest first</option><option value="priority">Priority first</option></select></label></div>
        <div className="queue-result" role="status">{queueLoading ? "Updating queue…" : `${workbench?.matched ?? 0} matching / ${workbench?.summary.total ?? 0} authorized`}
          <button className="text-button" disabled={busy} onClick={() => { setFilter(""); setStatusFilter("all"); setPriorityFilter("all"); setOwnerFilter("all"); }}>Clear filters</button></div>
        <div className="queue-items">{workbench?.items.map(c => <button disabled={busy || queueLoading} key={c.id}
          aria-pressed={current?.id === c.id} className={`case-item ${current?.id === c.id ? "selected" : ""}`} onClick={() => navigateCase(c.id)}>
          <span className="queue-item-top"><strong>{c.id}</strong>{c.priority === "priority" && <span className="priority-badge">PRIORITY</span>}</span>
          <b className="queue-name">{c.display_name}</b><span>{label(c.state)} · {c.request_type}</span>
          <span className="queue-item-meta"><small>{label(c.owner)}</small><small>{Math.floor(c.age_hours / 24)}d {Math.floor(c.age_hours % 24)}h old</small></span>
          <span className={`target-label ${c.target_state}`}>{label(c.target_state)} · {dateTime(c.target)}</span>
          {(!!c.missing_fields?.length || c.conflict || c.source_gap) && <small className="warning-text">{[c.missing_fields?.length ? "Intake gap" : "", c.conflict ? "Evidence conflict" : "", c.source_gap ? "Source gap" : ""].filter(Boolean).join(" / ")}</small>}
        </button>)}</div>
        {workbench && !workbench.items.length && <p className="empty">No matching cases. Clear filters to restore your authorized queue.</p>}
        {!workbench && <p className="empty">Queue unavailable. Use Refresh data after resolving the reported error.</p>}
        {workbench && <p className="target-disclaimer">{workbench.target_note}</p>}
      </aside>
      <div className="case-workspace">
      {opening && <section className="card" role="status">Loading authorized case record…</section>}
      {!opening && current && operations && <><section className="card case-header"><div><p className="eyebrow">SPECIAL AUTHORIZATION / {current.expiry ? "RENEWAL" : "NEW REQUEST"}</p><h2>{current.id}</h2><p>{current.member360?.name || "Authorized case status"}</p></div>
        <span className="pill">{current.state.replaceAll("_", " ")}</span><small>Authoritative record v{current.version}</small></section>
        <nav className="case-tabs" aria-label="Case sections">{tabs.map(t => <button key={t} aria-current={tab === t ? "page" : undefined} disabled={busy} onClick={() => setTab(t)}>{t === "tasks" ? `Tasks (${operations.tasks.filter(x => x.state !== "done").length})` : label(t)}</button>)}</nav>
        {tab === "overview" && <Overview current={current} ops={operations} reviewer={session.role === "reviewer"} busy={busy} owner={owner} priority={priority} setOwner={setOwner} setPriority={setPriority} onAssign={saveRouting} onNavigate={setTab} />}
        {tab === "documents" && session.role === "reviewer" && <>
          {authProfile !== "local" && <button className="secondary" disabled={busy} onClick={downloadSource}>Download synthetic intake source PDF</button>}
          <Documents ops={operations} /></>}
        {tab === "tasks" && <TaskPanel tasks={operations.tasks} reviewer={session.role === "reviewer"} busy={busy} onCreate={createTask} onUpdate={updateTask} />}
        {session.role === "reviewer" && <>
          {tab === "intake" && <section className="card" data-tour="intake"><div className="section-heading"><h2>Intake & Member 360</h2><button className="secondary" disabled={running || !!current.decision || !session.features.intake} onClick={() => run("intake")}>Run intake</button></div>
            <p>Plan {current.member360?.plan} · Coverage {current.member360?.coverage} · Values below 85% confidence require human verification.</p>
            {authProfile !== "local" && <p>Synthetic member record: {current.member360?.member_id}. Compare the source PDF before confirming any OCR correction.</p>}
            <div className="form-grid">{Object.entries(fields).map(([name, field]) => <label key={name}>{name.replaceAll("_", " ")}
              {authProfile === "showcase" ? <select value={field.value || ""} disabled={running || !!current.decision}
                onChange={e => setFields(f => ({ ...f, [name]: { ...field, value: e.target.value || null, confidence: 1 } }))}>
                {!current.showcase_fields?.[name]?.includes(field.value || "") && <option value={field.value || ""} disabled>Verify OCR against a built-in value</option>}
                {current.showcase_fields?.[name]?.map(value => <option key={value} value={value}>{value || "Missing / not provided"}</option>)}
              </select> : <input value={field.value || ""} readOnly={name === "member_id" && authProfile !== "starter"} disabled={running || !!current.decision}
                onChange={e => setFields(f => ({ ...f, [name]: { ...field, value: e.target.value || null, confidence: 1 } }))} />}
              <small className={field.confidence < .85 || !field.value ? "warning-text" : ""}>{Math.round(field.confidence * 100)}% confidence · {field.source}</small>
            </label>)}</div><button className="secondary" disabled={running || !!current.decision} onClick={verifyForm}>Confirm verified form fields</button>
            <details><summary>Prior therapy claims</summary>{current.member360?.claims.map(c => <p key={c.id}>{c.id} · {c.therapy} · {c.date}</p>)}</details>
          </section>}
          {tab === "evidence" && <section className="card" data-tour="evidence"><div className="section-heading"><div><p className="eyebrow">GROUNDED, NOT DECIDED</p><h2>Criteria evidence matrix</h2></div>
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
          </section>}
          {tab === "decision" && <section className="card decision" data-tour="decision"><p className="eyebrow">{authProfile === "showcase" ? "ANONYMOUS HUMAN DEMO ACTION" : "AUTHORIZED HUMAN CHECKPOINT"}</p><h2>Reviewer decision</h2>
            {current.decision ? <><p><strong>{current.decision.outcome}</strong> · {current.decision.reviewer} · {new Date(current.decision.timestamp).toLocaleString()}</p><p>{current.decision.reason}</p><small>Evidence brief v{current.decision.brief_version}. Saved decisions are immutable in this demo.</small></> : <>
              <p>Evidence states are not clinical outcomes. Review all gaps and conflicts before deciding.</p>
              <label>Outcome<select value={outcome} onChange={e => { setOutcome(e.target.value); decisionKey.current = null; }} disabled={running}>
                <option value="information_requested">Request more information</option><option value="approved">Approve</option><option value="declined">Decline</option></select></label>
              <label htmlFor="decision-reason">Rationale</label>{authProfile === "showcase" ? <select id="decision-reason" value={reason} disabled={running}
                onChange={e => { setReason(e.target.value); decisionKey.current = null; }}>
                <option value="">Choose a synthetic rationale</option>{reasons.map(value => <option key={value}>{value}</option>)}
              </select> : <textarea id="decision-reason" value={reason} onChange={e => { setReason(e.target.value); decisionKey.current = null; }} minLength={10} maxLength={1000} disabled={running} />}
              <label className="checkbox"><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} disabled={running} />I reviewed the current evidence and am explicitly recording this decision.</label>
              <button disabled={running || !current.brief || !confirmed || reason.trim().length < 10} onClick={saveDecision}>Record my decision</button>
            </>}
          </section>}
        </>}
        {tab === "status" && <section className="card" data-tour="status"><p className="eyebrow">PLAIN LANGUAGE / MINIMUM NECESSARY</p><div className="section-heading"><h2>Case status & next step</h2><button className="secondary" disabled={busy} onClick={() => run("status")}>Run status check</button></div><p>{current.message}</p><p>Next owner: {current.next_owner}. No decision date is promised.</p>
          {authProfile === "showcase" ? <><h3>Built-in synthetic communication preview</h3><p>{draft}</p>
            <p className="small">Preview only: no free-text submission, saved outbox or external send in the public showcase.</p></> : <>
          <label>{current.missing_information_draft ? "Unsaved missing-information draft" : "Unsaved member-update draft"}<textarea value={draft} maxLength={2000} onChange={e => setDraft(e.target.value)} disabled={running} /></label>
          <label className="checkbox"><input type="checkbox" checked={sendConfirmed} onChange={e => setSendConfirmed(e.target.checked)} disabled={running} />Confirm this draft for the local outbox only.</label>
          <button className="secondary" disabled={running || !sendConfirmed || !draft.trim()} onClick={saveDraft}>Confirm local draft (no external send)</button>
          <div className="local-outbox"><h3>Your confirmed local drafts</h3><p className="small">Only drafts saved by your current persona are shown. No external delivery.</p>
            {operations.outbox.length ? operations.outbox.map(d => <details key={d.id}><summary>Draft #{d.id} / {dateTime(d.created)}</summary><p>{d.text}</p></details>) : <p className="empty">No confirmed local drafts for this persona.</p>}</div></>}
        </section>}
        {tab === "activity" && <section className="card" data-tour="activity"><p className="eyebrow">PERSISTED, ROLE-FILTERED EVENTS</p><h2>Audit timeline</h2><ol className="timeline">{current.timeline.toReversed().map(t => <li key={t.id}><b>{t.event.replaceAll("_", " ")}</b>
          <small>{new Date(t.created).toLocaleString()}{t.actor && ` · ${t.actor}`} · trace {t.trace}</small></li>)}</ol></section>}
      </>}
      {!opening && !current && <section className="card empty">Select an authorized case to inspect its record.</section>}
      </div>
      <aside className="assistant card" data-tour="assistant"><p className="eyebrow">BENEFITS IQ ASSISTANT</p><h2>Your review companion</h2>
        <p>{session.mode === "live" ? "Configured model-backed chat. Capability data remains synthetic." : "Deterministic synthetic agent behind Microsoft Agent Framework + AG-UI. No live AI call."}</p>
        <div className="activity" role="status" aria-live="polite">{running ? <strong>Workflow in progress…</strong> : <strong>Ready for a human-led workflow</strong>}
          {activities.map((a, i) => <p key={`${i}-${a}`}>{a}</p>)}</div>
        {running && controller.current && <button className="secondary" onClick={() => controller.current?.abort()}>Cancel workflow</button>}
        <p className="small">Interrupted runs are never silently replayed. Refresh the case before retrying; streamed state is provisional.</p>
        {current && session.features.chat && <><button className="secondary" disabled={busy} onClick={toggleChat}>{showChat ? "Close chat" : "Open case-bound chat"}</button>
          {showChat && <CaseChat key={`${session.id}-${current.id}`} caseId={current.id} presetOnly={authProfile === "showcase"} />}</>}
      </aside>
    </div>}</>}
    <footer>BENEFITS IQ <span>Independent October SE Build demo · Synthetic fixtures · No production integrations</span></footer>
  </main>;
}
