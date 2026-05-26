from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Enum, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base
from app.enums import TipoMovimento

TIPOS_POSITIVOS = {TipoMovimento.ENTRADA, TipoMovimento.AJUSTE_POSITIVO}


class EstoqueMovimentacao(Base):
    __tablename__ = "estoque_movimentacoes"

    id             = Column(Integer, primary_key=True, index=True)
    data           = Column(DateTime, default=datetime.now, nullable=False)
    tipo_mov       = Column(Enum(TipoMovimento), nullable=False)
    id_produto     = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade     = Column(Numeric(10, 3), nullable=False)
    valor_unitario = Column(Numeric(10, 2), nullable=False)
    id_venda       = Column(Integer, ForeignKey("vendas.id"), nullable=True)
    responsavel    = Column(String(150))
    observacoes    = Column(Text)

    produto = relationship("Produto", back_populates="movimentacoes")
    venda   = relationship("Venda")

    @property
    def sinal(self):
        return 1 if self.tipo_mov in TIPOS_POSITIVOS else -1

    @property
    def valor_total(self):
        return float(self.quantidade) * float(self.valor_unitario)
