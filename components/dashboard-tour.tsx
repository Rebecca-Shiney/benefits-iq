"use client";

import { useId, useLayoutEffect, useRef, useState } from "react";

type TourContext = {
  session: string | null;
  role: "reviewer" | "contact" | "employer" | null;
  demo: boolean;
  view: string;
  tab: string;
  caseId: string | null;
  busy: boolean;
  ready: boolean;
  chat: boolean;
  intake: boolean;
  evidence: boolean;
};
type Step = { target: string; title: string; text: string; tab?: string };
type Walkthrough = { steps: Step[]; index: number; direction: 1 | -1; key: string; initialTab: string; expectedTab: string };
type Position = { left: number; top: number; focus: { left: number; top: number; width: number; height: number } };

function visibleTarget(name: string) {
  const element = document.querySelector<HTMLElement>(`[data-tour="${name}"]`);
  if (!element || element.closest('[hidden], [aria-hidden="true"]')) return null;
  const rect = element.getBoundingClientRect();
  const style = getComputedStyle(element);
  return rect.width && rect.height && style.visibility !== "hidden" && style.display !== "none" ? element : null;
}

function stepsFor(context: TourContext): Step[] {
  const workspace: Step = {
    target: "workspace", title: context.demo ? "Choose your demo workspace" : "Your assigned workspace",
    text: context.demo
      ? "Switch between the fictional reviewer, contact-centre and employer views here. This is demo navigation, not sign-in or authenticated roles. Use synthetic data only."
      : "This is your signed-in workspace. Use only synthetic data; never enter real personal or health information.",
  };
  if (!context.role) return [workspace,
    { target: "safety", title: "People decide. Agents prepare.", text: "The data is fictional. Agents help check and explain it; they do not make clinical decisions or send messages. This tour only points things out." },
    { target: "welcome", title: "Start with a workspace", text: "Close this guide, choose a view and open the workspace. Use the same guide button there for a walkthrough tailored to that dashboard." },
  ];
  if (context.role === "employer") return [workspace,
    { target: "portfolio", title: "See the group, not individual members", text: "These are fictional employer-level trends from a separate portfolio dataset. There is no employee drill-through, clinical case list or individual ranking." },
    { target: "suppression", title: "Small groups stay suppressed", text: "Suppressed values are intentionally hidden when a group is too small. Read the source and date here; these figures are not a live insurer feed." },
  ];
  const steps: Step[] = [workspace,
    { target: "metrics", title: "Your workload at a glance", text: "See active requests, items past their internal target, review readiness and open tasks. These are synthetic operational counts, not promised decision times." },
  ];
  if (context.view !== "cases") return [...steps,
    { target: "operations-nav", title: "Choose an operations view", text: "Move between the case queue and team tasks. Reviewers may also see Renewal watch. Switching views does not change a case or extend coverage." },
    context.view === "renewals"
      ? { target: "renewals", title: "Prepare for upcoming renewals", text: "This list shows recorded expiries in the next 30 days. Open a renewal to inspect its case; nothing is renewed automatically." }
      : { target: "team-tasks", title: "Keep handoffs visible", text: "See the responsible team, due date and task status. Open a case to manage a task yourself. A task is not a clinical outcome or an external message." },
  ];
  steps.push({ target: "queue", title: "Find a case to work on", text: "Search and filter the selected group's cases, then choose one to inspect. Team tasks and, for reviewers, Renewal watch are available above the queue." });
  if (context.caseId) {
    if (context.role === "reviewer" && ["overview", "intake", "documents", "evidence", "decision"].includes(context.tab)) {
      if (context.intake) steps.push({ target: "intake", tab: "intake", title: "Check intake and Member 360", text: "Review the member snapshot and form fields. Missing values or low confidence need a human check against the source. This tour does not run intake or save corrections." });
      steps.push({ target: "documents", tab: "documents", title: "Look at the original sources", text: "Read the built-in form, policy and prior-therapy sources. Check their versions and dates; a missing or stale source needs human follow-up." });
      if (context.evidence) steps.push({ target: "evidence", tab: "evidence", title: "Follow evidence back to its source", text: "The evidence matrix connects each criterion to citations, gaps and conflicts. Preparing evidence is a separate action; a supported check is not an approval." });
      steps.push({ target: "decision", tab: "decision", title: "A human records the decision", text: "Review the evidence, choose an outcome and rationale, then explicitly confirm only when you intend to save. Decisions are durable demo records. This tour never selects or submits one." });
    } else if (context.role === "contact" && context.tab === "overview") {
      steps.push(
        { target: "status", tab: "status", title: "Explain the next step simply", text: "Read the current status and next owner without clinical evidence or reviewer rationale. Any communication shown is a preview or local draft, never an external send." },
        { target: "tasks", tab: "tasks", title: "Coordinate a follow-up", text: "Track the contact team's handoffs here. Creating or completing a task is your separate choice; it does not change the clinical outcome." },
      );
    } else {
      const panels: Record<string, Step> = {
        overview: { target: "overview", title: "Understand the selected request", text: "Read its context and next owner before taking an action. Source completeness and service priority do not determine a clinical outcome." },
        tasks: { target: "tasks", title: "Coordinate a follow-up", text: "Track team handoffs and their progress here. Creating or completing a task is a separate action, not a clinical decision or external send." },
        status: { target: "status", title: "Explain the next step simply", text: "Use the case status and next owner for a plain-language update. No decision date is promised and no message is sent by this tour." },
        activity: { target: "activity", title: "See what changed", text: "The timeline keeps the events visible to this view. Public demo actions are anonymous, not verified clinical acts. The tour adds no audit entries." },
      };
      if (panels[context.tab]) steps.push(panels[context.tab]);
    }
    if (context.chat) steps.push({ target: "assistant", title: "Ask a read-only assistant", text: "Open case-bound chat when you want an explanation of status, intake or criteria. Answers are advisory; check sources yourself. Chat cannot record decisions or send messages, and this tour makes no model calls." });
  }
  return steps;
}

export function DashboardTour({ context, onNavigate }: { context: TourContext; onNavigate: (tab: string) => void }) {
  const [tour, setTour] = useState<Walkthrough | null>(null);
  const [position, setPosition] = useState<Position | null>(null);
  const [announcement, setAnnouncement] = useState("");
  const trigger = useRef<HTMLButtonElement>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const card = useRef<HTMLDivElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const titleId = useId(), descriptionId = useId();
  const key = JSON.stringify([context.session, context.role, context.caseId, context.view, context.busy, context.chat, context.intake, context.evidence]);
  const active = tour !== null;

  function finish(message = "Tour closed. You can restart from Get to know your dashboard.", restore = true) {
    if (restore && tour?.key === key && tour.expectedTab === context.tab) onNavigate(tour.initialTab);
    setTour(null); setPosition(null); setAnnouncement(message);
  }

  function move(index: number, steps = tour?.steps, direction: 1 | -1 = 1) {
    if (!tour || !steps) return;
    if (index < 0 || index >= steps.length) { finish("Tour complete. Explore at your own pace, or restart from the guide button."); return; }
    const expectedTab = steps[index].tab || tour.initialTab;
    setPosition(null);
    setTour({ ...tour, steps, index, direction, expectedTab });
    onNavigate(expectedTab);
  }

  useLayoutEffect(() => {
    if (!active) return;
    const element = dialog.current;
    element?.showModal();
    return () => { element?.close(); trigger.current?.focus(); };
  }, [active]);

  useLayoutEffect(() => {
    if (!tour) return;
    if (tour.key !== key || tour.expectedTab !== context.tab) {
      finish("The dashboard changed, so the tour closed. Restart for the current view.", false);
      return;
    }
    const snapshot = tour;
    const step = tour.steps[tour.index];
    let frame = 0;
    let scrolled = false;
    function measure() {
      const target = visibleTarget(step.target);
      if (!target) {
        const remaining = snapshot.steps.filter((_, index) => index !== snapshot.index);
        const next = snapshot.direction === 1 ? snapshot.index : snapshot.index - 1;
        if (next < 0 || next >= remaining.length) finish("The highlighted section is unavailable, so the guide closed. You can restart for the current view.");
        else move(next, remaining, snapshot.direction);
        return;
      }
      if (!scrolled) {
        // Instant scrolling also avoids motion for visitors with reduced-motion preferences.
        target.scrollIntoView({
          block: "start", inline: "nearest", behavior: "instant",
        });
        scrolled = true;
      }
      const rect = target.getBoundingClientRect();
      const panel = card.current;
      if (!panel) return;
      const viewport = window.visualViewport;
      const width = viewport?.width ?? window.innerWidth, height = viewport?.height ?? window.innerHeight;
      const offsetX = viewport?.offsetLeft ?? 0, offsetY = viewport?.offsetTop ?? 0;
      const margin = 16, gap = 14;
      const panelWidth = panel.offsetWidth, panelHeight = panel.offsetHeight;
      const minX = offsetX + margin, minY = offsetY + margin;
      const maxX = offsetX + width - margin, maxY = offsetY + height - margin;
      const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(value, Math.max(min, max)));
      const candidates = [
        { left: rect.right + gap, top: clamp(rect.top, minY, maxY - panelHeight) },
        { left: rect.left - gap - panelWidth, top: clamp(rect.top, minY, maxY - panelHeight) },
        { left: clamp(rect.left, minX, maxX - panelWidth), top: rect.bottom + gap },
        { left: clamp(rect.left, minX, maxX - panelWidth), top: rect.top - gap - panelHeight },
      ];
      const fitted = candidates.find(p => p.left >= minX && p.top >= minY && p.left + panelWidth <= maxX && p.top + panelHeight <= maxY);
      const placement = fitted || { left: minX, top: rect.top > offsetY + height / 2 ? minY : Math.max(minY, maxY - panelHeight) };
      let top = clamp(rect.top - 5, minY, maxY), bottom = clamp(rect.bottom + 5, minY, maxY);
      if (!fitted) {
        if (placement.top === minY) top = Math.max(top, placement.top + panelHeight + gap);
        else bottom = Math.min(bottom, placement.top - gap);
      }
      const left = clamp(rect.left - 5, minX, maxX), right = clamp(rect.right + 5, minX, maxX);
      setPosition({ ...placement, focus: { left, top, width: Math.max(0, right - left), height: Math.max(0, bottom - top) } });
    }
    function schedule() { cancelAnimationFrame(frame); frame = requestAnimationFrame(measure); }
    function resized() { scrolled = false; schedule(); }
    measure();
    const observer = new MutationObserver(records => {
      if (records.some(record => !dialog.current?.contains(record.target))) schedule();
    });
    observer.observe(document.querySelector("main") || document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["hidden", "style", "class", "aria-hidden"] });
    const resize = new ResizeObserver(schedule);
    resize.observe(document.documentElement);
    if (card.current) resize.observe(card.current);
    const target = visibleTarget(step.target);
    if (target) resize.observe(target);
    window.addEventListener("resize", resized);
    window.addEventListener("scroll", schedule, true);
    window.visualViewport?.addEventListener("resize", resized);
    window.visualViewport?.addEventListener("scroll", schedule);
    return () => {
      cancelAnimationFrame(frame); observer.disconnect(); resize.disconnect();
      window.removeEventListener("resize", resized); window.removeEventListener("scroll", schedule, true);
      window.visualViewport?.removeEventListener("resize", resized);
      window.visualViewport?.removeEventListener("scroll", schedule);
    };
  }, [tour, key, context.tab]);

  useLayoutEffect(() => {
    if (tour && position) heading.current?.focus({ preventScroll: true });
  }, [tour, position !== null]);

  const step = tour?.steps[tour.index];
  return <>
    <button ref={trigger} className="secondary tour-trigger" type="button" disabled={context.busy || !context.ready}
      aria-haspopup="dialog" onClick={() => {
        const steps = stepsFor(context).filter(item => item.tab || visibleTarget(item.target));
        if (!steps.length) { setAnnouncement("No dashboard sections are available yet. Try again after loading finishes."); return; }
        setAnnouncement("");
        setTour({ steps, index: 0, direction: 1, key, initialTab: context.tab, expectedTab: context.tab });
      }}>Get to know your dashboard</button>
    <span className="sr-only" role="status">{announcement}</span>
    <dialog ref={dialog} className="dashboard-tour" data-tour-target={step?.target} aria-label="Dashboard guide" aria-labelledby={titleId} aria-describedby={descriptionId}
      onCancel={event => { event.preventDefault(); finish(); }}
      onKeyDown={event => {
        if (event.key === "Tab") {
          const buttons = Array.from(dialog.current?.querySelectorAll<HTMLButtonElement>("button:not(:disabled)") || []);
          const first = buttons[0], last = buttons.at(-1), focused = document.activeElement;
          if (event.shiftKey && (focused === first || focused === heading.current)) {
            event.preventDefault(); last?.focus();
          } else if (!event.shiftKey && focused === last) {
            event.preventDefault(); first?.focus();
          }
          return;
        }
        if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
        if (event.key === "ArrowRight") { event.preventDefault(); move((tour?.index ?? 0) + 1); }
        if (event.key === "ArrowLeft") { event.preventDefault(); if (tour && tour.index > 0) move(tour.index - 1, tour.steps, -1); }
      }}>
      {tour && step && <>
        {position && <div className="tour-spotlight" style={position.focus} aria-hidden="true" />}
        <div ref={card} className="tour-card" style={{ left: position?.left ?? 16, top: position?.top ?? 16, visibility: position ? "visible" : "hidden" }}>
          <button type="button" className="secondary tour-close" aria-label="Close dashboard tour" onClick={() => finish()}>x</button>
          <p className="eyebrow">GET TO KNOW YOUR DASHBOARD</p>
          <p className="tour-progress" aria-live="polite" aria-atomic="true">Step {tour.index + 1} of {tour.steps.length}</p>
          <h2 id={titleId} ref={heading} tabIndex={-1}>{step.title}</h2>
          <p id={descriptionId}>{step.text}</p>
          <p className="small">Read-only guide · Arrow keys move · Escape closes</p>
          <div className="tour-actions">
            <button type="button" className="secondary" onClick={() => finish()}>Skip tour</button>
            <button type="button" className="secondary" disabled={tour.index === 0} onClick={() => move(tour.index - 1, tour.steps, -1)}>Back</button>
            <button type="button" onClick={() => move(tour.index + 1)}>{tour.index === tour.steps.length - 1 ? "Finish" : "Next"}</button>
          </div>
        </div>
      </>}
    </dialog>
  </>;
}
