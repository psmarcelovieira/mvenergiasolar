from sqlalchemy import Column, Integer, String, Enum, Date, Numeric
from app.database import Base
from app.enums import StatusCliente, TipoPessoa, Escolaridade, TipoImovel, OrigemLead


class Cliente(Base):
    __tablename__ = "clientes"

    id            = Column(Integer, primary_key=True, index=True)
    status        = Column(Enum(StatusCliente), default=StatusCliente.ATIVO, nullable=False)
    tipo_pessoa   = Column(Enum(TipoPessoa), default=TipoPessoa.PF, nullable=False)
    nome          = Column(String(150), nullable=False)
    cpf_cnpj      = Column(String(14), unique=True)
    email         = Column(String(100))
    telefone      = Column(String(20))
    cidade        = Column(String(100))
    uf            = Column(String(2))
    data_cadastro = Column(Date, nullable=False)

    # Perfil para análise de vendas
    profissao     = Column(String(100))
    renda_mensal  = Column(Numeric(12, 2))
    escolaridade  = Column(Enum(Escolaridade))
    conta_energia = Column(Numeric(10, 2))
    tipo_imovel   = Column(Enum(TipoImovel))
    origem_lead   = Column(Enum(OrigemLead))
    endereco      = Column(String(200))
    bairro        = Column(String(100))
