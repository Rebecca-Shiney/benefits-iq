"use client";

import { useState } from "react";
import type { Case, CaseOperations, Task, TaskKind, Workbench } from "@/lib/contracts";

export function label(value: string) { return value.replaceAll("_", " "); }
export function dateTime(value: string) {
  return new Date(value).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function Metrics({ data }: { data: Workbench }) {
  const s = data.summary;
  return <section className="metrics" aria-label="Authorized workload metrics">
    {[
      { title: "Active requests", value: s.active, detail: `${s.total} authorized records`, tone: "teal" },
      { title: "Past service target", value: s.overdue, detail: `${s.due_soon} due within 24 hours`, tone: "amber" },
      { title: "Ready for review", value: s.review_ready, detail: `${s.unassigned} active requests unassigned`, tone: "blue" },
      { title: "Open team tasks", value: s.open_tasks, detail: "Tracked locally, not externally sent", tone: "purple" },
    ].map(m => <article className={`metric ${m.tone}`} key={m.title}><p>{m.title}</p><strong>{m.value}</strong><small>{m.detail}</small></article>)}
  </section>;
}

export function TaskPanel({ tasks, reviewer, busy, onCreate, onUpdate }: {
  tasks: Task[]; reviewer: boolean; busy: boolean;
  onCreate: (kind: TaskKind) => void; onUpdate: (task: Task, state: Task["state"]) => void;
}) {
  const [kind, setKind] = useState<TaskKind>("member_follow_up");
  return <section className="card task-panel"><div className="section-heading"><div><p className="eyebrow">TRACKED HANDOFFS</p><h2>Tasks & follow-ups</h2></div>
    <span className="count">{tasks.filter(t => t.state !== "done").length} open</span></div>
    <p>Team-owned local tasks. Completing one does not change a clinical outcome or send a message.</p>
    <div className="task-create"><label htmlFor="task-kind">New handoff<select id="task-kind" value={kind} disabled={busy} onChange={e => setKind(e.target.value as TaskKind)}>
      <option value="member_follow_up">Member follow-up draft / Contact centre</option>
      {reviewer && <><option value="verify_form">Verify form / Clinical intake</option>
        <option value="resolve_evidence">Reconcile evidence / Clinical review</option>
        <option value="renewal_review">Renewal review / Clinical review</option></>}
    </select></label><button className="secondary" disabled={busy} onClick={() => onCreate(kind)}>Create task</button></div>
    {!tasks.length && <p className="empty">No tasks visible to your role. Create a follow-up when coordination is needed.</p>}
    <ul className="task-list">{tasks.map(task => <li key={task.id}>
      <span className={`task-check ${task.state === "done" ? "done" : ""}`} aria-hidden="true">{task.state === "done" ? "✓" : "○"}</span>
      <div><strong>{task.title}</strong><small>{task.team} · Due {dateTime(task.due)} · v{task.version}</small>
        <span className={`state ${task.state}`}>{label(task.state)}</span></div>
      <div className="task-actions">{task.state === "open" && <button className="secondary" disabled={busy} onClick={() => onUpdate(task, "in_progress")}>Start</button>}
        {task.state !== "done" ? <button className="secondary" disabled={busy} onClick={() => onUpdate(task, "done")}>Complete</button>
          : <button className="secondary" disabled={busy} onClick={() => onUpdate(task, "open")}>Reopen</button>}</div>
    </li>)}</ul>
  </section>;
}

export function Overview({ current, ops, reviewer, busy, owner, priority, setOwner, setPriority, onAssign, onNavigate }: {
  current: Case; ops: CaseOperations; reviewer: boolean; busy: boolean; owner: string; priority: string;
  setOwner: (value: string) => void; setPriority: (value: string) => void; onAssign: () => void;
  onNavigate: (tab: string) => void;
}) {
  return <div className="overview-grid">
    <section className="card"><p className="eyebrow">REQUEST SNAPSHOT</p><h2>{current.expiry ? "Renewal authorization" : "New authorization"}</h2>
      <dl className="context-list"><div><dt>Employer</dt><dd>{ops.employer.name}</dd></div>
        <div><dt>Region</dt><dd>{ops.employer.region}</dd></div>
        <div><dt>Intake channel</dt><dd>{ops.channel}</dd></div>
        <div><dt>Received</dt><dd>{dateTime(ops.received)}</dd></div>
        <div><dt>Internal target</dt><dd>{dateTime(ops.target)}</dd></div>
        <div><dt>Reviewer owner</dt><dd>{label(ops.owner)}</dd></div>
        {reviewer && <><div><dt>Member identifier</dt><dd>{current.member}</dd></div><div><dt>Coverage</dt><dd>{current.member360?.coverage} / {ops.employer.plan}</dd></div></>}
        {current.expiry && <div><dt>Recorded expiry</dt><dd>{current.expiry} · No automatic extension</dd></div>}
      </dl><p className="small">Synthetic receipt dates and internal service targets are operational context, not a promised decision time.</p>
    </section>
    <section className="card"><p className="eyebrow">WHAT NEEDS ATTENTION</p><h2>{reviewer ? "Readiness checklist" : "Member support context"}</h2>
      {reviewer ? <><div className="completeness"><strong>{ops.verified_fields}/{ops.field_count}</strong><span>form fields meet confidence threshold</span></div>
        <progress aria-label="Verified form completeness" value={ops.verified_fields} max={ops.field_count} />
        <ul className="readiness-list">
          <li><span className={`state ${ops.missing_fields?.length ? "missing" : "supported"}`}>{ops.missing_fields?.length ? "Verify" : "Complete"}</span>
            <div><strong>Intake form</strong><small>{ops.missing_fields?.length ? ops.missing_fields.map(label).join(", ") : "No missing or low-confidence fields."}</small></div>
            <button className="text-button" disabled={busy} onClick={() => onNavigate("intake")}>Inspect</button></li>
          <li><span className={`state ${ops.source_gap ? "missing" : "supported"}`}>{ops.source_gap ? "Source gap" : "Current"}</span>
            <div><strong>Policy & criteria</strong><small>{ops.source_gap ? "Missing or expired source. Human escalation required." : "Matching versioned criteria fixture is in date."}</small></div>
            <button className="text-button" disabled={busy} onClick={() => onNavigate("documents")}>Sources</button></li>
          <li><span className={`state ${ops.conflict ? "conflict" : "supported"}`}>{ops.conflict ? "Conflict" : "Aligned"}</span>
            <div><strong>Prior therapy evidence</strong><small>{ops.conflict ? "Form and claims disagree. Reconcile before deciding." : "No form/claim conflict detected by fixture check."}</small></div>
            <button className="text-button" disabled={busy} onClick={() => onNavigate("evidence")}>Review</button></li>
        </ul><p className="small">These checks describe source completeness, not eligibility approval or clinical advice.</p></>
        : <><p>{current.message}</p><div className="status-next"><strong>Next team</strong><p>{current.next_owner}</p></div>
          <p>Clinical evidence, member health details and reviewer rationale are not available in this role.</p>
          <button className="secondary" disabled={busy} onClick={() => onNavigate("status")}>Prepare status update</button></>}
    </section>
    {reviewer && <section className="card routing"><div><p className="eyebrow">OPERATIONAL ROUTING</p><h2>Ownership & priority</h2>
      <p>Priority changes the internal target only. It never approves a request.</p></div>
      <label>Reviewer owner<select value={owner} onChange={e => setOwner(e.target.value)} disabled={busy || !!current.decision}>
        <option value="unassigned">Unassigned</option>{ops.owners?.map(o => <option value={o.id} key={o.id}>{o.id} / {o.label}</option>)}</select></label>
      <label>Service priority<select value={priority} onChange={e => setPriority(e.target.value)} disabled={busy || !!current.decision}>
        <option value="standard">Standard / 72h target</option><option value="priority">Priority / 24h target</option></select></label>
      <button disabled={busy || !!current.decision || (owner === ops.owner && priority === ops.priority)} onClick={onAssign}>Save routing</button>
      {current.decision && <p className="small">This decided case is immutable; follow-up tasks remain available.</p>}
    </section>}
  </div>;
}

export function Documents({ ops }: { ops: CaseOperations }) {
  return <section className="card"><p className="eyebrow">SOURCE REGISTER / LOCAL FIXTURES</p><h2>Documents & source freshness</h2>
    <p>Inspect the actual structured form, policy passages and prior-therapy fixtures used by this case. No uploaded files, OCR service or production connector is represented.</p>
    <div className="source-list">{ops.documents?.map(doc => <article key={doc.id}><div className="section-heading"><div><small>{doc.kind}</small><h3>{doc.title}</h3></div>
      <span className={`state ${doc.status}`}>{label(doc.status)}</span></div>
      <p className="source-id">{doc.id} / {doc.version || "No version"}</p><small>Source date: {doc.as_of || "Unavailable"}{doc.valid_until && ` · Valid through ${doc.valid_until}`}</small>
      <details><summary>Inspect local source context</summary><p>{doc.detail}</p></details>
      {doc.status === "stale" && <p className="warning-text">Not current evidence. Escalate for human source verification.</p>}
    </article>)}</div>
  </section>;
}
