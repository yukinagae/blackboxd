import type { TraceEvent } from "../types.ts";

export interface Storage {
  writeEvent(event: TraceEvent): Promise<void>;
}
