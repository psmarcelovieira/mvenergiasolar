from sqlalchemy import Column, Integer, String, Enum, Date, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.database import Base
from app.enums import StatusProjeto, StatusVistoria


class HomologacaoProjeto(Base):
    __tablename__ = "projetos_homologacao"

    id             = Column(Integer, primary_key=True, index=True)
    cliente_id     = Column(Integer, ForeignKey("clientes.id"))
    uc             = Column(String(50))
    data_entrada   = Column(Date)
    data_resultado = Column(Date)
    protocolo      = Column(String(50))
    status_projeto = Column(Enum(StatusProjeto), default=StatusProjeto.EM_ANALISE)
    status_vistoria = Column(Enum(StatusVistoria), default=StatusVistoria.NAO_SOLICITADO)
    kwp            = Column(Numeric(8, 3))
    inversor       = Column(String(100))
    observacoes    = Column(Text)

    cliente = relationship("Cliente", backref="projetos")
