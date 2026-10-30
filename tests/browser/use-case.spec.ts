import { expect, test, type Page } from "@playwright/test";
import path from "node:path";

const guideTab = (page: Page) => page.getByRole("tab", { name: "Understand the use case", exact: true });
const dashboardTab = (page: Page) => page.getByRole("tab", { name: "Your dashboard", exact: true });
const guide = (page: Page) => page.getByRole("tabpanel", { name: "Understand the use case", exact: true });
const tourButton = (page: Page) => page.getByRole("button", { name: "Get to know your dashboard", exact: true });
const copy = [
  ["Why it exists", "Bring a benefits request and its evidence together, so people can review it without chasing separate files."],
  ["Who it helps", "Reviewers check evidence, contact teams explain status, and employers see group trends, not individual records."],
  ["People make the decision", "Agents prepare checks and citations. A human must approve, decline or ask for more information."],
  ["How it connects", "Next.js talks to internal Python agents. Canadian AI, search and document reading help; private SQL keeps records."],
  ["What the AI does", "Microsoft Agent Framework powers case-bound chat. The model explains evidence and status; it never decides."],
  ["Where the IQs fit", "IQs are future options for enterprise knowledge and data. Today, we use Azure AI Search with synthetic sources."],
  ["How services stay protected", "Services use managed identities, not stored keys. The backend is internal and SQL uses a private connection."],
  ["Know the demo limits", "Anyone can switch demo views; this is not sign-in. No real member data, document uploads or external sends."],
];

async function login(page: Page, persona = "reviewer-a") {
  await page.goto("/");
  await page.getByLabel("LOCAL DEMO PERSONA", { exact: true }).selectOption(persona);
  await page.getByRole("button", { name: "Open workspace" }).click();
  await expect(page.getByRole("heading", {
    name: persona.startsWith("employer") ? "Specialty utilization trends" : "Case queue", exact: true,
  })).toBeVisible();
  await expect(guideTab(page)).toBeEnabled();
}

test("use-case guide is opt-in and preserves the selected case, case tab, unsaved fields and audit without requests", async ({ page }) => {
  await login(page, "reviewer-b");
  await expect(dashboardTab(page)).toHaveAttribute("aria-selected", "true");
  await expect(guide(page)).toHaveCount(0);
  await page.getByRole("button", { name: /^SYN-CASE-004/ }).click();
  await page.getByRole("navigation", { name: "Case sections" }).getByRole("button", { name: "intake", exact: true }).click();
  const indication = page.getByLabel(/^indication/i);
  await indication.fill("Synthetic unsaved change");
  await page.getByRole("button", { name: "Open case-bound chat" }).click();
  const message = page.getByLabel("Case-bound chat message");
  await message.fill("Synthetic draft not sent");
  const before = await (await page.request.get("/api/backend/cases/SYN-CASE-004")).json();
  const requests: string[] = [];
  page.on("request", request => {
    if (/\/api\/(backend|chat|session)/.test(request.url())) requests.push(request.url());
  });
  await guideTab(page).click();
  await expect(guide(page).getByRole("heading", { name: "Why this dashboard?" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Case sections" })).toHaveCount(0);
  await dashboardTab(page).click();
  await expect(page.getByRole("heading", { name: "SYN-CASE-004", exact: true })).toBeVisible();
  await expect(page.locator(".case-tabs button[aria-current]")).toHaveText("intake");
  await expect(indication).toHaveValue("Synthetic unsaved change");
  await expect(message).toHaveValue("Synthetic draft not sent");
  expect(requests).toEqual([]);
  expect(await (await page.request.get("/api/backend/cases/SYN-CASE-004")).json()).toEqual(before);
});

test("use-case explanations are exact short copy, at most two desktop lines, and fully reflow on mobile", async ({ page }) => {
  await login(page);
  await guideTab(page).click();
  const cards = guide(page).locator(".use-case-card");
  await expect(cards).toHaveCount(8);
  for (const [index, [title, text]] of copy.entries()) {
    await expect(cards.nth(index).getByRole("heading")).toHaveText(title);
    await expect(cards.nth(index).locator("p")).toHaveText(text);
    expect(text.length).toBeLessThanOrEqual(115);
  }
  for (const width of [1600, 1280]) {
    await page.setViewportSize({ width, height: 1100 });
    const lines = await cards.locator("p").evaluateAll(elements => elements.map(element => {
      const range = document.createRange();
      range.selectNodeContents(element);
      return range.getClientRects().length;
    }));
    expect(lines.every(count => count <= 2)).toBeTruthy();
  }
  if (process.env.BENEFITS_SCREENSHOT_DIR) {
    await page.screenshot({ path: path.join(process.env.BENEFITS_SCREENSHOT_DIR, "use-case-desktop.png"), fullPage: true });
  }
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    for (const card of await cards.all()) {
      await expect(card).toBeVisible();
      expect(await card.locator("p").evaluate(element => {
        const style = getComputedStyle(element);
        return style.overflow === "visible" && style.textOverflow !== "ellipsis" && element.scrollHeight <= element.clientHeight + 1;
      })).toBeTruthy();
    }
  }
  if (process.env.BENEFITS_SCREENSHOT_DIR) {
    await page.screenshot({ path: path.join(process.env.BENEFITS_SCREENSHOT_DIR, "use-case-mobile.png"), fullPage: true });
  }
  expect(await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue("--teal").trim())).toBe("#086f66");
  await expect(guide(page).getByRole("link")).toHaveAttribute("href", "https://github.com/Rebecca-Shiney/benefits-iq/blob/main/README.md#architecture");
});

test("use-case tabs have keyboard selection, roving focus and correctly labelled panels", async ({ page }) => {
  await login(page, "employer-b");
  await dashboardTab(page).focus();
  await page.keyboard.press("ArrowRight");
  await expect(guideTab(page)).toBeFocused();
  await expect(guideTab(page)).toHaveAttribute("aria-selected", "true");
  await expect(dashboardTab(page)).toHaveAttribute("tabindex", "-1");
  await expect(guide(page)).toHaveAttribute("id", (await guideTab(page).getAttribute("aria-controls"))!);
  await expect(guide(page)).toHaveAttribute("aria-labelledby", (await guideTab(page).getAttribute("id"))!);
  await page.keyboard.press("Tab");
  await expect(guide(page)).toBeFocused();
  await guideTab(page).focus();
  await page.keyboard.press("Home");
  await expect(dashboardTab(page)).toBeFocused();
  await expect(dashboardTab(page)).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("End");
  await expect(guideTab(page)).toBeFocused();
  await page.keyboard.press("ArrowLeft");
  await expect(dashboardTab(page)).toBeFocused();
  await expect(guide(page)).toHaveCount(0);
});

for (const persona of ["contact-a", "employer-a", "employer-b"]) {
  test(`use-case guide is the same non-personal explanation for ${persona}`, async ({ page }) => {
    await login(page, persona);
    await guideTab(page).click();
    await expect(guide(page).locator(".use-case-card")).toHaveCount(8);
    await expect(guide(page)).not.toContainText(/SYN-CASE-|SYN-MEMBER-|Avery Morgan|Riley Chen/);
    await dashboardTab(page).click();
    await expect(page.getByRole("heading", {
      name: persona.startsWith("employer") ? "Specialty utilization trends" : "Case queue", exact: true,
    })).toBeVisible();
    if (persona.startsWith("employer")) {
      await expect(page.getByRole("navigation", { name: "Operations views" })).toHaveCount(0);
    }
  });
}

test("use-case guide and the existing dashboard tour use only visible targets and close stale tours", async ({ page }) => {
  await login(page, "reviewer-b");
  await tourButton(page).click();
  await guideTab(page).dispatchEvent("click");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await tourButton(page).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.locator(".tour-progress")).toHaveText("Step 1 of 2");
  await dialog.getByRole("button", { name: "Next", exact: true }).click();
  await expect(dialog).toHaveAttribute("data-tour-target", "use-case");
  await expect(dialog.getByRole("heading")).toHaveText("Understand why this dashboard exists");
  await dialog.getByRole("button", { name: "Finish", exact: true }).click();
  await expect(tourButton(page)).toBeFocused();
  await expect(guideTab(page)).toHaveAttribute("aria-selected", "true");
  await dashboardTab(page).click();
  await tourButton(page).click();
  await expect(dialog.locator(".tour-progress")).toHaveText("Step 1 of 8");
  await page.keyboard.press("Escape");
});

test("use-case tab resets when a different workspace is opened", async ({ page }) => {
  await login(page, "contact-a");
  await guideTab(page).click();
  await page.getByLabel("Demo workspace").selectOption("employer-a");
  await page.getByRole("button", { name: "Switch workspace" }).click();
  await expect(page.getByRole("heading", { name: "Specialty utilization trends" })).toBeVisible();
  await expect(dashboardTab(page)).toHaveAttribute("aria-selected", "true");
  await expect(guide(page)).toHaveCount(0);
});
