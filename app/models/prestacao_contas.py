from sqlalchemy import Column, String, Integer, ForeignKey, Numeric, Date, Enum, Text
from sqlalchemy.orm import relationship
from app.database import Base
from app.enums import StatusPrestacao


class PrestacaoContas(Base):
    __tablename__ = "prestacao_contas"

    id_prestacao        = Column(String(7), primary_key=True)
    data                = Column(Date, nullable=False)
    id_venda            = Column(Integer, ForeignKey("vendas.id"), nullable=False)
    id_colaborador      = Column(String(6), ForeignKey("colaboradores.id_colaborador"), nullable=False)
    valor_recebido      = Column(Numeric(10, 2), nullable=False)
    custo_instalacao    = Column(Numeric(10, 2), default=0)
    percentual_comissao = Column(Numeric(5, 4), nullable=False)
    status_pagto        = Column(Enum(StatusPrestacao), default=StatusPrestacao.PENDENTE)
    data_pagto          = Column(Date, nullable=True)
    observacoes         = Column(Text)

    venda        = relationship("Venda")
    colaborador  = relationship("Colaborador")

    @property
    def valor_comissao(self):
        return round(float(self.valor_recebido) * float(self.percentual_comissao), 2)

    @property
    def valor_liquido(self):
        return float(self.valor_recebido) - self.valor_comissao
