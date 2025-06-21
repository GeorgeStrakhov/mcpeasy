import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Add the src directory to the path so we can import our models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import our models
from src.models import Base

# Auto-discover and import custom models from submodules
def discover_custom_models():
    """
    Discover and import custom models from submodules to include in metadata.
    This ensures custom models are included in Alembic autogeneration.
    """
    import importlib
    from pathlib import Path
    
    # Search for models.py files in custom submodules
    custom_paths = [
        Path("src/custom_tools"),
        Path("src/custom_resources")
    ]
    
    for custom_path in custom_paths:
        if not custom_path.exists():
            continue
            
        # Scan each organization's submodule
        for org_dir in custom_path.iterdir():
            if org_dir.is_dir() and not org_dir.name.startswith('.'):
                models_file = org_dir / "models.py"
                if models_file.exists():
                    try:
                        # Import the custom models module
                        module_path = f"{custom_path.name}.{org_dir.name}.models"
                        importlib.import_module(module_path)
                        print(f"Discovered custom models: {module_path}")
                    except ImportError as e:
                        print(f"Warning: Could not import {module_path}: {e}")
                    except Exception as e:
                        print(f"Error importing {module_path}: {e}")

# Discover custom models to include in metadata
discover_custom_models()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

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


def get_database_url():
    """Get database URL from environment variable"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    # Convert postgresql:// to postgresql+asyncpg:// for alembic compatibility
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql://", 1)
    
    return database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
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
    # Get database URL and set it in config
    database_url = get_database_url()
    config.set_main_option("sqlalchemy.url", database_url)
    
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