from datetime import date
from pydantic import BaseModel
from typing import Optional
from app.enums import TipoLancamento, CategoriaFinanceiro, StatusPagamento, FormaPagamento


class LancamentoCreate(BaseModel):
    tipo            : TipoLancamento
    categoria       : CategoriaFinanceiro
    descricao       : str
    valor           : float
    data_vencimento : date
    forma_pagamento : FormaPagamento
    id_venda        : Optional[int] = None
    observacoes     : Optional[str] = None


class LancamentoUpdate(BaseModel):
    descricao       : Optional[str]             = None
    valor           : Optional[float]           = None
    data_vencimento : Optional[date]            = None
    forma_pagamento : Optional[FormaPagamento]  = None
    observacoes     : Optional[str]             = None


class LancamentoResponse(BaseModel):
    id                   : int
    tipo                 : TipoLancamento
    categoria            : CategoriaFinanceiro
    descricao            : str
    valor                : float
    data_vencimento      : date
    data_pagamento       : Optional[date]
    status_pagamento     : StatusPagamento
    forma_pagamento      : FormaPagamento
    id_venda             : Optional[int]
    lancamento_mestre_id : Optional[int]   = None
    parcela_num          : Optional[int]   = None
    parcela_total        : Optional[int]   = None

    model_config = {"from_attributes": True}
