from sqlalchemy import Column, String, Enum, Numeric, Date, Text
from app.database import Base
from app.enums import TipoContrato, StatusColaborador


class Colaborador(Base):
    __tablename__ = "colaboradores"

    id_colaborador      = Column(String(6), primary_key=True)
    nome                = Column(String(150), nullable=False)
    cpf                 = Column(String(14), unique=True, nullable=True)
    cargo               = Column(String(100))
    tipo_contrato       = Column(Enum(TipoContrato), nullable=False)
    percentual_comissao = Column(Numeric(5, 4), nullable=False)
    telefone            = Column(String(20))
    email               = Column(String(100))
    data_admissao       = Column(Date, nullable=False)
    status              = Column(Enum(StatusColaborador), default=StatusColaborador.ATIVO)
    observacoes         = Column(Text)
