import { z } from "zod";

const Id = z.string().regex(/^[a-zA-Z0-9_-]{1,128}$/);
export const ChatRequest = z.object({
  messages: z.array(z.object({
    id: Id, role: z.enum(["user", "assistant"]), content: z.string().min(1).max(16_000),
  }).strict()).min(1).max(19),
}).strict().refine(({ messages }) => messages.every((message, index) =>
  message.role === (index % 2 === 0 ? "user" : "assistant")) && messages.at(-1)?.role === "user");

const Tool = z.enum([
  "get_case_status", "read_intake_completeness", "read_criteria_version",
  "extract_authorization_form", "retrieve_drug_criteria", "get_expiring_authorizations",
]);
const Event = z.discriminatedUnion("type", [
  z.object({ type: z.literal("RUN_STARTED"), threadId: Id, runId: Id }),
  z.object({ type: z.literal("RUN_FINISHED"), threadId: Id, runId: Id }),
  z.object({ type: z.literal("RUN_ERROR") }),
  z.object({ type: z.literal("TEXT_MESSAGE_START"), messageId: Id, role: z.literal("assistant") }),
  z.object({ type: z.literal("TEXT_MESSAGE_CONTENT"), messageId: Id, delta: z.string().max(8000) }),
  z.object({ type: z.literal("TEXT_MESSAGE_END"), messageId: Id }),
  z.object({ type: z.literal("TOOL_CALL_START"), toolCallId: Id, toolCallName: Tool }),
  z.object({ type: z.literal("TOOL_CALL_ARGS"), toolCallId: Id }),
  z.object({ type: z.literal("TOOL_CALL_END"), toolCallId: Id }),
  z.object({ type: z.literal("TOOL_CALL_RESULT"), toolCallId: Id }),
  z.object({ type: z.enum(["STEP_STARTED", "STEP_FINISHED"]) }),
  z.object({ type: z.enum(["STATE_SNAPSHOT", "STATE_DELTA", "MESSAGES_SNAPSHOT", "RAW", "CUSTOM"]) }),
]);
export type ChatEvent = z.infer<typeof Event>;
export const CHAT_LIMITS = { bytes: 262_144, frame: 32_000, events: 2048, text: 16_000 } as const;

export class ChatProtocolError extends Error {
  constructor() { super("CHAT_STREAM_INVALID"); }
}

export async function* readChatEvents(body: ReadableStream<Uint8Array>, threadId: string): AsyncGenerator<ChatEvent> {
  const reader = body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: true });
  let buffer = "", bytes = 0, events = 0, text = 0, started = false, terminal = false, runId = "";
  const messages = new Set<string>(), knownMessages = new Set<string>(), tools = new Set<string>(), openTools = new Set<string>();

  function parse(frame: string): ChatEvent | null {
    const data = frame.split("\n").filter(line => line.startsWith("data:")).map(line => line.slice(5).trimStart()).join("\n");
    if (!data) return null;
    if (++events > CHAT_LIMITS.events) throw new ChatProtocolError();
    let value: unknown;
    try { value = JSON.parse(data); } catch { throw new ChatProtocolError(); }
    const result = Event.safeParse(value);
    if (!result.success) throw new ChatProtocolError();
    const event = result.data;
    if (event.type === "RUN_ERROR") {
      terminal = true;
      return event;
    }
    if (event.type === "RUN_STARTED") {
      if (started || event.threadId !== threadId) throw new ChatProtocolError();
      started = true; runId = event.runId;
      return event;
    }
    if (!started) throw new ChatProtocolError();
    if (event.type === "RUN_FINISHED") {
      if (event.threadId !== threadId || event.runId !== runId || messages.size || openTools.size) throw new ChatProtocolError();
      terminal = true;
    } else if (event.type === "TEXT_MESSAGE_START") {
      if (knownMessages.has(event.messageId) || knownMessages.size >= 16) throw new ChatProtocolError();
      messages.add(event.messageId); knownMessages.add(event.messageId);
    } else if (event.type === "TEXT_MESSAGE_CONTENT") {
      text += event.delta.length;
      if (!messages.has(event.messageId) || text > CHAT_LIMITS.text) throw new ChatProtocolError();
    } else if (event.type === "TEXT_MESSAGE_END") {
      if (!messages.delete(event.messageId)) throw new ChatProtocolError();
    } else if (event.type === "TOOL_CALL_START") {
      if (tools.has(event.toolCallId) || tools.size >= 16) throw new ChatProtocolError();
      tools.add(event.toolCallId); openTools.add(event.toolCallId);
    } else if (event.type === "TOOL_CALL_ARGS" || event.type === "TOOL_CALL_RESULT") {
      if (!tools.has(event.toolCallId)) throw new ChatProtocolError();
      return null;
    } else if (event.type === "TOOL_CALL_END") {
      if (!openTools.delete(event.toolCallId)) throw new ChatProtocolError();
    } else if (!["STEP_STARTED", "STEP_FINISHED"].includes(event.type)) {
      // Never forward model state, snapshots, raw events, tool arguments or results.
      return null;
    }
    return event;
  }

  try {
    while (!terminal) {
      const { value, done } = await reader.read();
      if (done) {
        buffer += decoder.decode();
        if (buffer.trim()) throw new ChatProtocolError();
        break;
      }
      bytes += value.byteLength;
      if (bytes > CHAT_LIMITS.bytes) throw new ChatProtocolError();
      try { buffer += decoder.decode(value, { stream: true }); } catch { throw new ChatProtocolError(); }
      // CRLF may be split across chunks; retain a trailing CR for the next chunk.
      buffer = buffer.replace(/\r\n/g, "\n");
      let end: number;
      while ((end = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, end);
        buffer = buffer.slice(end + 2);
        if (frame.length > CHAT_LIMITS.frame) throw new ChatProtocolError();
        const event = parse(frame);
        if (event) yield event;
        if (terminal) return;
      }
      if (buffer.length > CHAT_LIMITS.frame) throw new ChatProtocolError();
    }
    if (!terminal) throw new ChatProtocolError();
  } finally {
    try { await reader.cancel(); }
    catch (error) { console.warn("Chat stream cancellation failed", { type: error instanceof Error ? error.name : "unknown" }); }
    reader.releaseLock();
  }
}
