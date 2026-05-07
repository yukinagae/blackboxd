import os

from blackboxd import SupabaseStorage, configure


configure(
    storage=SupabaseStorage(os.environ["SUPABASE_DB_DSN"]),
    environment="development",
    app_version="0.1.0",
    default_tags=["supabase"],
)
