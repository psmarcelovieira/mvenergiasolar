"""add_cancelamentos_venda

Revision ID: a3f8c1d2e9b0
Revises: d8111f366e8c
Create Date: 2026-05-27 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = 'a3f8c1d2e9b0'
down_revision: Union[str, Sequence[str], None] = 'd8111f366e8c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = inspect(bind).get_table_names()
    # Banco novo: vendas ainda não existe (create_all vai criar tudo com o schema atual)
    if 'vendas' not in tables or 'usuarios' not in tables:
        return
    if 'cancelamentos_venda' not in tables:
        op.create_table(
            'cancelamentos_venda',
            sa.Column('id',                 sa.Integer(),   nullable=False),
            sa.Column('venda_id',           sa.Integer(),   nullable=False),
            sa.Column('solicitante_id',     sa.Integer(),   nullable=False),
            sa.Column('autorizador_id',     sa.Integer(),   nullable=False),
            sa.Column('motivo',             sa.Text(),      nullable=False),
            sa.Column('data_cancelamento',  sa.DateTime(),  nullable=False),
            sa.Column('estoque_revertido',  sa.Boolean(),   nullable=False, server_default='false'),
            sa.Column('financeiro_tratado', sa.Boolean(),   nullable=False, server_default='false'),
            sa.ForeignKeyConstraint(['venda_id'],       ['vendas.id']),
            sa.ForeignKeyConstraint(['solicitante_id'], ['usuarios.id']),
            sa.ForeignKeyConstraint(['autorizador_id'], ['usuarios.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('venda_id'),
        )
        op.create_index('ix_cancelamentos_venda_id', 'cancelamentos_venda', ['id'])


def downgrade() -> None:
    op.drop_index('ix_cancelamentos_venda_id', table_name='cancelamentos_venda')
    op.drop_table('cancelamentos_venda')
