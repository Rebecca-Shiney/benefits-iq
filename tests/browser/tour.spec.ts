import { expect, test, type Page } from "@playwright/test";
import path from "node:path";

const guide = (page: Page) => page.getByRole("dialog");
const start = (page: Page) => page.getByRole("button", { name: "Get to know your dashboard", exact: true });

// Spread real requests across fixtures rather than disabling the shared per-view limiter.
async function login(page: Page, persona = "reviewer-b") {
  await page.goto("/");
  await page.getByLabel("LOCAL DEMO PERSONA", { exact: true }).selectOption(persona);
  await page.getByRole("button", { name: "Open workspace" }).click();
  await expect(page.getByRole("heading", { name: persona.startsWith("employer") ? "Specialty utilization trends" : "Case queue", exact: true })).toBeVisible();
  await expect(start(page)).toBeEnabled();
}

async function expectStep(page: Page, target: string, index: number, total: number, focusTitle = true) {
  await expect(guide(page)).toHaveAttribute("data-tour-target", target);
  await expect(guide(page).locator(".tour-progress")).toHaveText(`Step ${index} of ${total}`);
  if (focusTitle) await expect(guide(page).getByRole("heading")).toBeFocused();
  await expect(page.locator(`[data-tour="${target}"]`)).toBeVisible();
  const card = await page.locator(".tour-card").boundingBox();
  expect(card).not.toBeNull();
  const viewport = page.viewportSize()!;
  expect(card!.x).toBeGreaterThanOrEqual(15);
  expect(card!.y).toBeGreaterThanOrEqual(15);
  expect(card!.x + card!.width).toBeLessThanOrEqual(viewport.width - 15);
  expect(card!.y + card!.height).toBeLessThanOrEqual(viewport.height - 15);
  const highlight = await page.locator(".tour-spotlight").boundingBox();
  const targetBox = await page.locator(`[data-tour="${target}"]`).boundingBox();
  expect(highlight!.width).toBeGreaterThanOrEqual(Math.min(60, targetBox!.width));
  expect(highlight!.height).toBeGreaterThanOrEqual(Math.min(40, targetBox!.height));
}

test("guide is opt-in and landing navigation, Escape, skip and restart restore focus", async ({ page }) => {
  await page.goto("/");
  await expect(start(page)).toBeEnabled();
  await expect(guide(page)).toHaveCount(0);
  await start(page).click();
  await expectStep(page, "workspace", 1, 3);
  await expect(guide(page).getByRole("button", { name: "Back", exact: true })).toBeDisabled();
  await page.keyboard.press("ArrowRight");
  await expectStep(page, "safety", 2, 3);
  await page.keyboard.press("ArrowLeft");
  await expectStep(page, "workspace", 1, 3);
  await page.keyboard.press("Escape");
  await expect(guide(page)).toHaveCount(0);
  await expect(start(page)).toBeFocused();
  await page.keyboard.press("Enter");
  await expectStep(page, "workspace", 1, 3);
  await guide(page).getByRole("button", { name: "Skip tour", exact: true }).click();
  await expect(start(page)).toBeFocused();
});

test("reviewer tour visits read-only tabs, supports Back and Finish, and changes no case or model state", async ({ page }) => {
  await login(page);
  await page.getByRole("button", { name: /^SYN-CASE-004/ }).click();
  await expect(page.getByRole("heading", { name: "SYN-CASE-004", exact: true })).toBeVisible();
  const before = await (await page.request.get("/api/backend/cases/SYN-CASE-004")).json();
  const writes: string[] = [];
  page.on("request", request => {
    if (request.method() !== "GET" && /\/api\/(backend|chat|session)/.test(request.url())) writes.push(request.url());
  });
  await start(page).click();
  const targets = ["workspace", "metrics", "queue", "intake", "documents", "evidence", "decision", "assistant"];
  for (const [index, target] of targets.entries()) {
    await expectStep(page, target, index + 1, targets.length);
    if (target === "intake") {
      await guide(page).getByRole("button", { name: "Back", exact: true }).click();
      await expectStep(page, "queue", 3, 8);
      await guide(page).getByRole("button", { name: "Next", exact: true }).click();
      await expectStep(page, "intake", 4, 8);
    }
    if (target === "decision") {
      await expect(page.locator(".decision input[type=checkbox]")).not.toBeChecked();
      await expect(page.locator(".decision button").last()).toBeDisabled();
    }
    await guide(page).getByRole("button", { name: index === targets.length - 1 ? "Finish" : "Next", exact: true }).click();
  }
  await expect(guide(page)).toHaveCount(0);
  await expect(start(page)).toBeFocused();
  await expect(page.locator(".case-tabs button[aria-current]")).toHaveText("overview");
  expect(writes).toEqual([]);
  expect(await (await page.request.get("/api/backend/cases/SYN-CASE-004")).json()).toEqual(before);
  await start(page).click();
  await expectStep(page, "workspace", 1, 8);
  await guide(page).getByRole("button", { name: "Close dashboard tour", exact: true }).click();
  await expect(start(page)).toBeFocused();
});

for (const [persona, targets] of [
  ["contact-a", ["workspace", "metrics", "queue", "status", "tasks", "assistant"]],
  ["employer-a", ["workspace", "portfolio", "suppression"]],
  ["employer-b", ["workspace", "portfolio", "suppression"]],
] as const) {
  test(`${persona} tour contains only its selected-view sections`, async ({ page }) => {
    await login(page, persona);
    await start(page).click();
    for (const [index, target] of targets.entries()) {
      await expectStep(page, target, index + 1, targets.length);
      await expect(guide(page)).not.toContainText(/Member 360|choose an outcome|evidence matrix/);
      await expect(page.locator('[data-tour="decision"], [data-tour="intake"], [data-tour="evidence"]')).toHaveCount(0);
      await guide(page).getByRole("button", { name: index === targets.length - 1 ? "Finish" : "Next", exact: true }).click();
    }
    await expect(start(page)).toBeFocused();
  });
}

test("team, renewal and selected case-tab tours explain the actual open view", async ({ page }) => {
  await login(page, "reviewer-b");
  for (const [button, target] of [["Team tasks", "team-tasks"], ["Renewal watch", "renewals"]] as const) {
    await page.getByRole("navigation", { name: "Operations views" }).getByRole("button", { name: new RegExp(`^${button}`) }).click();
    await start(page).click();
    for (let i = 0; i < 3; i++) await guide(page).getByRole("button", { name: "Next", exact: true }).click();
    await expectStep(page, target, 4, 4);
    await guide(page).getByRole("button", { name: "Finish", exact: true }).click();
  }
  await page.getByRole("navigation", { name: "Operations views" }).getByRole("button", { name: /^Case queue/ }).click();
  for (const tab of ["tasks", "status", "activity"]) {
    await page.getByRole("navigation", { name: "Case sections" }).getByRole("button", { name: tab === "tasks" ? /^Tasks/ : tab, exact: tab !== "tasks" }).click();
    await start(page).click();
    for (let i = 0; i < 3; i++) await guide(page).getByRole("button", { name: "Next", exact: true }).click();
    await expectStep(page, tab, 4, 5);
    await page.keyboard.press("Escape");
    await expect(page.locator(".case-tabs button[aria-current]")).toContainText(tab === "tasks" ? "Tasks" : tab);
  }
});

test("missing and dynamically hidden targets are skipped without trapping the visitor", async ({ page }) => {
  await login(page);
  await start(page).click();
  await page.locator('[data-tour="metrics"]').evaluate(element => { element.setAttribute("hidden", ""); });
  await guide(page).getByRole("button", { name: "Next", exact: true }).click();
  await expectStep(page, "queue", 2, 7);
  await page.locator('[data-tour="queue"]').evaluate(element => { element.setAttribute("hidden", ""); });
  await expectStep(page, "intake", 2, 6);
  await page.addStyleTag({ content: "[data-tour] { display: none !important; }" });
  await expect(guide(page)).toHaveCount(0);
  await expect(start(page)).toBeFocused();
});

test("case, manual-tab and workspace changes close rather than resurrect a stale tour", async ({ page }) => {
  await login(page);
  await page.getByRole("button", { name: /^SYN-CASE-004/ }).click();
  await start(page).click();
  await page.locator(".case-item").filter({ hasText: "SYN-CASE-005" }).dispatchEvent("click");
  await expect(guide(page)).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "SYN-CASE-005", exact: true })).toBeVisible();
  await start(page).click();
  await page.locator(".case-tabs button").filter({ hasText: /^status$/ }).dispatchEvent("click");
  await expect(guide(page)).toHaveCount(0);
  await expect(page.locator(".case-tabs button[aria-current]")).toHaveText("status");
  await page.getByLabel("Demo workspace").selectOption("employer-a");
  await start(page).click();
  await page.locator(".persona-switch button").dispatchEvent("click");
  await expect(guide(page)).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Employer portfolio", exact: true })).toBeVisible();
  await start(page).click();
  await expectStep(page, "workspace", 1, 3);
});

test("mobile reduced-motion tour remains bounded, scrolls and confines keyboard focus", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await login(page);
  await start(page).click();
  const targets = ["workspace", "metrics", "queue", "intake", "documents", "evidence", "decision", "assistant"];
  for (const [index, target] of targets.entries()) {
    await expectStep(page, target, index + 1, 8);
    for (let i = 0; i < 6; i++) {
      await page.keyboard.press("Tab");
      expect(await guide(page).evaluate(element => element.contains(document.activeElement))).toBeTruthy();
    }
    for (let i = 0; i < 6; i++) {
      await page.keyboard.press("Shift+Tab");
      expect(await guide(page).evaluate(element => element.contains(document.activeElement))).toBeTruthy();
    }
    if (index < targets.length - 1) await page.keyboard.press("ArrowRight");
  }
  const focused = await guide(page).evaluate(() => document.activeElement?.textContent);
  await page.setViewportSize({ width: 320, height: 600 });
  await expectStep(page, "assistant", 8, 8, false);
  expect(await guide(page).evaluate(() => document.activeElement?.textContent)).toBe(focused);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.keyboard.press("Escape");
  await expect(start(page)).toBeFocused();
});

test("disabled features and absent case data do not create phantom tour steps", async ({ page }) => {
  await page.route("**/api/backend/session", async route => {
    const response = await route.fetch();
    const data = await response.json();
    await route.fulfill({ response, json: { ...data, features: { ...data.features, chat: false, intake: false, evidence: false, renewal: false } } });
  });
  await login(page);
  await start(page).click();
  for (const [index, target] of ["workspace", "metrics", "queue", "documents", "decision"].entries()) {
    await expectStep(page, target, index + 1, 5);
    await expect(guide(page)).not.toContainText("Renewal watch");
    await guide(page).getByRole("button", { name: index === 4 ? "Finish" : "Next", exact: true }).click();
  }
  await page.route("**/api/backend/workbench?**", route => route.fulfill({
    status: 503, json: { error: { code: "TEST_TOUR_SOURCE_UNAVAILABLE", traceId: "tour-negative-path" } },
  }));
  await login(page);
  await start(page).click();
  await expectStep(page, "workspace", 1, 2);
  await guide(page).getByRole("button", { name: "Next", exact: true }).click();
  await expectStep(page, "queue", 2, 2);
  await guide(page).getByRole("button", { name: "Finish", exact: true }).click();
});

test("public-showcase tour explicitly calls the view switcher demo navigation", async ({ page }) => {
  await page.route("**/api/auth/config", route => route.fulfill({ json: { profile: "showcase" } }));
  await page.goto("/");
  await page.getByLabel("PUBLIC DEMO VIEW", { exact: true }).selectOption("reviewer-b");
  await page.getByRole("button", { name: "Open workspace" }).click();
  await expect(start(page)).toBeEnabled();
  await start(page).click();
  await expect(guide(page)).toContainText("demo navigation, not sign-in or authenticated roles");
  await expect(guide(page)).toContainText("Use synthetic data only");
  await page.keyboard.press("Escape");
  await expect(start(page)).toBeFocused();
});

test("capture desktop and mobile tour artifacts when requested", async ({ page }) => {
  test.skip(!process.env.BENEFITS_SCREENSHOT_DIR, "Optional review artifacts.");
  await login(page);
  await start(page).click();
  for (let i = 0; i < 3; i++) await guide(page).getByRole("button", { name: "Next", exact: true }).click();
  await expectStep(page, "intake", 4, 8);
  await page.screenshot({ path: path.join(process.env.BENEFITS_SCREENSHOT_DIR!, "dashboard-tour.png") });
  await page.setViewportSize({ width: 390, height: 844 });
  await expectStep(page, "intake", 4, 8);
  await page.screenshot({ path: path.join(process.env.BENEFITS_SCREENSHOT_DIR!, "dashboard-tour-mobile.png") });
});
