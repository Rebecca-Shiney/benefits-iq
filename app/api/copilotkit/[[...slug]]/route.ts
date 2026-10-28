import { NextRequest } from "next/server";
import { CopilotRuntime, createCopilotRuntimeHandler } from "@copilotkit/runtime/v2";
import { HttpAgent } from "@ag-ui/client";
import { identity, sameOrigin, serviceHeaders, serviceUrl, safeError } from "@/lib/server";
import { StatelessRunner } from "@/lib/stateless-runner";

async function handle(request: NextRequest) {
  if (!sameOrigin(request)) return safeError("ORIGIN_DENIED", 403);
  const user = await identity();
  if (!user) return safeError("DEMO_SESSION_REQUIRED", 401);
  const caseId = request.headers.get("x-benefits-case") || "";
  if (!/^SYN-CASE-\d{3}$/.test(caseId)) return safeError("CASE_REQUIRED", 422);
  try {
    const auth = await fetch(`${serviceUrl()}/api/cases/${caseId}`, {
      headers: serviceHeaders(user), cache: "no-store", signal: AbortSignal.timeout(5000),
    });
    if (!auth.ok) return safeError("CASE_ACCESS_DENIED", auth.status);
    const live = process.env.BENEFITS_MODE === "live";
    const runtime = new CopilotRuntime({
      runner: new StatelessRunner(),
      agents: {
        health_benefits_orchestrator: new HttpAgent({
          url: `${serviceUrl()}/${live ? "ag-ui-live" : "ag-ui"}`,
          headers: serviceHeaders(user, caseId),
        }),
      },
    });
    const handler = createCopilotRuntimeHandler({ runtime, basePath: "/api/copilotkit",
      cors: { origin: process.env.BENEFITS_APP_ORIGIN || request.headers.get("origin") || request.nextUrl.origin, credentials: true } });
    return handler(request);
  } catch (error) {
    console.error("Copilot runtime unavailable", { type: error instanceof Error ? error.name : "unknown" });
    return safeError("AGENT_RUNTIME_UNAVAILABLE");
  }
}

export const GET = handle;
export const POST = handle;
