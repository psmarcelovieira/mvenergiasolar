from datetime import date
from pydantic import BaseModel, field_validator
from typing import Optional
from app.enums import StatusVenda, FormaPagamento


class ItemVendaCreate(BaseModel):
    produto_id     : int
    quantidade     : float
    preco_unitario : Optional[float] = None

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, v):
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return v



class ItemVendaResponse(BaseModel):
    id             : int
    produto_id     : int
    quantidade     : float
    preco_unitario : float
    subtotal       : float

    model_config = {"from_attributes": True}


class VendaCreate(BaseModel):
    cliente_id       : int
    id_responsavel : Optional[str] = None
    valor_instalacao : float = 0
    desconto         : float = 0
    forma_pagamento  : FormaPagamento
    parcelas         : int = 1
    observacoes      : Optional[str] = None
    itens            : list[ItemVendaCreate]


class VendaResponse(BaseModel):
    id               : int
    cliente_id       : int
    id_responsavel : Optional[str]
    data_orcamento   : date
    status_venda     : StatusVenda
    valor_instalacao : float
    desconto         : float
    forma_pagamento  : FormaPagamento
    parcelas         : int
    itens            : list[ItemVendaResponse]
    valor_equipamentos : float
    valor_final        : float

    model_config = {"from_attributes": True}
