import { JSONLStorage } from "./storage/jsonl.ts";
import type { Storage } from "./storage/base.ts";

export interface BlackboxdConfig {
  storage: Storage;
  environment: string;
  appVersion: string;
  defaultTags: string[];
  defaultMetadata: Record<string, unknown>;
}

const config: BlackboxdConfig = {
  storage: new JSONLStorage(),
  environment: "development",
  appVersion: "0.0.0",
  defaultTags: [],
  defaultMetadata: {},
};

export function configure(next: Partial<BlackboxdConfig> & { storage?: Storage | string }): BlackboxdConfig {
  if (typeof next.storage === "string") {
    config.storage = new JSONLStorage(next.storage);
  } else if (next.storage) {
    config.storage = next.storage;
  }

  if (next.environment !== undefined) {
    config.environment = next.environment;
  }

  if (next.appVersion !== undefined) {
    config.appVersion = next.appVersion;
  }

  if (next.defaultTags !== undefined) {
    config.defaultTags = [...next.defaultTags];
  }

  if (next.defaultMetadata !== undefined) {
    config.defaultMetadata = { ...next.defaultMetadata };
  }

  return config;
}

export function getConfig(): BlackboxdConfig {
  return config;
}
