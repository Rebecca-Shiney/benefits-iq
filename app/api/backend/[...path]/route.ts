import { NextRequest } from "next/server";
import { identity, sameOrigin, serviceHeaders, serviceUrl, safeError } from "@/lib/server";

async function handle(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  if (!sameOrigin(request)) return safeError("ORIGIN_DENIED", 403);
  const user = await identity();
  if (!user) return safeError("DEMO_SESSION_REQUIRED", 401);
  const { path } = await context.params;
  if (!path.every((p) => /^[a-zA-Z0-9_-]+$/.test(p))) return safeError("INVALID_PATH", 422);
  const length = Number(request.headers.get("content-length") || 0);
  if (length > 32_000) return safeError("REQUEST_LIMIT", 413);
  try {
    const body = request.method === "POST" ? await request.text() : undefined;
    if (body && body.length > 32_000) return safeError("REQUEST_LIMIT", 413);
    const response = await fetch(`${serviceUrl()}/api/${path.join("/")}${request.nextUrl.search}`, {
      method: request.method, headers: serviceHeaders(user), body,
      signal: AbortSignal.any([request.signal, AbortSignal.timeout(60_000)]), cache: "no-store",
    });
    return new Response(response.body, {
      status: response.status,
      headers: { "Content-Type": response.headers.get("content-type") || "application/json", "Cache-Control": "no-store" },
    });
  } catch (error) {
    console.error("Benefits service connection failed", { type: error instanceof Error ? error.name : "unknown" });
    return safeError("SERVICE_UNAVAILABLE");
  }
}

export const GET = handle;
export const POST = handle;
