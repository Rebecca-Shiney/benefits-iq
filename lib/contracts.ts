import { z } from "zod";
import { authorizationHeaders } from "./browser-auth";

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
  showcase_fields?: Record<string, string[]>;
  missing_information_draft?: string | null;
  member360?: { name: string; member_id: string; plan: string; coverage: string; fields: Record<string, Field>; claims: { id: string; therapy: string; date: string }[] };
  brief?: Brief | null;
  decision?: { outcome: string; reason: string; reviewer: string; timestamp: string; brief_version: number } | null;
  timeline: { id: number; event: string; created: string; trace: string; actor?: string }[];
  update_draft: string;
};
export type Session = { id: string; role: "reviewer" | "contact" | "employer"; employer: string; mode: string;
  profile?: "local" | "starter" | "showcase";
  features: Record<"chat" | "intake" | "evidence" | "renewal" | "employer" | "activities", boolean> };
export type Aggregate = {
  dataset: string; as_of: string; suppression: string;
  rows: { period: string; members: number | null; specialty_utilizers: number | null; cost: number | null }[];
};
export type TaskKind = "verify_form" | "resolve_evidence" | "member_follow_up" | "renewal_review";
export type Task = {
  id: string; case_id: string; kind: TaskKind; role: "reviewer" | "contact"; title: string; team: string;
  state: "open" | "in_progress" | "done"; due: string; version: number; updated: string;
};
export type QueueItem = Pick<Case, "id" | "state" | "version" | "expiry"> & {
  display_name: string; member?: string; received: string; target: string; priority: "standard" | "priority";
  owner: string; channel: string; request_type: string; age_hours: number;
  target_state: "closed" | "overdue" | "due_soon" | "on_track"; open_tasks: number;
  missing_fields?: string[]; conflict?: boolean; source_gap?: boolean;
};
export type Employer = { id: string; name: string; plan: string; region: string };
export type Workbench = {
  as_of: string; employer: Employer; items: QueueItem[]; matched: number; states: string[];
  summary: { total: number; active: number; overdue: number; due_soon: number; unassigned: number;
    review_ready: number; open_tasks: number; intake_gaps?: number; source_gaps?: number; conflicts?: number };
  tasks: Task[]; target_note: string;
};
export type CaseOperations = {
  case_id: string; employer: Employer; received: string; target: string; priority: "standard" | "priority";
  owner: string; channel: string; tasks: Task[];
  outbox: { id: number; text: string; created: string }[];
  documents?: { id: string; title: string; kind: string; version: string | null; as_of: string | null;
    status: string; valid_until?: string | null; detail: string }[];
  missing_fields?: string[]; conflict?: boolean; source_gap?: boolean; verified_fields?: number; field_count?: number;
  owners?: { id: string; label: string }[];
};

export async function api<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`/api/backend/${path}`, {
    method: body === undefined ? "GET" : "POST", cache: "no-store",
    headers: { "Content-Type": "application/json", ...await authorizationHeaders() },
    body: body === undefined ? undefined : JSON.stringify(body), signal,
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(`${error.error?.code || "REQUEST_FAILED"} · ${error.error?.traceId || response.status}`);
  }
  return response.json();
}
