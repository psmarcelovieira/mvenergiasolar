from sqlalchemy import Column, Integer, ForeignKey, Numeric, Enum, Date, String, Text
from sqlalchemy.orm import relationship
from app.database import Base
from app.enums import TipoLancamento, CategoriaFinanceiro, StatusPagamento, FormaPagamento


class Financeiro(Base):
    __tablename__ = "financeiro"

    id               = Column(Integer, primary_key=True, index=True)
    tipo             = Column(Enum(TipoLancamento), nullable=False)
    categoria        = Column(Enum(CategoriaFinanceiro), nullable=False)
    descricao        = Column(String(200), nullable=False)
    valor            = Column(Numeric(10, 2), nullable=False)
    data_vencimento  = Column(Date, nullable=False)
    data_pagamento   = Column(Date, nullable=True)
    status_pagamento = Column(Enum(StatusPagamento), default=StatusPagamento.PENDENTE)
    forma_pagamento  = Column(Enum(FormaPagamento), nullable=False)
    id_venda         = Column(Integer, ForeignKey("vendas.id"), nullable=True)
    observacoes      = Column(Text)

    venda = relationship("Venda")
