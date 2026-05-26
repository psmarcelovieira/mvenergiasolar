from datetime import date
from typing import Optional
from pydantic import BaseModel
from app.enums import StatusProjeto, StatusVistoria


class ProjetoCreate(BaseModel):
    cliente_id      : int
    uc              : Optional[str]   = None
    data_entrada    : Optional[date]  = None
    data_resultado  : Optional[date]  = None
    protocolo       : Optional[str]   = None
    status_projeto  : StatusProjeto   = StatusProjeto.EM_ANALISE
    status_vistoria : StatusVistoria  = StatusVistoria.NAO_SOLICITADO
    kwp             : Optional[float] = None
    inversor        : Optional[str]   = None
    observacoes     : Optional[str]   = None


class ProjetoUpdate(BaseModel):
    uc              : Optional[str]          = None
    data_entrada    : Optional[date]         = None
    data_resultado  : Optional[date]         = None
    protocolo       : Optional[str]          = None
    status_projeto  : Optional[StatusProjeto]  = None
    status_vistoria : Optional[StatusVistoria] = None
    kwp             : Optional[float]        = None
    inversor        : Optional[str]          = None
    observacoes     : Optional[str]          = None


class ProjetoResponse(BaseModel):
    id              : int
    cliente_id      : int
    uc              : Optional[str]
    data_entrada    : Optional[date]
    data_resultado  : Optional[date]
    protocolo       : Optional[str]
    status_projeto  : StatusProjeto
    status_vistoria : StatusVistoria
    kwp             : Optional[float]
    inversor        : Optional[str]
    observacoes     : Optional[str]

    model_config = {"from_attributes": True}
