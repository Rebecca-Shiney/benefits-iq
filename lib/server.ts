import "server-only";
import { createHmac, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";
import { NextRequest } from "next/server";

export const demoUsers = ["reviewer-a", "reviewer-b", "contact-a", "employer-a", "employer-b"];

function secret() {
  const value = process.env.BENEFITS_SERVICE_SECRET;
  if (!value || value.length < 32) throw new Error("BENEFITS_SERVICE_SECRET must contain at least 32 characters.");
  return value;
}

function signature(value: string) {
  return createHmac("sha256", secret()).update(value).digest("hex");
}

export function signSession(user: string) {
  const payload = `${user}.${Date.now() + 8 * 60 * 60 * 1000}`;
  return `${payload}.${signature(payload)}`;
}

export async function identity() {
  const token = (await cookies()).get("benefits-demo-session")?.value;
  if (!token) return null;
  const [user, expiry, sig] = token.split(".");
  if (!demoUsers.includes(user) || !expiry || !sig || Number(expiry) < Date.now()) return null;
  const expected = signature(`${user}.${expiry}`);
  if (sig.length !== expected.length || !timingSafeEqual(Buffer.from(sig), Buffer.from(expected))) return null;
  return user;
}

export function sameOrigin(request: NextRequest) {
  const origin = request.headers.get("origin");
  const expected = process.env.BENEFITS_APP_ORIGIN || `${request.nextUrl.protocol}//${request.headers.get("host")}`;
  return !origin || origin === expected;
}

export function serviceHeaders(user: string, caseId?: string) {
  return {
    Authorization: `Bearer ${secret()}`,
    "X-Benefits-User": user,
    ...(caseId ? { "X-Benefits-Case": caseId } : {}),
    "Content-Type": "application/json",
  };
}

export function serviceUrl() {
  return process.env.BENEFITS_SERVICE_URL || "http://127.0.0.1:8000";
}

export function safeError(code: string, status = 503) {
  return Response.json({ error: { code, traceId: crypto.randomUUID() } }, { status });
}
