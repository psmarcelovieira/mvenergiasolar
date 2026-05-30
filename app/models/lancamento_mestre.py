from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Enum, Date, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from app.enums import TipoLancamento, CategoriaFinanceiro, TipoRecorrencia, FormaPagamento


class LancamentoMestre(Base):
    __tablename__ = "lancamentos_mestre"

    id               = Column(Integer, primary_key=True, index=True)
    descricao        = Column(String(200), nullable=False)
    tipo             = Column(Enum(TipoLancamento), nullable=False)
    categoria        = Column(Enum(CategoriaFinanceiro), nullable=False)
    tipo_recorrencia = Column(Enum(TipoRecorrencia), nullable=False, default=TipoRecorrencia.UNICO)
    valor            = Column(Numeric(10, 2), nullable=False)
    num_parcelas     = Column(Integer, nullable=True)
    intervalo_meses  = Column(Integer, default=1, nullable=False)
    data_inicio      = Column(Date, nullable=False)
    data_fim         = Column(Date, nullable=True)
    forma_pagamento  = Column(Enum(FormaPagamento), nullable=False)
    observacoes      = Column(Text, nullable=True)
    ativo            = Column(Boolean, default=True, nullable=False)
    criado_em        = Column(DateTime, default=datetime.now)

    parcelas = relationship(
        "Financeiro",
        back_populates="lancamento_mestre",
        order_by="Financeiro.data_vencimento",
    )
