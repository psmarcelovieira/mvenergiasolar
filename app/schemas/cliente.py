from datetime import date
from typing import Optional
from pydantic import BaseModel, field_validator
from app.enums import StatusCliente, TipoPessoa, Escolaridade, TipoImovel, OrigemLead


class ClienteCreate(BaseModel):
    tipo_pessoa   : TipoPessoa = TipoPessoa.PF
    nome          : str
    cpf_cnpj      : Optional[str]  = None
    email         : Optional[str]  = None
    telefone      : Optional[str]  = None
    cidade        : Optional[str]  = None
    uf            : Optional[str]  = None
    profissao     : Optional[str]          = None
    renda_mensal  : Optional[float]        = None
    escolaridade  : Optional[Escolaridade] = None
    conta_energia : Optional[float]        = None
    tipo_imovel   : Optional[TipoImovel]   = None
    origem_lead   : Optional[OrigemLead]   = None
    endereco      : Optional[str]          = None
    bairro        : Optional[str]          = None

    @field_validator("cpf_cnpj")
    @classmethod
    def validar_cpf_cnpj(cls, v):
        if v is None:
            return v
        digitos = "".join(filter(str.isdigit, v))
        if len(digitos) not in (11, 14):
            raise ValueError("CPF deve ter 11 dígitos ou CNPJ 14 dígitos")
        return digitos


class ClienteUpdate(BaseModel):
    nome          : Optional[str]           = None
    email         : Optional[str]           = None
    telefone      : Optional[str]           = None
    cidade        : Optional[str]           = None
    uf            : Optional[str]           = None
    status        : Optional[StatusCliente] = None
    profissao     : Optional[str]           = None
    renda_mensal  : Optional[float]         = None
    escolaridade  : Optional[Escolaridade]  = None
    conta_energia : Optional[float]         = None
    tipo_imovel   : Optional[TipoImovel]    = None
    origem_lead   : Optional[OrigemLead]    = None
    endereco      : Optional[str]           = None
    bairro        : Optional[str]           = None


class ClienteResponse(BaseModel):
    id            : int
    status        : StatusCliente
    tipo_pessoa   : TipoPessoa
    nome          : str
    cpf_cnpj      : Optional[str]
    email         : Optional[str]
    telefone      : Optional[str]
    cidade        : Optional[str]
    uf            : Optional[str]
    data_cadastro : date
    profissao     : Optional[str]
    renda_mensal  : Optional[float]
    escolaridade  : Optional[Escolaridade]
    conta_energia : Optional[float]
    tipo_imovel   : Optional[TipoImovel]
    origem_lead   : Optional[OrigemLead]
    endereco      : Optional[str]
    bairro        : Optional[str]

    model_config = {"from_attributes": True}
