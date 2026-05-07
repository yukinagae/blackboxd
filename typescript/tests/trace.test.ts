import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { configure, trace, traceSpan } from "../src/index.ts";

test("trace and traceSpan write nested JSONL events", async () => {
  const dir = await mkdtemp(join(tmpdir(), "blackboxd-ts-"));
  const path = join(dir, "events.jsonl");

  configure({
    storage: path,
    environment: "test",
    appVersion: "1.2.3",
  });

  const run = trace("run", { tags: ["unit"] })(async () => {
    return traceSpan("nested", async () => "ok");
  });

  assert.equal(await run(), "ok");

  const lines = (await readFile(path, "utf8")).trim().split("\n");
  assert.equal(lines.length, 2);

  const events = lines.map((line) => JSON.parse(line) as { name: string; traceId: string; environment: string });
  assert.ok(events.every((event) => event.traceId));
  assert.ok(events.some((event) => event.name === "nested"));
  assert.ok(events.every((event) => event.environment === "test"));
});
