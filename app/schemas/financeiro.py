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


class LancamentoResponse(BaseModel):
    id               : int
    tipo             : TipoLancamento
    categoria        : CategoriaFinanceiro
    descricao        : str
    valor            : float
    data_vencimento  : date
    data_pagamento   : Optional[date]
    status_pagamento : StatusPagamento
    forma_pagamento  : FormaPagamento
    id_venda         : Optional[int]

    model_config = {"from_attributes": True}
