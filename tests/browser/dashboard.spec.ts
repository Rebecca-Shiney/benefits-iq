import { expect, test, type Page } from "@playwright/test";
import path from "node:path";

async function login(page: Page, persona = "reviewer-a") {
  await page.goto("/");
  await page.getByLabel("LOCAL DEMO PERSONA").selectOption(persona);
  await page.getByRole("button", { name: "Open workspace" }).click();
  await expect(page.getByRole("navigation", { name: "Operations views" })).toBeVisible();
}

async function selectCase(page: Page, id: string) {
  await page.getByRole("button", { name: new RegExp("^" + id) }).click();
  await expect(page.getByRole("heading", { name: id, exact: true })).toBeVisible();
}

test("queue search, status, owner, priority and sorting are usable", async ({ page }) => {
  await login(page);
  const queue = page.getByRole("complementary").filter({ has: page.getByRole("heading", { name: "Case queue", exact: true }) });
  await expect(queue.getByText("6 matching / 6 authorized")).toBeVisible();
  await page.getByLabel("Search cases").fill("Jordan");
  await expect(queue.getByText("1 matching / 6 authorized")).toBeVisible();
  await expect(queue.getByRole("button", { name: /^SYN-CASE-002/ })).toBeVisible();
  await page.getByLabel("Search cases").fill("missing-case");
  await expect(queue.getByText("No matching cases.", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Clear filters" }).click();
  await page.getByRole("combobox", { name: "Priority", exact: true }).selectOption("priority");
  await expect(queue.getByText("1 matching / 6 authorized")).toBeVisible();
  await expect(queue.getByRole("button", { name: /^SYN-CASE-003/ })).toBeVisible();
  await page.getByRole("button", { name: "Clear filters" }).click();
  await page.getByRole("combobox", { name: "Ownership", exact: true }).selectOption("unassigned");
  await expect(queue.getByText("2 matching / 6 authorized")).toBeVisible();
  await page.getByRole("button", { name: "Clear filters" }).click();
  await page.getByRole("combobox", { name: "Sort by" }).selectOption("newest");
  await expect(queue.getByRole("button", { name: /^SYN-CASE-/ }).first()).toContainText("SYN-CASE-010");
  await selectCase(page, "SYN-CASE-001");
  await page.getByRole("navigation", { name: "Case sections" }).getByRole("button", { name: "documents", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Documents & source freshness" })).toBeVisible();
  await page.getByText("Inspect local source context", { exact: true }).first().click();
  await expect(page.getByText("No PDF upload or OCR is implied.", { exact: false })).toBeVisible();
  await page.getByRole("navigation", { name: "Case sections" }).getByRole("button", { name: "decision", exact: true }).click();
  if (await page.getByRole("button", { name: "Record my decision" }).count()) {
    await expect(page.getByRole("button", { name: "Record my decision" })).toBeDisabled();
  }
});

test("routing and team task lifecycle persist without a clinical decision", async ({ page }) => {
  await login(page);
  await selectCase(page, "SYN-CASE-006");
  const before = await (await page.request.get("/api/backend/cases/SYN-CASE-006")).json();
  const original = await (await page.request.get("/api/backend/cases/SYN-CASE-006/operations")).json();
  await page.getByRole("combobox", { name: "Reviewer owner", exact: true }).selectOption("unassigned");
  await page.getByRole("button", { name: "Save routing" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Operational routing saved" })).toBeVisible();
  const routed = await (await page.request.get("/api/backend/cases/SYN-CASE-006/operations")).json();
  expect(routed.owner).toBe("unassigned");
  await page.getByRole("combobox", { name: "Reviewer owner", exact: true }).selectOption(original.owner);
  await page.getByRole("button", { name: "Save routing" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Operational routing saved" })).toBeVisible();
  await page.getByRole("navigation", { name: "Case sections" }).getByRole("button", { name: /^Tasks/ }).click();
  await page.getByRole("button", { name: "Start", exact: true }).click();
  await expect(page.locator(".task-list .state")).toHaveText("in progress");
  await page.getByRole("button", { name: "Complete", exact: true }).click();
  await expect(page.locator(".task-list .state")).toHaveText("done");
  await page.getByRole("button", { name: "Reopen", exact: true }).click();
  await expect(page.locator(".task-list .state")).toHaveText("open");
  await page.getByRole("button", { name: "Create task", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "OPEN_TASK_ALREADY_EXISTS" })).toBeVisible();
  const after = await (await page.request.get("/api/backend/cases/SYN-CASE-006")).json();
  expect(after.state).toBe(before.state);
  expect(after.decision).toBe(before.decision);
  await page.getByRole("navigation", { name: "Operations views" }).getByRole("button", { name: /^Team tasks/ }).click();
  await expect(page.getByRole("heading", { name: "Team tasks", exact: true })).toBeVisible();
});

test("contact view omits clinical data and supports streamed status", async ({ page }) => {
  await login(page, "contact-a");
  const sections = page.getByRole("navigation", { name: "Case sections" });
  await expect(sections.getByRole("button", { name: "evidence", exact: true })).toHaveCount(0);
  await expect(page.getByText("Avery Morgan", { exact: false })).toHaveCount(0);
  await sections.getByRole("button", { name: "status", exact: true }).click();
  await page.getByRole("button", { name: "Run status check" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Workflow saved." })).toBeVisible();
  const response = await page.request.get("/api/backend/workbench");
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(data.tasks.every((t: { role: string }) => t.role === "contact")).toBeTruthy();
  expect(JSON.stringify(data)).not.toContain("prescriber");
  expect((await page.request.get("/api/backend/cases/SYN-CASE-004/operations")).status()).toBe(403);
});

test("renewals and expired criteria open their actual authorized records", async ({ page }) => {
  await login(page, "reviewer-b");
  await page.getByRole("navigation", { name: "Operations views" }).getByRole("button", { name: /^Renewal watch/ }).click();
  await expect(page.locator(".renewal-item")).toHaveCount(2);
  await page.locator(".renewal-item").filter({ hasText: "SYN-CASE-012" }).getByRole("button", { name: "Open renewal" }).click();
  await expect(page.getByRole("heading", { name: "SYN-CASE-012", exact: true })).toBeVisible();
  await selectCase(page, "SYN-CASE-005");
  await expect(page.getByText("Missing or expired source.", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Sources", exact: true }).click();
  await expect(page.getByText("Not current evidence.", { exact: false })).toBeVisible();
  expect((await page.request.get("/api/backend/cases/SYN-CASE-001/operations")).status()).toBe(403);
});

test("employer portfolio has suppressed aggregates and no member operations", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("LOCAL DEMO PERSONA").selectOption("employer-a");
  await page.getByRole("button", { name: "Open workspace" }).click();
  await expect(page.getByRole("heading", { name: "Specialty utilization trends" })).toBeVisible();
  await expect(page.getByText("Suppressed", { exact: true }).first()).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Operations views" })).toHaveCount(0);
  expect((await page.request.get("/api/backend/workbench")).status()).toBe(403);
});

test("queue service errors show an actionable retry rather than stale success", async ({ page }) => {
  const pattern = "**/api/backend/workbench?**";
  await page.route(pattern, route => route.fulfill({
    status: 503, contentType: "application/json",
    body: JSON.stringify({ error: { code: "TEST_SERVICE_UNAVAILABLE", traceId: "browser-error-check" } }),
  }));
  await login(page);
  await expect(page.getByRole("alert").filter({ hasText: "TEST_SERVICE_UNAVAILABLE" })).toBeVisible();
  await expect(page.getByText("No operational snapshot available.")).toBeVisible();
  await page.unroute(pattern);
  await page.getByRole("button", { name: "Refresh data", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Readiness checklist" })).toBeVisible();
  await expect(page.getByText("6 matching / 6 authorized")).toBeVisible();
  await expect(page.getByRole("alert").filter({ hasText: "TEST_SERVICE_UNAVAILABLE" })).toHaveCount(0);
});

test("responsive workspace has no horizontal overflow and keyboard navigation works", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await selectCase(page, "SYN-CASE-001");
  const overview = page.getByRole("navigation", { name: "Case sections" }).getByRole("button", { name: "overview", exact: true });
  await overview.focus();
  await page.keyboard.press("Tab");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Intake & Member 360" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  const queueWidth = await page.locator(".queue-items").evaluate(e => e.clientWidth);
  const itemWidth = await page.locator(".case-item").first().evaluate(e => e.clientWidth);
  expect(queueWidth).toBeGreaterThan(300);
  expect(itemWidth).toBeGreaterThan(queueWidth - 10);
  await page.getByRole("navigation", { name: "Case sections" }).getByRole("button", { name: "evidence", exact: true }).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
});

test("capture updated review-ready dashboard when an artifact directory is supplied", async ({ page }) => {
  test.skip(!process.env.BENEFITS_SCREENSHOT_DIR, "Optional local artifact capture.");
  await login(page);
  await selectCase(page, "SYN-CASE-001");
  await expect(page.getByRole("heading", { name: "Readiness checklist" })).toBeVisible();
  await page.evaluate(() => {
    window.scrollTo(0, 0);
    const queue = document.querySelector(".queue-items");
    if (queue) queue.scrollTop = 0;
  });
  await page.screenshot({ path: path.join(process.env.BENEFITS_SCREENSHOT_DIR!, "dashboard-after.png"), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: path.join(process.env.BENEFITS_SCREENSHOT_DIR!, "dashboard-mobile.png"), fullPage: true });
});
