import { NextRequest } from "next/server";
import { cookies } from "next/headers";
import { demoUsers, sameOrigin, signSession, safeError } from "@/lib/server";
import { readBoundedJson } from "@/lib/request-policy";

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return safeError("ORIGIN_DENIED", 403);
  const input = await readBoundedJson(request, 1024);
  if (input instanceof Response) return input;
  const body = input.value;
  if (!body || typeof body !== "object" || !("user" in body) || typeof body.user !== "string" || !demoUsers.includes(body.user)) {
    return safeError("UNKNOWN_DEMO_IDENTITY", 422);
  }
  (await cookies()).set("benefits-demo-session", signSession(body.user), {
    httpOnly: true, sameSite: "strict", path: "/", maxAge: 8 * 60 * 60,
  });
  return Response.json({ mode: "local-synthetic-demo" });
}
