from sqlalchemy import Column, Integer, String, Enum, Numeric
from sqlalchemy.orm import relationship
from app.database import Base
from app.enums import CategoriaProduto, UnidadeProduto


class Produto(Base):
    __tablename__ = "produtos"

    id             = Column(Integer, primary_key=True, index=True)
    codigo         = Column(String(20), unique=True, nullable=False)
    nome           = Column(String(150), nullable=False)
    categoria      = Column(Enum(CategoriaProduto), nullable=False)
    unidade        = Column(Enum(UnidadeProduto), nullable=False)
    fabricante     = Column(String(100))
    modelo         = Column(String(100))
    potencia_w     = Column(Numeric(10, 2))
    custo_unitario = Column(Numeric(10, 2), nullable=False)
    preco_venda    = Column(Numeric(10, 2), nullable=False)
    qtd_minima     = Column(Integer, default=0)

    movimentacoes = relationship("EstoqueMovimentacao", back_populates="produto")

    @property
    def margem_pct(self):
        if not self.preco_venda or self.preco_venda == 0:
            return 0
        return round((self.preco_venda - self.custo_unitario) / self.preco_venda, 4)

    @property
    def qtd_estoque(self):
        return sum(m.quantidade * m.sinal for m in self.movimentacoes)

    @property
    def alerta_estoque(self):
        return self.qtd_estoque < self.qtd_minima
