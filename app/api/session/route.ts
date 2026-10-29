import { NextRequest } from "next/server";
import { cookies } from "next/headers";
import { demoUsers, sameOrigin, signSession, safeError, starterMode, showcaseMode } from "@/lib/server";
import { readBoundedJson } from "@/lib/request-policy";

export async function POST(request: NextRequest) {
  if (starterMode()) return safeError("DEMO_AUTH_DISABLED", 404);
  if (!sameOrigin(request)) return safeError("ORIGIN_DENIED", 403);
  const input = await readBoundedJson(request, 1024);
  if (input instanceof Response) return input;
  const body = input.value;
  if (!body || typeof body !== "object" || !("user" in body) || typeof body.user !== "string" || !demoUsers.includes(body.user)) {
    return safeError("UNKNOWN_DEMO_IDENTITY", 422);
  }
  if (showcaseMode() && Object.keys(body).length !== 1) return safeError("SYNTHETIC_VIEW_ONLY", 422);
  (await cookies()).set("benefits-demo-session", showcaseMode() ? body.user : signSession(body.user), {
    httpOnly: true, secure: showcaseMode(), sameSite: "strict", path: "/", maxAge: 8 * 60 * 60,
  });
  return Response.json({ mode: showcaseMode() ? "public-anonymous-synthetic-showcase" : "local-synthetic-demo" });
}
