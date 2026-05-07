import { randomUUID } from "node:crypto";

export function createId(): string {
  return randomUUID();
}

export function utcNowIso(): string {
  return new Date().toISOString();
}

export function durationMs(startedAt: string, endedAt: string): number {
  return Math.max(0, Date.parse(endedAt) - Date.parse(startedAt));
}
