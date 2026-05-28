from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.enums import PerfilUsuario


class UsuarioCreate(BaseModel):
    nome:           str
    login:          str
    senha:          str
    perfil:         PerfilUsuario = PerfilUsuario.VENDEDOR
    colaborador_id: Optional[str] = None


class UsuarioUpdate(BaseModel):
    nome:           Optional[str]           = None
    login:          Optional[str]           = None
    senha:          Optional[str]           = None
    perfil:         Optional[PerfilUsuario] = None
    colaborador_id: Optional[str]           = None


class UsuarioResponse(BaseModel):
    id:             int
    nome:           str
    login:          str
    perfil:         PerfilUsuario
    colaborador_id: Optional[str]      = None
    ultimo_login:   Optional[datetime] = None

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    login: str
    senha: str
