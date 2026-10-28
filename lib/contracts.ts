import { z } from "zod";

export const ActivitySchema = z.object({
  activity: z.enum(["intake_completeness", "criteria_evidence", "case_status", "reviewer_decision_requested",
    "missing_information_draft", "member_update_draft", "employer_aggregate"]),
  version: z.literal("1.0"), caseId: z.string(), traceId: z.string(),
  data: z.record(z.string(), z.union([z.string(), z.number(), z.array(z.string())])),
}).strict();

export type Source = { id: string; version: string; as_of: string; title: string; passage: string };
export type Field = { value: string | null; confidence: number; source: string };
export type Brief = {
  version: number; criteria_version: string | null; gaps: string[]; conflicts: string[];
  items: { criterion: string; state: string; explanation: string; sources: Source[] }[];
};
export type Case = {
  id: string; state: string; version: number; message: string; next_owner: string; expiry: string | null;
  scenario?: string; member?: string;
  missing_information_draft?: string | null;
  member360?: { name: string; plan: string; coverage: string; fields: Record<string, Field>; claims: { id: string; therapy: string; date: string }[] };
  brief?: Brief | null;
  decision?: { outcome: string; reason: string; reviewer: string; timestamp: string; brief_version: number } | null;
  timeline: { id: number; event: string; created: string; trace: string }[];
  update_draft: string;
};
export type Session = { id: string; role: "reviewer" | "contact" | "employer"; employer: string; mode: string;
  features: Record<"chat" | "intake" | "evidence" | "renewal" | "employer" | "activities", boolean> };
export type Aggregate = {
  dataset: string; as_of: string; suppression: string;
  rows: { period: string; members: number | null; specialty_utilizers: number | null; cost: number | null }[];
};

export async function api<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`/api/backend/${path}`, {
    method: body === undefined ? "GET" : "POST", cache: "no-store",
    headers: { "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body), signal,
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(`${error.error?.code || "REQUEST_FAILED"} · ${error.error?.traceId || response.status}`);
  }
  return response.json();
}
