from sqlalchemy import Column, String, Integer, Enum, Date, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.database import Base
from app.enums import TipoServico, StatusOS, FormaPagamento


class OrdemServico(Base):
    __tablename__ = "ordens_servico"

    id_os            = Column(String(6), primary_key=True)
    cliente_id       = Column(Integer, ForeignKey("clientes.id"))
    id_tecnico       = Column(String(6), ForeignKey("colaboradores.id_colaborador"))
    tipo_servico     = Column(Enum(TipoServico), nullable=False)
    descricao        = Column(Text, nullable=False)
    status_os        = Column(Enum(StatusOS), default=StatusOS.ABERTA, nullable=False)
    data_abertura    = Column(Date, nullable=False)
    data_agendamento = Column(Date)
    data_conclusao   = Column(Date)
    forma_pagamento  = Column(Enum(FormaPagamento), default=FormaPagamento.PIX)
    custo_total      = Column(Numeric(10, 2))
    observacoes      = Column(Text)

    cliente = relationship("Cliente",      backref="ordens_servico")
    tecnico = relationship("Colaborador",  backref="ordens_servico")
