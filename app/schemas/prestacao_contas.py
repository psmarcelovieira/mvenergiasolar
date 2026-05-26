from datetime import date
from pydantic import BaseModel
from typing import Optional
from app.enums import StatusPrestacao


class PrestacaoResponse(BaseModel):
    id_prestacao        : str
    data                : date
    id_venda            : int
    id_colaborador      : str
    valor_recebido      : float
    custo_instalacao    : float
    percentual_comissao : float
    valor_comissao      : float
    valor_liquido       : float
    status_pagto        : StatusPrestacao
    data_pagto          : Optional[date]

    model_config = {"from_attributes": True}
