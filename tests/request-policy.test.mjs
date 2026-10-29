import assert from "node:assert/strict";
import test from "node:test";
import { readBoundedJson } from "../lib/request-policy.ts";

function request(body, headers = {}, signal) {
  return new Request("http://localhost/api/test", {
    method: "POST", body, duplex: "half", signal,
    headers: { "content-type": "application/json", ...headers },
  });
}

async function error(response, status, code) {
  assert.ok(response instanceof Response);
  assert.equal(response.status, status);
  assert.equal((await response.json()).error.code, code);
}

test("valid JSON is preserved for the real runtime handler", async () => {
  const text = JSON.stringify({ messages: [{ role: "user", content: "Check my case." }] });
  assert.deepEqual(await readBoundedJson(request(text)), { text, value: JSON.parse(text) });
});

test("GET has no body but still rejects compressed requests", async () => {
  assert.deepEqual(await readBoundedJson(new Request("http://localhost")), {});
  await error(await readBoundedJson(new Request("http://localhost", {
    headers: { "content-encoding": "gzip" },
  })), 415, "COMPRESSED_REQUEST_DENIED");
});

test("compressed JSON cannot reach downstream body parsers", async () => {
  for (const encoding of ["gzip", "deflate", "br", "gzip, identity"]) {
    await error(await readBoundedJson(request("{}", { "content-encoding": encoding })),
      415, "COMPRESSED_REQUEST_DENIED");
  }
});

test("Content-Length is only an early rejection, not a trusted size", async () => {
  await error(await readBoundedJson(request("{}", { "content-length": "32001" })), 413, "REQUEST_LIMIT");
  await error(await readBoundedJson(request("{}", { "content-length": "-1" })), 400, "INVALID_CONTENT_LENGTH");
  await error(await readBoundedJson(request(JSON.stringify("a".repeat(33_000)), {
    "content-length": "1",
  })), 413, "REQUEST_LIMIT");
});

test("unknown-length streams are bounded by bytes before buffering", async () => {
  let cancelled = false;
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(new Uint8Array(20_000));
      controller.enqueue(new Uint8Array(20_000));
    },
    cancel() { cancelled = true; },
  });
  await error(await readBoundedJson(request(stream)), 413, "REQUEST_LIMIT");
  assert.equal(cancelled, true);
});

test("multibyte UTF-8 cannot evade the byte limit", async () => {
  await error(await readBoundedJson(request(JSON.stringify("é".repeat(16_000)))), 413, "REQUEST_LIMIT");
});

test("byte limits accept the exact threshold and reject the next byte", async () => {
  const maximum = "{}".padEnd(32_000);
  assert.equal((await readBoundedJson(request(maximum))).text.length, 32_000);
  await error(await readBoundedJson(request(maximum + " ")), 413, "REQUEST_LIMIT");
  assert.equal((await readBoundedJson(request("{}".padEnd(1024)), 1024)).text.length, 1024);
  await error(await readBoundedJson(request("{}".padEnd(1025)), 1024), 413, "REQUEST_LIMIT");
});

test("malformed JSON, invalid UTF-8 and wrong content type fail explicitly", async () => {
  await error(await readBoundedJson(request("{")), 400, "INVALID_JSON");
  await error(await readBoundedJson(request(new Uint8Array([0xff]))), 400, "INVALID_JSON");
  await error(await readBoundedJson(request("{}", { "content-type": "text/plain" })), 415, "JSON_REQUIRED");
});

test("oversized collections are rejected before SDK schema parsing", async () => {
  await error(await readBoundedJson(request(JSON.stringify(Array(129).fill(0)))), 422, "REQUEST_SHAPE_LIMIT");
  await error(await readBoundedJson(request(JSON.stringify(
    Object.fromEntries(Array.from({ length: 129 }, (_, i) => [`key${i}`, i])),
  ))), 422, "REQUEST_SHAPE_LIMIT");
});

test("deep JSON cannot cause recursive SDK validation", async () => {
  let value = "end";
  for (let i = 0; i < 26; i++) value = { child: value };
  await error(await readBoundedJson(request(JSON.stringify(value))), 422, "REQUEST_SHAPE_LIMIT");
});

test("total nodes and individual strings have independent bounds", async () => {
  const value = Array.from({ length: 64 }, () => Array(64).fill(0));
  await error(await readBoundedJson(request(JSON.stringify(value))), 422, "REQUEST_SHAPE_LIMIT");
  await error(await readBoundedJson(request(JSON.stringify("a".repeat(16_001)))), 422, "REQUEST_SHAPE_LIMIT");
});

test("aborted requests are not parsed or forwarded", async () => {
  const controller = new AbortController();
  controller.abort();
  await error(await readBoundedJson(request("{}", {}, controller.signal)), 408, "REQUEST_INTERRUPTED");
});

test("stalled body reads are cancelled at the ten-second deadline", async (context) => {
  context.mock.timers.enable({ apis: ["setTimeout"] });
  let cancelled = false;
  const stream = new ReadableStream({ cancel() { cancelled = true; } });
  const pending = readBoundedJson(request(stream));
  context.mock.timers.tick(10_000);
  await error(await pending, 408, "REQUEST_INTERRUPTED");
  assert.equal(cancelled, true);
});
