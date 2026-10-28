import { NextRequest } from "next/server";
import { cookies } from "next/headers";
import { demoUsers, sameOrigin, signSession, safeError } from "@/lib/server";

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return safeError("ORIGIN_DENIED", 403);
  const body: unknown = await request.json();
  if (!body || typeof body !== "object" || !("user" in body) || typeof body.user !== "string" || !demoUsers.includes(body.user)) {
    return safeError("UNKNOWN_DEMO_IDENTITY", 422);
  }
  (await cookies()).set("benefits-demo-session", signSession(body.user), {
    httpOnly: true, sameSite: "strict", path: "/", maxAge: 8 * 60 * 60,
  });
  return Response.json({ mode: "local-synthetic-demo" });
}
