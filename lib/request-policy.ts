type JsonBody = { text?: string; value?: unknown };

function denied(code: string, status: number) {
  return Response.json({ error: { code, traceId: crypto.randomUUID() } }, { status });
}

function boundedShape(root: unknown) {
  const pending = [{ value: root, depth: 0 }];
  let nodes = 0;
  while (pending.length) {
    const { value, depth } = pending.pop()!;
    if (++nodes > 4096 || depth > 24) return false;
    if (typeof value === "string" && value.length > 16_000) return false;
    if (value !== null && typeof value === "object") {
      const children = Object.values(value);
      if (children.length > 128) return false;
      for (const child of children) pending.push({ value: child, depth: depth + 1 });
    }
  }
  return true;
}

export async function readBoundedJson(request: Request, limit = 32_000): Promise<JsonBody | Response> {
  const encoding = request.headers.get("content-encoding");
  if (encoding && encoding.toLowerCase() !== "identity") return denied("COMPRESSED_REQUEST_DENIED", 415);
  if (request.method !== "POST") return {};
  const length = request.headers.get("content-length");
  if (length !== null && (!/^\d+$/.test(length) || !Number.isSafeInteger(Number(length)))) {
    return denied("INVALID_CONTENT_LENGTH", 400);
  }
  if (length !== null && Number(length) > limit) return denied("REQUEST_LIMIT", 413);
  if (request.headers.get("content-type")?.split(";")[0].trim().toLowerCase() !== "application/json") {
    return denied("JSON_REQUIRED", 415);
  }
  if (!request.body) return denied("INVALID_JSON", 400);

  const reader = request.body.getReader();
  const buffer = new Uint8Array(limit);
  let size = 0;
  let timedOut = false;
  const cancel = () => {
    void reader.cancel().catch((error: unknown) => {
      console.warn("Request body cancellation failed", { type: error instanceof Error ? error.name : "unknown" });
    });
  };
  const timer = setTimeout(() => { timedOut = true; cancel(); }, 10_000);
  request.signal.addEventListener("abort", cancel, { once: true });
  try {
    while (true) {
      if (request.signal.aborted) {
        cancel();
        return denied("REQUEST_INTERRUPTED", 408);
      }
      const { done, value } = await reader.read();
      if (timedOut || request.signal.aborted) return denied("REQUEST_INTERRUPTED", 408);
      if (done) break;
      if (size + value.byteLength > limit) {
        cancel();
        return denied("REQUEST_LIMIT", 413);
      }
      buffer.set(value, size);
      size += value.byteLength;
    }
    let text: string;
    let value: unknown;
    try {
      text = new TextDecoder("utf-8", { fatal: true }).decode(buffer.subarray(0, size));
      value = JSON.parse(text);
    } catch {
      return denied("INVALID_JSON", 400);
    }
    if (!boundedShape(value)) return denied("REQUEST_SHAPE_LIMIT", 422);
    return { text, value };
  } catch (error) {
    console.warn("Request body read failed", { type: error instanceof Error ? error.name : "unknown" });
    return denied("REQUEST_INTERRUPTED", 400);
  } finally {
    clearTimeout(timer);
    request.signal.removeEventListener("abort", cancel);
    reader.releaseLock();
  }
}
