"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { authorizationHeaders } from "@/lib/browser-auth";
import { readChatEvents } from "@/lib/chat-protocol";

type Turn = { id: string; prompt: string; answer: string; status: "streaming" | "complete" | "failed" | "cancelled" };

export function CaseChat({ caseId }: { caseId: string }) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [activity, setActivity] = useState("Ready. Chat cannot save decisions or send communications.");
  const request = useRef<AbortController | null>(null);
  const mounted = useRef(true);
  const input = useRef<HTMLTextAreaElement>(null);
  const history = useRef<HTMLDivElement>(null);
  const nearBottom = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; request.current?.abort(); };
  }, []);
  useEffect(() => {
    if (nearBottom.current && history.current) history.current.scrollTop = history.current.scrollHeight;
  }, [turns, activity]);
  useEffect(() => {
    if (!busy && turns.length) input.current?.focus();
  }, [busy]);

  async function send(text: string, retry = false) {
    if (request.current || !text.trim()) return;
    const prior = turns.filter(turn => turn.status === "complete");
    if (prior.length >= 9) { setError("Conversation limit reached. Clear chat to start a new conversation."); return; }
    const id = crypto.randomUUID(), abort = new AbortController();
    request.current = abort;
    setBusy(true); setError(""); setPrompt(""); setActivity("Connecting to the case-bound assistant.");
    setTurns([...turns.slice(0, retry ? -1 : undefined), { id, prompt: text, answer: "", status: "streaming" }]);
    let finished = false, answer = "", traceId = "";
    const update = (patch: Partial<Turn>) => {
      if (mounted.current) setTurns(current => current.map(turn => turn.id === id ? { ...turn, ...patch } : turn));
    };
    try {
      const messages = [...prior.flatMap(turn => [
        { id: `${turn.id}-user`, role: "user", content: turn.prompt },
        { id: `${turn.id}-assistant`, role: "assistant", content: turn.answer },
      ]), { id: `${id}-user`, role: "user", content: text }];
      const body = JSON.stringify({ messages });
      if (new TextEncoder().encode(body).byteLength > 24_000) throw new Error("CONVERSATION_LIMIT_CLEAR_CHAT");
      const response = await fetch("/api/chat", {
        method: "POST", headers: { ...await authorizationHeaders(), "Content-Type": "application/json", "X-Benefits-Case": caseId },
        body, signal: AbortSignal.any([abort.signal, AbortSignal.timeout(185_000)]), cache: "no-store",
      });
      traceId = response.headers.get("x-benefits-trace") || "";
      if (!response.ok || !response.body) {
        throw new Error(response.status === 401 ? "SIGN_IN_REQUIRED" : response.status === 403 ? "CASE_ACCESS_DENIED" : "CHAT_SERVICE_UNAVAILABLE");
      }
      for await (const event of readChatEvents(response.body, caseId)) {
        if (abort.signal.aborted) throw new DOMException("Cancelled", "AbortError");
        if (event.type === "TEXT_MESSAGE_CONTENT") {
          answer += event.delta; update({ answer });
        } else if (event.type === "TOOL_CALL_START") {
          setActivity(`Checking ${event.toolCallName.replaceAll("_", " ")}. No decision is being recorded.`);
        } else if (event.type === "TOOL_CALL_END") {
          setActivity("Read-only check finished. Preparing the response.");
        } else if (event.type === "RUN_FINISHED") {
          finished = true;
        } else if (event.type === "RUN_ERROR") {
          throw new Error("CHAT_RUN_FAILED");
        }
      }
      if (!finished || !answer.trim()) throw new Error("CHAT_RESPONSE_INCOMPLETE");
      update({ status: "complete" });
      if (mounted.current) setActivity("Response complete. A human must make any clinical decision.");
    } catch (failure) {
      const cancelled = abort.signal.aborted;
      update({ status: cancelled ? "cancelled" : "failed" });
      if (mounted.current) {
        const code = failure instanceof Error && failure.message === "CONVERSATION_LIMIT_CLEAR_CHAT"
          ? "Conversation is too large. Clear chat before starting a new conversation."
          : "Chat did not finish. Refresh the case before retrying; partial text is not a completed response.";
        setError(cancelled ? "Chat cancelled. Partial text is not a completed response." : `${code}${traceId ? ` Trace ${traceId}` : ""}`);
        setActivity(cancelled ? "Chat cancelled. Nothing is replayed automatically." : "Chat unavailable. No automatic retry.");
      }
    } finally {
      request.current = null;
      if (mounted.current) setBusy(false);
    }
  }

  function submit(event: FormEvent) { event.preventDefault(); void send(prompt.trim()); }
  const last = turns.at(-1);
  return <section className="case-chat" aria-label="Case-bound assistant chat">
    <p className="small">Synthetic evidence only. Read-only chat; decisions stay in the reviewer panel. Chat is kept only in this open panel and clears when closed or the case changes.</p>
    <div ref={history} className="chat-history" role="log" aria-label="Chat conversation" aria-live="off" tabIndex={0}
      onScroll={() => { const element = history.current; if (element) nearBottom.current = element.scrollHeight - element.scrollTop - element.clientHeight < 60; }}>
      {!turns.length && <p>Ask about intake completeness, criteria evidence or case status.</p>}
      {turns.map(turn => <article key={turn.id}>
        <h3>You</h3><p className="chat-text">{turn.prompt}</p>
        <h3>Assistant</h3><p className="chat-text">{turn.answer || (turn.status === "streaming" ? "Waiting for response…" : "No completed response.")}</p>
        {turn.status !== "complete" && turn.status !== "streaming" && <p className="small">Incomplete / {turn.status}. Not included in subsequent conversation context.</p>}
      </article>)}
    </div>
    <p role="status" aria-live="polite">{activity}</p>
    {error && <p role="alert">{error}</p>}
    <form onSubmit={submit}>
      <label htmlFor="case-chat-message">Case-bound chat message</label>
      <textarea id="case-chat-message" ref={input} rows={3} maxLength={2000} value={prompt}
        onChange={event => setPrompt(event.target.value)} disabled={busy} aria-describedby="chat-keyboard-help" />
      <p id="chat-keyboard-help" className="small">Enter adds a line. Tab to Send message, then press Enter to send. Maximum 2,000 characters.</p>
      <div className="chat-actions">
        <button type="submit" disabled={busy || !prompt.trim()}>Send message</button>
        {busy && <button type="button" className="secondary" onClick={() => request.current?.abort()}>Cancel chat response</button>}
        {!busy && last && ["failed", "cancelled"].includes(last.status) &&
          <button type="button" className="secondary" onClick={() => void send(last.prompt, true)}>Retry last message</button>}
        <button type="button" className="secondary" disabled={busy || !turns.length} onClick={() => {
          setTurns([]); setError(""); setActivity("Chat cleared. No conversation is stored on the server."); input.current?.focus();
        }}>Clear chat</button>
      </div>
    </form>
  </section>;
}
