"""auth_profissional_usuarios

Revision ID: b7e2a4f1c5d3
Revises: a3f8c1d2e9b0
Create Date: 2026-05-27 00:01:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b7e2a4f1c5d3'
down_revision: Union[str, Sequence[str], None] = 'a3f8c1d2e9b0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column(
        'colaborador_id', sa.String(6),
        sa.ForeignKey('colaboradores.id_colaborador'),
        nullable=True,
    ))
    op.add_column('usuarios', sa.Column('ultimo_login',      sa.DateTime(), nullable=True))
    op.add_column('usuarios', sa.Column('tentativas_falhas', sa.Integer(),  nullable=False,
                                        server_default='0'))
    op.add_column('usuarios', sa.Column('bloqueado_ate',     sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('usuarios', 'bloqueado_ate')
    op.drop_column('usuarios', 'tentativas_falhas')
    op.drop_column('usuarios', 'ultimo_login')
    op.drop_column('usuarios', 'colaborador_id')
