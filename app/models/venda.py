from sqlalchemy import Column, Integer, ForeignKey, Date, Numeric, Enum, Text, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.enums import StatusVenda, FormaPagamento


class Venda(Base):
    __tablename__ = "vendas"

    id               = Column(Integer, primary_key=True, index=True)
    cliente_id       = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    data_orcamento   = Column(Date, nullable=False)
    data_aprovacao   = Column(Date, nullable=True)
    status_venda     = Column(Enum(StatusVenda), default=StatusVenda.ORCAMENTO, nullable=False)
    valor_instalacao = Column(Numeric(10, 2), default=0)
    desconto         = Column(Numeric(10, 2), default=0)
    forma_pagamento  = Column(Enum(FormaPagamento), nullable=False)
    parcelas         = Column(Integer, default=1)
    observacoes      = Column(Text)
    id_responsavel = Column(String(6), ForeignKey("colaboradores.id_colaborador"), nullable=True)

    cliente     = relationship("Cliente")
    itens       = relationship("ItemVenda", back_populates="venda")
    responsavel = relationship("Colaborador")

    @property
    def valor_equipamentos(self):
        return sum(item.subtotal for item in self.itens)

    @property
    def valor_final(self):
        return self.valor_equipamentos + float(self.valor_instalacao or 0) - float(self.desconto or 0)
