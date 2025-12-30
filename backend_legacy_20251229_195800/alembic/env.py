import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Pridať backend adresár do sys.path, aby sme mohli importovať services
# env.py je v backend/alembic/, takže potrebujeme ísť o úroveň vyššie do backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from services.database import Base, DATABASE_URL
from services.auth import User  # noqa: F401
from services.api_keys import ApiKey  # noqa: F401
from services.webhooks import Webhook  # noqa: F401
try:
    from services.erp.models import ErpConnection, ErpSyncLog  # noqa: F401
except ImportError:
    pass

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Prepísať sqlalchemy.url v konfigurácii na hodnotu z database.py
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
