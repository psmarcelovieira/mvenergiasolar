"""financeiro_parcelado

Revision ID: e4f6a8b2c0d1
Revises: a3f8c1d2e9b0
Create Date: 2026-05-29 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = 'e4f6a8b2c0d1'
down_revision: Union[str, Sequence[str], None] = 'b7e2a4f1c5d3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    # Banco novo: create_all() cria tudo com o schema atual — não há nada a fazer
    if 'financeiro' not in tables:
        return

    # ── 1. Cria tabela lancamentos_mestre ──────────────────────────────────────
    if 'lancamentos_mestre' not in tables:
        op.create_table(
            'lancamentos_mestre',
            sa.Column('id',               sa.Integer(),     nullable=False),
            sa.Column('descricao',        sa.String(200),   nullable=False),
            sa.Column('tipo',             sa.String(50),    nullable=False),
            sa.Column('categoria',        sa.String(50),    nullable=False),
            sa.Column('tipo_recorrencia', sa.String(20),    nullable=False, server_default='Único'),
            sa.Column('valor',            sa.Numeric(10,2), nullable=False),
            sa.Column('num_parcelas',     sa.Integer(),     nullable=True),
            sa.Column('intervalo_meses',  sa.Integer(),     nullable=False, server_default='1'),
            sa.Column('data_inicio',      sa.Date(),        nullable=False),
            sa.Column('data_fim',         sa.Date(),        nullable=True),
            sa.Column('forma_pagamento',  sa.String(30),    nullable=False),
            sa.Column('observacoes',      sa.Text(),        nullable=True),
            sa.Column('ativo',            sa.Boolean(),     nullable=False, server_default='true'),
            sa.Column('criado_em',        sa.DateTime(),    nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_lancamentos_mestre_id', 'lancamentos_mestre', ['id'])

    # ── 2. Adiciona colunas em financeiro ─────────────────────────────────────
    existing_cols = {c['name'] for c in inspector.get_columns('financeiro')}

    if 'lancamento_mestre_id' not in existing_cols:
        # FK omitido: não suportado em ALTER TABLE no SQLite.
        op.add_column('financeiro', sa.Column('lancamento_mestre_id', sa.Integer(), nullable=True))

    if 'parcela_num' not in existing_cols:
        op.add_column('financeiro', sa.Column('parcela_num',   sa.Integer(), nullable=True))

    if 'parcela_total' not in existing_cols:
        op.add_column('financeiro', sa.Column('parcela_total', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('financeiro', 'parcela_total')
    op.drop_column('financeiro', 'parcela_num')
    op.drop_column('financeiro', 'lancamento_mestre_id')
    op.drop_index('ix_lancamentos_mestre_id', table_name='lancamentos_mestre')
    op.drop_table('lancamentos_mestre')
