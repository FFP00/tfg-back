import logging
from logging.config import fileConfig

from sqlmodel import SQLModel

from alembic import context
from app.config.database import engine
from app.config.settings import settings

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)

logger = logging.getLogger(__name__)


def offline() -> None:
    logger.info("Realizando migraciones offline.")

    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=SQLModel.metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def online() -> None:
    logger.info("Realizando migraciones online.")

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=SQLModel.metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    offline()
else:
    online()
