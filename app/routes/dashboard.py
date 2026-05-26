from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.venda import Venda
from app.models.produto import Produto
from app.models.financeiro import Financeiro
from app.enums import StatusVenda, StatusPagamento, TipoLancamento

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/")
def get_dashboard(db: Session = Depends(get_db)):
    todas_vendas     = db.query(Venda).all()
    vendas_aprovadas = [v for v in todas_vendas if v.status_venda == StatusVenda.APROVADO]
    vendas_pipeline  = [v for v in todas_vendas if v.status_venda in (
        StatusVenda.ORCAMENTO, StatusVenda.NEGOCIACAO
    )]

    receita_aprovada = sum(v.valor_final for v in vendas_aprovadas)
    pipeline         = sum(v.valor_final for v in vendas_pipeline)
    ticket_medio     = receita_aprovada / len(vendas_aprovadas) if vendas_aprovadas else 0

    lancamentos_pagos = db.query(Financeiro).filter(
        Financeiro.status_pagamento == StatusPagamento.PAGO
    ).all()
    receitas_pagas = sum(float(l.valor) for l in lancamentos_pagos if l.tipo == TipoLancamento.RECEITA)
    despesas_pagas = sum(float(l.valor) for l in lancamentos_pagos if l.tipo == TipoLancamento.DESPESA)

    produtos       = db.query(Produto).all()
    itens_em_alerta = sum(1 for p in produtos if p.alerta_estoque)
    valor_estoque   = sum(float(p.custo_unitario) * float(p.qtd_estoque) for p in produtos)

    return {
        "total_vendas"    : len(todas_vendas),
        "receita_aprovada": round(receita_aprovada, 2),
        "pipeline"        : round(pipeline, 2),
        "saldo_financeiro": round(receitas_pagas - despesas_pagas, 2),
        "ticket_medio"    : round(ticket_medio, 2),
        "itens_em_alerta" : itens_em_alerta,
        "valor_em_estoque": round(valor_estoque, 2),
    }
