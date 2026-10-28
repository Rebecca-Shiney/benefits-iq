import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".\\tests\\browser",
  workers: 1,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: process.env.BENEFITS_TEST_URL || "http://127.0.0.1:3020",
    viewport: { width: 1600, height: 1000 },
    trace: "retain-on-failure",
  },
});
