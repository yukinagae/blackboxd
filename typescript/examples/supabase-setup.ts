import { configure, SupabaseStorage } from "../src/index.ts";

configure({
  storage: new SupabaseStorage(process.env.SUPABASE_DB_DSN ?? ""),
  environment: "development",
  appVersion: "0.1.0",
  defaultTags: ["typescript", "supabase"],
});
