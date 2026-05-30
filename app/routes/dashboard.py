from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.venda import Venda
from app.models.produto import Produto
from app.models.financeiro import Financeiro
from app.enums import StatusVenda, StatusPagamento, TipoLancamento

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/")
def get_dashboard(db: Session = Depends(get_db)):
    todas_vendas     = db.query(Venda).filter(Venda.status_venda != StatusVenda.CANCELADO).all()
    vendas_aprovadas = [v for v in todas_vendas if v.status_venda == StatusVenda.APROVADO]
    vendas_pipeline  = [v for v in todas_vendas if v.status_venda in (
        StatusVenda.ORCAMENTO, StatusVenda.NEGOCIACAO
    )]

    receita_aprovada = sum(v.valor_final for v in vendas_aprovadas)
    pipeline         = sum(v.valor_final for v in vendas_pipeline)
    ticket_medio     = receita_aprovada / len(vendas_aprovadas) if vendas_aprovadas else 0

    todos_lancamentos = db.query(Financeiro).all()
    pagos             = [l for l in todos_lancamentos if l.status_pagamento == StatusPagamento.PAGO]
    pendentes         = [l for l in todos_lancamentos if l.status_pagamento == StatusPagamento.PENDENTE]

    receitas_pagas   = sum(float(l.valor) for l in pagos     if l.tipo == TipoLancamento.RECEITA)
    despesas_pagas   = sum(float(l.valor) for l in pagos     if l.tipo == TipoLancamento.DESPESA)
    contas_a_receber = sum(float(l.valor) for l in pendentes if l.tipo == TipoLancamento.RECEITA)
    contas_a_pagar   = sum(float(l.valor) for l in pendentes if l.tipo == TipoLancamento.DESPESA)

    produtos        = db.query(Produto).all()
    itens_em_alerta = sum(1 for p in produtos if p.alerta_estoque)
    valor_estoque   = sum(float(p.custo_unitario) * float(p.qtd_estoque) for p in produtos)

    return {
        "total_vendas"     : len(todas_vendas),
        "receita_aprovada" : round(receita_aprovada, 2),
        "pipeline"         : round(pipeline, 2),
        "saldo_financeiro" : round(receitas_pagas - despesas_pagas, 2),
        "ticket_medio"     : round(ticket_medio, 2),
        "itens_em_alerta"  : itens_em_alerta,
        "valor_em_estoque" : round(valor_estoque, 2),
        "contas_a_receber" : round(contas_a_receber, 2),
        "contas_a_pagar"   : round(contas_a_pagar, 2),
    }


@router.get("/fluxo-caixa")
def fluxo_caixa(meses: int = Query(default=6, ge=1, le=24), db: Session = Depends(get_db)):
    """
    Retorna projeção mês a mês para os próximos N meses.
    Inclui lançamentos com data_vencimento dentro do período (pagos ou pendentes).
    """
    hoje        = date.today()
    mes_atual   = date(hoje.year, hoje.month, 1)

    import calendar as _cal

    resultado = []
    for i in range(meses):
        # primeiro e último dia do mês
        ano  = mes_atual.year + (mes_atual.month - 1 + i) // 12
        mes  = (mes_atual.month - 1 + i) % 12 + 1
        ini  = date(ano, mes, 1)
        fim  = date(ano, mes, _cal.monthrange(ano, mes)[1])

        lancamentos_mes = db.query(Financeiro).filter(
            Financeiro.data_vencimento >= ini,
            Financeiro.data_vencimento <= fim,
            Financeiro.status_pagamento != StatusPagamento.CANCELADO,
        ).all()

        rec_pago  = sum(float(l.valor) for l in lancamentos_mes
                        if l.tipo == TipoLancamento.RECEITA and l.status_pagamento == StatusPagamento.PAGO)
        desp_pago = sum(float(l.valor) for l in lancamentos_mes
                        if l.tipo == TipoLancamento.DESPESA and l.status_pagamento == StatusPagamento.PAGO)
        rec_pend  = sum(float(l.valor) for l in lancamentos_mes
                        if l.tipo == TipoLancamento.RECEITA and l.status_pagamento == StatusPagamento.PENDENTE)
        desp_pend = sum(float(l.valor) for l in lancamentos_mes
                        if l.tipo == TipoLancamento.DESPESA and l.status_pagamento == StatusPagamento.PENDENTE)

        resultado.append({
            "mes"               : f"{ano}-{mes:02d}",
            "receitas_pagas"    : round(rec_pago, 2),
            "despesas_pagas"    : round(desp_pago, 2),
            "receitas_previstas": round(rec_pend, 2),
            "despesas_previstas": round(desp_pend, 2),
            "saldo_real"        : round(rec_pago - desp_pago, 2),
            "saldo_projetado"   : round(rec_pago + rec_pend - desp_pago - desp_pend, 2),
        })

    return resultado
