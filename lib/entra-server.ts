import "server-only";
import { ManagedIdentityCredential } from "@azure/identity";
import { createRemoteJWKSet, errors, jwtVerify } from "jose";
import { z } from "zod";

const Binding = z.object({
  role: z.enum(["reviewer", "contact", "employer"]),
  employer: z.enum(["SYN-EMP-A", "SYN-EMP-B"]),
}).strict();
const Configuration = z.object({
  tenant: z.uuid(), api: z.uuid(), spa: z.uuid(), runtime: z.uuid(),
  origin: z.url(), bindings: z.record(z.uuid(), Binding),
});
type EntraConfiguration = z.infer<typeof Configuration>;
export type CloudIdentity = { id: string; authorization: string };
let cached: EntraConfiguration | undefined;
let keys: ReturnType<typeof createRemoteJWKSet> | undefined;
let credential: ManagedIdentityCredential | undefined;

export function starterMode() {
  const profile = process.env.BENEFITS_PROFILE || "local";
  if (profile !== "local" && profile !== "starter") throw new Error("PROFILE_NOT_IMPLEMENTED");
  return profile === "starter";
}

export function entraConfiguration() {
  if (!cached) {
    const raw = process.env.BENEFITS_IDENTITY_BINDINGS || "";
    if (raw.length > 65_536) throw new Error("ENTRA_CONFIGURATION_INVALID");
    const result = Configuration.safeParse({
      tenant: process.env.BENEFITS_TENANT_ID, api: process.env.BENEFITS_API_CLIENT_ID,
      spa: process.env.BENEFITS_SPA_CLIENT_ID, runtime: process.env.BENEFITS_RUNTIME_CLIENT_ID,
      origin: process.env.BENEFITS_APP_ORIGIN, bindings: JSON.parse(raw),
    });
    if (!result.success || !Object.keys(result.data.bindings).length || Object.keys(result.data.bindings).length > 128) {
      throw new Error("ENTRA_CONFIGURATION_INVALID");
    }
    if (new URL(result.data.origin).protocol !== "https:") throw new Error("HTTPS_APP_ORIGIN_REQUIRED");
    cached = result.data;
  }
  return cached;
}

export async function cloudIdentity(authorization: string): Promise<CloudIdentity | null> {
  const config = entraConfiguration();
  if (!authorization.startsWith("Bearer ") || authorization.length > 16_384) return null;
  keys ??= createRemoteJWKSet(new URL(`https://login.microsoftonline.com/${config.tenant}/discovery/v2.0/keys`), {
    timeoutDuration: 5000, cooldownDuration: 30_000, cacheMaxAge: 3_600_000,
  });
  try {
    const { payload } = await jwtVerify(authorization.slice(7), keys, {
      issuer: `https://login.microsoftonline.com/${config.tenant}/v2.0`, audience: config.api,
      algorithms: ["RS256"], clockTolerance: 30,
      requiredClaims: ["exp", "iat", "nbf", "iss", "aud", "tid", "oid", "ver"],
    });
    if (payload.tid !== config.tenant || payload.ver !== "2.0" || payload.azp !== config.spa ||
        typeof payload.oid !== "string" || typeof payload.scp !== "string" ||
        !payload.scp.split(" ").includes("access_as_user")) return null;
    const binding = config.bindings[payload.oid.toLowerCase()];
    const role = binding && ({ reviewer: "Benefits.Reviewer", contact: "Benefits.Contact", employer: "Benefits.Employer" })[binding.role];
    if (!role || !Array.isArray(payload.roles) || !payload.roles.includes(role)) return null;
    return { id: payload.oid.toLowerCase(), authorization };
  } catch (error) {
    if (error instanceof errors.JOSEError && error.code !== "ERR_JWKS_TIMEOUT") {
      console.warn("Entra access denied", { type: error.name });
      return null;
    }
    throw error;
  }
}

export async function runtimeAuthorization() {
  const config = entraConfiguration();
  credential ??= new ManagedIdentityCredential({ clientId: config.runtime });
  const token = await credential.getToken(`api://${config.api}/.default`);
  if (!token) throw new Error("RUNTIME_TOKEN_UNAVAILABLE");
  return `Bearer ${token.token}`;
}

export function publicAuthConfiguration() {
  if (!starterMode()) return { profile: "local" as const };
  const config = entraConfiguration();
  return {
    profile: "starter" as const, tenantId: config.tenant, clientId: config.spa,
    scope: `api://${config.api}/access_as_user`, origin: new URL(config.origin).origin,
  };
}
