from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.enums import PerfilUsuario

MAX_TENTATIVAS = 5
BLOQUEIO_MINUTOS = 5


class Usuario(Base):
    __tablename__ = "usuarios"

    id               = Column(Integer, primary_key=True, index=True)
    nome             = Column(String(100), nullable=False)
    login            = Column(String(50),  nullable=False, unique=True)
    senha_hash       = Column(String(200), nullable=False)
    perfil           = Column(Enum(PerfilUsuario), nullable=False, default=PerfilUsuario.VENDEDOR)
    colaborador_id   = Column(String(6), ForeignKey("colaboradores.id_colaborador"), nullable=True)
    ultimo_login     = Column(DateTime, nullable=True)
    tentativas_falhas = Column(Integer, nullable=False, default=0)
    bloqueado_ate    = Column(DateTime, nullable=True)

    colaborador = relationship("Colaborador", foreign_keys=[colaborador_id])
