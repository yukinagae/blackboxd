import { mkdir, appendFile } from "node:fs/promises";
import { dirname } from "node:path";

import type { TraceEvent } from "../types.ts";
import type { Storage } from "./base.ts";

export class JSONLStorage implements Storage {
  path: string;

  constructor(path = ".blackboxd/logs.jsonl") {
    this.path = path;
  }

  async writeEvent(event: TraceEvent): Promise<void> {
    await mkdir(dirname(this.path), { recursive: true });
    await appendFile(this.path, `${JSON.stringify(event)}\n`, "utf8");
  }
}
