from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class CancelamentoVenda(Base):
    __tablename__ = "cancelamentos_venda"

    id                 = Column(Integer, primary_key=True, index=True)
    venda_id           = Column(Integer, ForeignKey("vendas.id"), nullable=False, unique=True)
    solicitante_id     = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    autorizador_id     = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    motivo             = Column(Text, nullable=False)
    data_cancelamento  = Column(DateTime, default=datetime.now, nullable=False)
    estoque_revertido  = Column(Boolean, default=False, nullable=False)
    financeiro_tratado = Column(Boolean, default=False, nullable=False)

    venda       = relationship("Venda",   foreign_keys=[venda_id])
    solicitante = relationship("Usuario", foreign_keys=[solicitante_id])
    autorizador = relationship("Usuario", foreign_keys=[autorizador_id])

    @property
    def solicitante_nome(self) -> str:
        return self.solicitante.nome if self.solicitante else ""

    @property
    def autorizador_nome(self) -> str:
        return self.autorizador.nome if self.autorizador else ""
