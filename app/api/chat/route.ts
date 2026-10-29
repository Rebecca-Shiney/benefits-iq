import { NextRequest } from "next/server";
import { identity, sameOrigin, serviceHeaders, serviceUrl, safeError, starterMode } from "@/lib/server";
import { readBoundedJson } from "@/lib/request-policy";
import { ChatRequest, readChatEvents } from "@/lib/chat-protocol";

export async function POST(request: NextRequest) {
  const abort = new AbortController();
  try {
    if (!sameOrigin(request)) return safeError("ORIGIN_DENIED", 403);
    const user = await identity(request);
    if (!user) return safeError(starterMode() ? "ENTRA_SESSION_REQUIRED" : "DEMO_SESSION_REQUIRED", 401);
    const caseId = request.headers.get("x-benefits-case") || "";
    if (!/^SYN-CASE-\d{3}$/.test(caseId)) return safeError("CASE_REQUIRED", 422);
    const input = await readBoundedJson(request, 24_000);
    if (input instanceof Response) return input;
    const parsed = ChatRequest.safeParse(input.value);
    if (!parsed.success) return safeError("INVALID_CHAT_REQUEST", 422);
    const headers = await serviceHeaders(user, caseId);
    const signal = AbortSignal.any([request.signal, abort.signal, AbortSignal.timeout(180_000)]);
    const access = await fetch(`${serviceUrl()}/api/cases/${caseId}`, { headers, signal, cache: "no-store" });
    await access.body?.cancel();
    if (!access.ok) return safeError("CASE_ACCESS_DENIED", access.status);
    const live = starterMode() || process.env.BENEFITS_MODE === "live";
    const response = await fetch(`${serviceUrl()}/${live ? "ag-ui-live" : "ag-ui"}`, {
      method: "POST", headers: { ...headers, Accept: "text/event-stream" }, signal, cache: "no-store",
      body: JSON.stringify({
        threadId: caseId, runId: crypto.randomUUID(), messages: parsed.data.messages,
        tools: [], context: [], state: {}, forwardedProps: {},
      }),
    });
    if (!response.ok || !response.body || !response.headers.get("content-type")?.startsWith("text/event-stream")) {
      await response.body?.cancel();
      return safeError("CHAT_SERVICE_UNAVAILABLE", response.ok ? 502 : response.status);
    }
    const events = readChatEvents(response.body, caseId);
    const encoder = new TextEncoder();
    const traceId = crypto.randomUUID();
    let ended = false;
    const body = new ReadableStream<Uint8Array>({
      async pull(controller) {
        if (ended) return;
        try {
          const next = await events.next();
          if (next.done) { ended = true; controller.close(); return; }
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(next.value)}\n\n`));
        } catch (error) {
          console.error("Chat stream failed", { traceId, type: error instanceof Error ? error.name : "unknown" });
          ended = true;
          if (!abort.signal.aborted && !request.signal.aborted) {
            controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: "RUN_ERROR" })}\n\n`));
            controller.close();
          }
          abort.abort();
        }
      },
      async cancel() {
        ended = true; abort.abort();
        await events.return(undefined);
      },
    });
    return new Response(body, { headers: {
      "Content-Type": "text/event-stream", "Cache-Control": "no-store",
      "X-Accel-Buffering": "no", "X-Benefits-Trace": traceId,
    } });
  } catch (error) {
    abort.abort();
    console.error("Chat service unavailable", { type: error instanceof Error ? error.name : "unknown" });
    return safeError("CHAT_SERVICE_UNAVAILABLE");
  }
}
