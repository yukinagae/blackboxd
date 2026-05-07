from __future__ import annotations

from blackboxd.storage.supabase import SupabaseStorage


class PostgresStorage(SupabaseStorage):
    """Backward-compatible alias for the Supabase/Postgres backend."""
