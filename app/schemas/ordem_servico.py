from datetime import date
from typing import Optional
from pydantic import BaseModel
from app.enums import TipoServico, StatusOS, FormaPagamento


class OSCreate(BaseModel):
    cliente_id       : int
    id_tecnico       : Optional[str]        = None
    tipo_servico     : TipoServico
    descricao        : str
    data_abertura    : date
    data_agendamento : Optional[date]       = None
    forma_pagamento  : FormaPagamento       = FormaPagamento.PIX
    custo_total      : Optional[float]      = None
    observacoes      : Optional[str]        = None


class OSUpdate(BaseModel):
    id_tecnico       : Optional[str]        = None
    tipo_servico     : Optional[TipoServico]  = None
    descricao        : Optional[str]        = None
    status_os        : Optional[StatusOS]   = None
    data_agendamento : Optional[date]       = None
    data_conclusao   : Optional[date]       = None
    forma_pagamento  : Optional[FormaPagamento] = None
    custo_total      : Optional[float]      = None
    observacoes      : Optional[str]        = None


class OSResponse(BaseModel):
    id_os            : str
    cliente_id       : int
    id_tecnico       : Optional[str]
    tipo_servico     : TipoServico
    descricao        : str
    status_os        : StatusOS
    data_abertura    : date
    data_agendamento : Optional[date]
    data_conclusao   : Optional[date]
    forma_pagamento  : Optional[FormaPagamento]
    custo_total      : Optional[float]
    observacoes      : Optional[str]

    model_config = {"from_attributes": True}
