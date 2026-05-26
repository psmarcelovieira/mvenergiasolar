from sqlalchemy import Column, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.database import Base


class ItemVenda(Base):
    __tablename__ = "itens_venda"

    id             = Column(Integer, primary_key=True, index=True)
    venda_id       = Column(Integer, ForeignKey("vendas.id"), nullable=False)
    produto_id     = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade     = Column(Numeric(10, 3), nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)

    venda   = relationship("Venda", back_populates="itens")
    produto = relationship("Produto")

    @property
    def subtotal(self):
        return float(self.quantidade) * float(self.preco_unitario)
