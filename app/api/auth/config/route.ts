import { publicAuthConfiguration } from "@/lib/entra-server";
import { safeError } from "@/lib/server";

export const dynamic = "force-dynamic";

export function GET() {
  try {
    return Response.json(publicAuthConfiguration(), { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    console.error("Authentication configuration unavailable", { type: error instanceof Error ? error.name : "unknown" });
    return safeError("AUTH_CONFIGURATION_INVALID");
  }
}
