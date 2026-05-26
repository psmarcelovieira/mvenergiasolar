from datetime import datetime
from pydantic import BaseModel, field_validator
from typing import Optional
from app.enums import TipoMovimento


class MovimentacaoCreate(BaseModel):
    tipo_mov       : TipoMovimento
    id_produto     : int
    quantidade     : float
    valor_unitario : float
    id_venda       : Optional[int] = None
    responsavel    : Optional[str] = None
    observacoes    : Optional[str] = None

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, v):
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return v


class MovimentacaoResponse(BaseModel):
    id             : int
    data           : datetime
    tipo_mov       : TipoMovimento
    id_produto     : int
    quantidade     : float
    valor_unitario : float
    sinal          : int
    valor_total    : float
    id_venda       : Optional[int]
    responsavel    : Optional[str]

    model_config = {"from_attributes": True}
