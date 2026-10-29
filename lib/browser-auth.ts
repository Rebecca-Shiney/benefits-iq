"use client";

import { BrowserCacheLocation, LogLevel, PublicClientApplication } from "@azure/msal-browser";
import { z } from "zod";

const Configuration = z.discriminatedUnion("profile", [
  z.object({ profile: z.literal("local") }),
  z.object({ profile: z.literal("showcase") }),
  z.object({
    profile: z.literal("starter"), tenantId: z.uuid(), clientId: z.uuid(),
    scope: z.string().min(1), origin: z.url(),
  }),
]);
type BrowserAuth = { config: z.infer<typeof Configuration>; client: PublicClientApplication | null };
let initialization: Promise<BrowserAuth> | undefined;

export async function initializeAuth(): Promise<BrowserAuth> {
  initialization ??= (async () => {
    const response = await fetch("/api/auth/config", { cache: "no-store" });
    if (!response.ok) throw new Error("AUTH_CONFIGURATION_UNAVAILABLE");
    const config = Configuration.parse(await response.json());
    if (config.profile !== "starter") return { config, client: null };
    if (config.origin !== window.location.origin) throw new Error("AUTH_ORIGIN_MISMATCH");
    const client = new PublicClientApplication({
      auth: {
        clientId: config.clientId, authority: `https://login.microsoftonline.com/${config.tenantId}`,
        redirectUri: `${config.origin}/auth`, postLogoutRedirectUri: config.origin,
      },
      cache: {
        cacheLocation: BrowserCacheLocation.MemoryStorage,
      },
      system: { loggerOptions: {
        piiLoggingEnabled: false, logLevel: LogLevel.Error,
        loggerCallback: () => console.error("Microsoft Entra browser authentication error."),
      } },
    });
    await client.initialize();
    return { config, client };
  })();
  try {
    return await initialization;
  } catch (error) {
    initialization = undefined;
    throw error;
  }
}

export async function signIn() {
  const { config, client } = await initializeAuth();
  if (config.profile !== "starter" || !client) throw new Error("ENTRA_LOGIN_NOT_CONFIGURED");
  const result = await client.loginPopup({ scopes: [config.scope], prompt: "select_account" });
  if (!result.account) throw new Error("ENTRA_ACCOUNT_REQUIRED");
  client.setActiveAccount(result.account);
}

export async function signOut() {
  const { client } = await initializeAuth();
  if (client) await client.logoutPopup({ account: client.getActiveAccount() });
}

export async function authorizationHeaders(): Promise<Record<string, string>> {
  const { config, client } = await initializeAuth();
  if (config.profile !== "starter") return {};
  const account = client?.getActiveAccount();
  if (!client || !account) throw new Error("ENTRA_SIGN_IN_REQUIRED");
  const result = await client.acquireTokenSilent({ account, scopes: [config.scope] });
  return { Authorization: `Bearer ${result.accessToken}` };
}
