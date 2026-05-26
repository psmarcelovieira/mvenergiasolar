from sqlalchemy import Column, Integer, String, Enum
from app.database import Base
from app.enums import PerfilUsuario


class Usuario(Base):
    __tablename__ = "usuarios"

    id        = Column(Integer, primary_key=True, index=True)
    nome      = Column(String(100), nullable=False)
    login     = Column(String(50),  nullable=False, unique=True)
    senha_hash = Column(String(200), nullable=False)
    perfil    = Column(Enum(PerfilUsuario), nullable=False, default=PerfilUsuario.VENDEDOR)
