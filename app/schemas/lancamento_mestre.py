from datetime import date, datetime
from pydantic import BaseModel, model_validator
from typing import Optional
from app.enums import TipoLancamento, CategoriaFinanceiro, TipoRecorrencia, FormaPagamento
from app.schemas.financeiro import LancamentoResponse


class LancamentoMestreCreate(BaseModel):
    descricao        : str
    tipo             : TipoLancamento
    categoria        : CategoriaFinanceiro
    tipo_recorrencia : TipoRecorrencia = TipoRecorrencia.UNICO
    valor            : float
    num_parcelas     : Optional[int]  = None
    intervalo_meses  : int            = 1
    data_inicio      : date
    data_fim         : Optional[date] = None
    forma_pagamento  : FormaPagamento
    observacoes      : Optional[str]  = None

    @model_validator(mode="after")
    def valida_campos(self):
        if self.tipo_recorrencia == TipoRecorrencia.PARCELADO:
            if not self.num_parcelas or self.num_parcelas < 2:
                raise ValueError("Parcelado exige num_parcelas >= 2")
        if self.intervalo_meses < 1:
            raise ValueError("intervalo_meses deve ser >= 1")
        return self


class ParcelasEditarRequest(BaseModel):
    novo_valor      : Optional[float] = None
    nova_descricao  : Optional[str]   = None
    a_partir_de     : Optional[date]  = None


class CancelarSerieRequest(BaseModel):
    a_partir_de : Optional[date] = None


class LancamentoMestreResponse(BaseModel):
    id               : int
    descricao        : str
    tipo             : TipoLancamento
    categoria        : CategoriaFinanceiro
    tipo_recorrencia : TipoRecorrencia
    valor            : float
    num_parcelas     : Optional[int]
    intervalo_meses  : int
    data_inicio      : date
    data_fim         : Optional[date]
    forma_pagamento  : FormaPagamento
    observacoes      : Optional[str]
    ativo            : bool
    criado_em        : datetime
    parcelas         : list[LancamentoResponse] = []

    model_config = {"from_attributes": True}
