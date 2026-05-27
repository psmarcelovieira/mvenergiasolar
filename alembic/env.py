from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Normaliza DATABASE_URL antes de importar app.database (que cria o engine no nível do módulo).
# Garante que um valor inválido ou vazio no env var não cause crash na importação.
_raw_url = os.getenv("DATABASE_URL") or "sqlite:///./solar.db"
_db_url = _raw_url.replace("postgres://", "postgresql://", 1)
os.environ["DATABASE_URL"] = _db_url
config.set_main_option("sqlalchemy.url", _db_url)

# Importa Base e todos os modelos para que o autogenerate os enxergue
from app.database import Base
from app.models import (  # noqa: F401
    cliente, produto, venda, item_venda, colaborador,
    estoque, financeiro, prestacao_contas, projeto, ordem_servico, usuario,
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,   # necessário para SQLite
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
            render_as_batch=True,   # necessário para SQLite
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
