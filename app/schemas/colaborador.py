from datetime import date
from pydantic import BaseModel
from typing import Optional
from app.enums import TipoContrato, StatusColaborador


class ColaboradorCreate(BaseModel):
    nome                : str
    cpf                 : Optional[str] = None
    cargo               : Optional[str] = None
    tipo_contrato       : TipoContrato
    percentual_comissao : float
    telefone            : Optional[str] = None
    email               : Optional[str] = None
    data_admissao       : date


class ColaboradorUpdate(BaseModel):
    nome                : Optional[str]              = None
    cargo               : Optional[str]              = None
    tipo_contrato       : Optional[TipoContrato]     = None
    percentual_comissao : Optional[float]            = None
    telefone            : Optional[str]              = None
    email               : Optional[str]              = None
    status              : Optional[StatusColaborador] = None


class ColaboradorResponse(BaseModel):
    id_colaborador      : str
    nome                : str
    cpf                 : Optional[str]
    cargo               : Optional[str]
    tipo_contrato       : TipoContrato
    percentual_comissao : float
    telefone            : Optional[str]
    email               : Optional[str]
    data_admissao       : date
    status              : StatusColaborador

    model_config = {"from_attributes": True}
