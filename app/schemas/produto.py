from pydantic import BaseModel
from typing import Optional
from app.enums import CategoriaProduto, UnidadeProduto


class ProdutoCreate(BaseModel):
    codigo         : str
    nome           : str
    categoria      : CategoriaProduto
    unidade        : UnidadeProduto
    custo_unitario : float
    preco_venda    : float
    qtd_minima     : int = 0
    fabricante     : Optional[str] = None
    modelo         : Optional[str] = None
    potencia_w     : Optional[float] = None


class ProdutoUpdate(BaseModel):
    nome           : Optional[str]   = None
    categoria      : Optional[CategoriaProduto] = None
    unidade        : Optional[UnidadeProduto]   = None
    custo_unitario : Optional[float] = None
    preco_venda    : Optional[float] = None
    qtd_minima     : Optional[int]   = None
    fabricante     : Optional[str]   = None
    modelo         : Optional[str]   = None
    potencia_w     : Optional[float] = None


class ProdutoResponse(BaseModel):
    id             : int
    codigo         : str
    nome           : str
    categoria      : CategoriaProduto
    unidade        : UnidadeProduto
    custo_unitario : float
    preco_venda    : float
    qtd_minima     : int
    fabricante     : Optional[str]
    modelo         : Optional[str]
    potencia_w     : Optional[float]
    margem_pct     : float
    qtd_estoque    : float
    alerta_estoque : bool


    model_config = {"from_attributes": True}
