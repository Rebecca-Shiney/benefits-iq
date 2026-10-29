import { expect, test, type Page } from "@playwright/test";

async function openChat(page: Page) {
  await page.goto("/");
  await page.getByLabel("LOCAL DEMO PERSONA").selectOption("reviewer-a");
  await page.getByRole("button", { name: "Open workspace" }).click();
  await page.getByRole("button", { name: /^SYN-CASE-001/ }).click();
  await expect(page.getByRole("heading", { name: "SYN-CASE-001", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Open case-bound chat" }).click();
  return page.getByRole("region", { name: "Case-bound assistant chat" });
}

test("first-party chat supports keyboard sending and genuine read-only MAF streaming", async ({ page }) => {
  const chat = await openChat(page);
  const before = await (await page.request.get("/api/backend/cases/SYN-CASE-001")).json();
  await chat.getByLabel("Case-bound chat message").fill("Current status");
  await chat.getByLabel("Case-bound chat message").press("Tab");
  await expect(chat.getByRole("button", { name: "Send message", exact: true })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(chat.getByRole("status")).toContainText("Response complete");
  await expect(chat.getByRole("log")).toContainText("Synthetic mode - no model call.");
  await expect(chat.getByRole("log")).toContainText("Status Agent:");
  await expect(chat.getByLabel("Case-bound chat message")).toBeFocused();
  const after = await (await page.request.get("/api/backend/cases/SYN-CASE-001")).json();
  expect(after.decision).toEqual(before.decision);
  expect(after.version).toBe(before.version);
  await page.getByRole("button", { name: "Close chat" }).click();
  await page.getByRole("button", { name: "Open case-bound chat" }).click();
  await expect(chat.getByRole("log")).not.toContainText("Status Agent:");
  await chat.getByLabel("Case-bound chat message").fill("A message not sent");
  await page.getByRole("button", { name: /^SYN-CASE-002/ }).click();
  await expect(chat).toHaveCount(0);
});

test("chat errors are explicit, partial replies are marked incomplete, retry is user initiated", async ({ page }) => {
  let calls = 0;
  await page.route("**/api/chat", async route => {
    calls++;
    const events = [
      { type: "RUN_STARTED", threadId: "SYN-CASE-001", runId: "retry-run" },
      { type: "TEXT_MESSAGE_START", messageId: "m1", role: "assistant" },
      { type: "TEXT_MESSAGE_CONTENT", messageId: "m1", delta: calls === 1 ? "Partial response" : "Retried response" },
      ...(calls === 1 ? [{ type: "RUN_ERROR", message: "private provider detail" }] : [
        { type: "TEXT_MESSAGE_END", messageId: "m1" },
        { type: "RUN_FINISHED", threadId: "SYN-CASE-001", runId: "retry-run" },
      ]),
    ];
    await route.fulfill({ contentType: "text/event-stream", body: events.map(event => `data: ${JSON.stringify(event)}\n\n`).join("") });
  });
  const chat = await openChat(page);
  await chat.getByLabel("Case-bound chat message").fill("Current status");
  await chat.getByRole("button", { name: "Send message", exact: true }).click();
  await expect(chat.getByRole("alert")).toContainText("Chat did not finish");
  await expect(chat.getByRole("log")).toContainText("Incomplete / failed");
  await expect(chat).not.toContainText("private provider detail");
  expect(calls).toBe(1);
  await chat.getByRole("button", { name: "Retry last message" }).click();
  await expect(chat.getByRole("status")).toContainText("Response complete");
  expect(calls).toBe(2);
  await chat.getByRole("button", { name: "Clear chat" }).click();
  await expect(chat.getByRole("log")).not.toContainText("Retried response");
});

test("chat cancellation never silently retries and keeps controls usable", async ({ page }) => {
  let release: () => void = () => {};
  const pending = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/chat", async route => { await pending; await route.abort("aborted"); });
  const chat = await openChat(page);
  await chat.getByLabel("Case-bound chat message").fill("Current status");
  await chat.getByRole("button", { name: "Send message", exact: true }).click();
  await chat.getByRole("button", { name: "Cancel chat response" }).click();
  release();
  await expect(chat.getByRole("alert")).toContainText("Chat cancelled");
  await expect(chat.getByRole("status")).toContainText("Nothing is replayed automatically");
  await expect(chat.getByLabel("Case-bound chat message")).toBeEnabled();
  await expect(chat.getByRole("button", { name: "Retry last message" })).toBeEnabled();
});
