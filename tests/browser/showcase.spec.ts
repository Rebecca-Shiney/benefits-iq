import { expect, test, type Page } from "@playwright/test";

async function showcasePresentation(page: Page, view = "reviewer-a", caseId = "SYN-CASE-001") {
  // Browser presentation tests reuse the loopback backend; managed-caller validation has separate signed-token tests.
  await page.route("**/api/auth/config", route => route.fulfill({ json: { profile: "showcase" } }));
  await page.route("**/api/backend/session", async route => {
    const response = await route.fetch();
    const data = await response.json();
    await route.fulfill({ response, json: { ...data, id: `anonymous-demo:${data.id}`, profile: "showcase" } });
  });
  await page.route(/\/api\/backend\/cases\/SYN-CASE-\d{3}$/, async route => {
    const response = await route.fetch();
    const data = await response.json();
    const fields = Object.fromEntries(Object.entries(data.member360?.fields || {}).map(([name, value]) => [
      name, [(value as { value: string | null }).value || ""],
    ]));
    await route.fulfill({ response, json: { ...data, showcase_fields: fields } });
  });
  await page.goto("/");
  await page.getByLabel("PUBLIC DEMO VIEW", { exact: true }).selectOption(view);
  await page.getByRole("button", { name: "Open workspace" }).click();
  await page.getByRole("button", { name: new RegExp(`^${caseId}`) }).click();
}

test("public presentation clearly distinguishes selectable views from authenticated access", async ({ page }) => {
  await showcasePresentation(page);
  const banner = page.getByRole("region", { name: "Public showcase limitations" });
  await expect(banner).toContainText("NO SIGN-IN");
  await expect(banner).toContainText("Anyone can switch every demo view");
  await expect(banner).toContainText("Never enter health or personal data");
  await expect(page.getByRole("button", { name: "Sign in with Microsoft Entra" })).toHaveCount(0);
  await expect(page.locator(".workspace-meta")).toContainText("anonymous-demo:reviewer-a");
  await page.getByLabel("Demo workspace").selectOption("contact-a");
  await page.getByRole("button", { name: "Switch workspace" }).click();
  await expect(page.getByRole("heading", { name: "Member support", exact: true })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Case sections" })).not.toContainText("decision");
  await page.getByLabel("Demo workspace").selectOption("employer-b");
  await page.getByRole("button", { name: "Switch workspace" }).click();
  await expect(page.getByRole("heading", { name: "Employer portfolio" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Specialty utilization trends" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Case sections" })).toHaveCount(0);
});

test("public forms use finite choices and communication is preview only", async ({ page }) => {
  await showcasePresentation(page, "reviewer-b", "SYN-CASE-004");
  const tabs = page.getByRole("navigation", { name: "Case sections" });
  await tabs.getByRole("button", { name: "intake", exact: true }).click();
  await expect(page.getByLabel("prescriber", { exact: false })).toHaveJSProperty("tagName", "SELECT");
  await expect(page.locator("textarea")).toHaveCount(0);
  await tabs.getByRole("button", { name: "decision", exact: true }).click();
  await expect(page.getByLabel("Rationale", { exact: true })).toHaveJSProperty("tagName", "SELECT");
  await expect(page.getByRole("button", { name: "Record my decision" })).toBeDisabled();
  await tabs.getByRole("button", { name: "status", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Built-in synthetic communication preview" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Confirm local draft (no external send)" })).toHaveCount(0);
  await expect(page.locator("textarea")).toHaveCount(0);
});

test("public chat presets remain keyboard accessible and send no conversation history", async ({ page }) => {
  const requests: { messages: { role: string; content: string }[] }[] = [];
  page.on("request", request => { if (request.url().endsWith("/api/chat")) requests.push(request.postDataJSON()); });
  await showcasePresentation(page, "reviewer-b", "SYN-CASE-004");
  await page.getByRole("button", { name: "Open case-bound chat" }).click();
  const chat = page.getByRole("region", { name: "Case-bound assistant chat" });
  const prompt = chat.getByLabel("Case-bound chat message", { exact: true });
  await expect(prompt).toHaveJSProperty("tagName", "SELECT");
  await expect(chat).toContainText("without sending conversation history");
  for (const question of ["Current status", "Which criteria version applies?"]) {
    await prompt.selectOption(question);
    await prompt.focus();
    await prompt.press("Tab");
    await expect(chat.getByRole("button", { name: "Send message", exact: true })).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(chat.getByRole("status")).toContainText("Response complete");
    await expect(prompt).toBeFocused();
  }
  expect(requests).toHaveLength(2);
  expect(requests.every(request => request.messages.length === 1 && request.messages[0].role === "user")).toBe(true);
});
