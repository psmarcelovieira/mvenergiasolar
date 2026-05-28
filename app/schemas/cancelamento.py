from datetime import datetime
from pydantic import BaseModel, field_validator


class CancelamentoRequest(BaseModel):
    solicitante_login : str
    autorizador_login : str
    autorizador_senha : str
    motivo            : str

    @field_validator("motivo")
    @classmethod
    def motivo_nao_vazio(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("Motivo deve ter pelo menos 10 caracteres")
        return v.strip()


class CancelamentoResponse(BaseModel):
    id                 : int
    venda_id           : int
    motivo             : str
    data_cancelamento  : datetime
    estoque_revertido  : bool
    financeiro_tratado : bool
    solicitante_nome   : str
    autorizador_nome   : str

    model_config = {"from_attributes": True}
