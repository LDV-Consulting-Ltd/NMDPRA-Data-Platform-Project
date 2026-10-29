import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from dotenv import load_dotenv

load_dotenv()

# Allow `from app.db_url import ...` when alembic runs from apps/api
_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.db_url import resolve_database_url  # noqa: E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None  # We use raw SQL in migrations for full control

database_url = resolve_database_url(
    database_url=os.getenv("DATABASE_URL"),
    supabase_db_url=os.getenv("SUPABASE_DB_URL"),
    supabase_db_host=os.getenv("SUPABASE_DB_HOST"),
    supabase_db_password=os.getenv("SUPABASE_DB_PASSWORD"),
    supabase_db_user=os.getenv("SUPABASE_DB_USER"),
    supabase_db_name=os.getenv("SUPABASE_DB_NAME"),
    supabase_db_port=int(os.getenv("SUPABASE_DB_PORT") or "5432"),
    supabase_db_sslmode=os.getenv("SUPABASE_DB_SSLMODE"),
)
# Alembic ConfigParser treats % as interpolation — escape for URLs with encoded chars.
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
