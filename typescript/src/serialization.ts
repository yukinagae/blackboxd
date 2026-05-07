export function toJsonable(value: unknown): unknown {
  if (
    value === null ||
    value === undefined ||
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return value;
  }

  if (value instanceof Date) {
    return value.toISOString();
  }

  if (Array.isArray(value)) {
    return value.map((item) => toJsonable(item));
  }

  if (typeof value === "object") {
    if ("toJSON" in value && typeof (value as { toJSON?: unknown }).toJSON === "function") {
      return toJsonable((value as { toJSON: () => unknown }).toJSON());
    }

    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, item]) => [key, toJsonable(item)]),
    );
  }

  return String(value);
}
