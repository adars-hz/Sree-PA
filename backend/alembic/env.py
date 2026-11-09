import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add the root directory to sys.path so we can import from backend.app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.config import settings
from backend.app.database.db import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in executing the migrations.
config = context.config

# Interpret the config file for SQLAlchemy.
section = config.get_section(config.config_ini_section)
# Override the sqlalchemy.url from the .ini file with the actual DB path from settings
section['sqlalchemy.url'] = f"sqlite:///{settings.DB_PATH}"

# Initialize the engine
connectable = engine_from_config(
    section,
    prefix="sqlalchemy.",
    poolclass=pool.QueuePool,
)

# This is the Alembic Config object, which provides
# access to the values within the .ini file in executing the migrations.
target_metadata = Base.metadata

# revision identifiers, used by Alembic to track which migrations have been run.
revision = context.get_revision(config, target_metadata=None)

if revision is None:
    # This is the first migration
    pass

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.QueuePool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Use a simple render_id to avoid complex SQLite alterations
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
