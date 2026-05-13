# 1. Todas las importaciones arriba (Corrige E402)
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

import app.database.model  # noqa: F401
from alembic import context
from app.settings import settings

# Obtener el objeto de configuración de Alembic
config = context.config

# 2. Configuración de logging sin usar 'assert' (Corrige S101)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
else:
    # Opcional: manejar el error si el archivo no existe
    pass

# Definir el metadata para autogenerate
target_metadata = SQLModel.metadata

def get_url() -> str:
    return str(settings.SQLALCHEMY_DATABASE_URI)

def run_migrations_offline():
    """Ejecutar migraciones en modo 'offline'."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Ejecutar migraciones en modo 'online'."""
    # Asegurar que obtenemos la sección de configuración
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
