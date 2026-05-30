"""auth_profissional_usuarios

Revision ID: b7e2a4f1c5d3
Revises: a3f8c1d2e9b0
Create Date: 2026-05-27 00:01:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = 'b7e2a4f1c5d3'
down_revision: Union[str, Sequence[str], None] = 'a3f8c1d2e9b0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if 'usuarios' not in inspector.get_table_names():
        return  # tabela será criada pelo create_all com o schema atual

    existing = {c['name'] for c in inspector.get_columns('usuarios')}

    if 'colaborador_id' not in existing:
        # FK constraint omitido: não suportado em ALTER TABLE no SQLite.
        # PostgreSQL recebe o FK via create_all no banco novo; ORM declara o relacionamento.
        op.add_column('usuarios', sa.Column('colaborador_id', sa.String(6), nullable=True))
    if 'ultimo_login' not in existing:
        op.add_column('usuarios', sa.Column('ultimo_login', sa.DateTime(), nullable=True))
    if 'tentativas_falhas' not in existing:
        op.add_column('usuarios', sa.Column('tentativas_falhas', sa.Integer(), nullable=False,
                                            server_default='0'))
    if 'bloqueado_ate' not in existing:
        op.add_column('usuarios', sa.Column('bloqueado_ate', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('usuarios', 'bloqueado_ate')
    op.drop_column('usuarios', 'tentativas_falhas')
    op.drop_column('usuarios', 'ultimo_login')
    op.drop_column('usuarios', 'colaborador_id')
