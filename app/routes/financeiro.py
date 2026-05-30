import calendar
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.financeiro import Financeiro
from app.models.lancamento_mestre import LancamentoMestre
from app.schemas.financeiro import LancamentoCreate, LancamentoUpdate, LancamentoResponse
from app.schemas.lancamento_mestre import (
    LancamentoMestreCreate, LancamentoMestreResponse,
    ParcelasEditarRequest, CancelarSerieRequest,
)
from app.enums import StatusPagamento, TipoLancamento, TipoRecorrencia

router = APIRouter(prefix="/financeiro", tags=["Financeiro"])


def _add_months(d: date, months: int) -> date:
    """Adds months to a date handling end-of-month edge cases."""
    month = d.month - 1 + months
    year  = d.year + month // 12
    month = month % 12 + 1
    day   = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _gerar_datas(dados: LancamentoMestreCreate) -> list[date]:
    if dados.tipo_recorrencia == TipoRecorrencia.UNICO:
        return [dados.data_inicio]

    if dados.tipo_recorrencia == TipoRecorrencia.PARCELADO:
        return [
            _add_months(dados.data_inicio, i * dados.intervalo_meses)
            for i in range(dados.num_parcelas)
        ]

    # RECORRENTE — gera até data_fim ou 12 meses à frente
    limite = dados.data_fim or _add_months(dados.data_inicio, 12)
    datas, d = [], dados.data_inicio
    while d <= limite:
        datas.append(d)
        d = _add_months(d, dados.intervalo_meses)
    return datas


# ── Lançamentos únicos (backward-compatible) ──────────────────────────────────

@router.post("/", response_model=LancamentoResponse, status_code=201)
def criar_lancamento(dados: LancamentoCreate, db: Session = Depends(get_db)):
    lancamento = Financeiro(**dados.model_dump())
    db.add(lancamento)
    db.commit()
    db.refresh(lancamento)
    return lancamento


@router.get("/", response_model=list[LancamentoResponse])
def listar_lancamentos(db: Session = Depends(get_db)):
    return db.query(Financeiro).order_by(Financeiro.data_vencimento).all()


@router.patch("/{lancamento_id}/pagar", response_model=LancamentoResponse)
def pagar_lancamento(lancamento_id: int, db: Session = Depends(get_db)):
    lanc = db.query(Financeiro).filter(Financeiro.id == lancamento_id).first()
    if not lanc:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado")
    if lanc.status_pagamento == StatusPagamento.PAGO:
        raise HTTPException(status_code=409, detail="Lançamento já está pago")
    lanc.status_pagamento = StatusPagamento.PAGO
    lanc.data_pagamento   = date.today()
    db.commit()
    db.refresh(lanc)
    return lanc


@router.patch("/{lancamento_id}/cancelar", response_model=LancamentoResponse)
def cancelar_lancamento(lancamento_id: int, db: Session = Depends(get_db)):
    lanc = db.query(Financeiro).filter(Financeiro.id == lancamento_id).first()
    if not lanc:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado")
    if lanc.status_pagamento == StatusPagamento.PAGO:
        raise HTTPException(status_code=409, detail="Lançamento já pago não pode ser cancelado")
    if lanc.status_pagamento == StatusPagamento.CANCELADO:
        raise HTTPException(status_code=409, detail="Lançamento já está cancelado")
    lanc.status_pagamento = StatusPagamento.CANCELADO
    db.commit()
    db.refresh(lanc)
    return lanc


@router.patch("/{lancamento_id}", response_model=LancamentoResponse)
def editar_lancamento(lancamento_id: int, dados: LancamentoUpdate, db: Session = Depends(get_db)):
    lanc = db.query(Financeiro).filter(Financeiro.id == lancamento_id).first()
    if not lanc:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado")
    if lanc.status_pagamento == StatusPagamento.PAGO:
        raise HTTPException(status_code=409, detail="Lançamento já pago não pode ser editado")
    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(lanc, campo, valor)
    db.commit()
    db.refresh(lanc)
    return lanc


@router.get("/saldo")
def saldo_financeiro(db: Session = Depends(get_db)):
    pagos    = db.query(Financeiro).filter(Financeiro.status_pagamento == StatusPagamento.PAGO).all()
    receitas = sum(float(l.valor) for l in pagos if l.tipo == TipoLancamento.RECEITA)
    despesas = sum(float(l.valor) for l in pagos if l.tipo == TipoLancamento.DESPESA)
    return {"receitas_pagas": receitas, "despesas_pagas": despesas, "saldo": receitas - despesas}


# ── Lançamentos em lote: parcelado / recorrente ───────────────────────────────

@router.post("/lote", response_model=LancamentoMestreResponse, status_code=201)
def criar_lote(dados: LancamentoMestreCreate, db: Session = Depends(get_db)):
    mestre = LancamentoMestre(
        descricao        = dados.descricao,
        tipo             = dados.tipo,
        categoria        = dados.categoria,
        tipo_recorrencia = dados.tipo_recorrencia,
        valor            = dados.valor,
        num_parcelas     = dados.num_parcelas,
        intervalo_meses  = dados.intervalo_meses,
        data_inicio      = dados.data_inicio,
        data_fim         = dados.data_fim,
        forma_pagamento  = dados.forma_pagamento,
        observacoes      = dados.observacoes,
    )
    db.add(mestre)
    db.flush()

    datas = _gerar_datas(dados)
    # parcela_total = None para recorrente sem data_fim (série aberta)
    total = len(datas) if dados.data_fim or dados.tipo_recorrencia == TipoRecorrencia.PARCELADO else None

    for i, dt in enumerate(datas, start=1):
        label = f"{dados.descricao} ({i}/{total})" if total else f"{dados.descricao} — parcela {i}"
        db.add(Financeiro(
            tipo                 = dados.tipo,
            categoria            = dados.categoria,
            descricao            = label,
            valor                = dados.valor,
            data_vencimento      = dt,
            status_pagamento     = StatusPagamento.PENDENTE,
            forma_pagamento      = dados.forma_pagamento,
            lancamento_mestre_id = mestre.id,
            parcela_num          = i,
            parcela_total        = total,
            observacoes          = dados.observacoes,
        ))

    db.commit()
    db.refresh(mestre)
    return mestre


@router.get("/mestres", response_model=list[LancamentoMestreResponse])
def listar_mestres(db: Session = Depends(get_db)):
    return db.query(LancamentoMestre).order_by(LancamentoMestre.criado_em.desc()).all()


@router.get("/mestres/{mestre_id}", response_model=LancamentoMestreResponse)
def buscar_mestre(mestre_id: int, db: Session = Depends(get_db)):
    mestre = db.query(LancamentoMestre).filter(LancamentoMestre.id == mestre_id).first()
    if not mestre:
        raise HTTPException(status_code=404, detail="Série não encontrada")
    return mestre


@router.patch("/mestres/{mestre_id}/parcelas-futuras", response_model=LancamentoMestreResponse)
def editar_parcelas_futuras(
    mestre_id: int,
    dados: ParcelasEditarRequest,
    db: Session = Depends(get_db),
):
    mestre = db.query(LancamentoMestre).filter(LancamentoMestre.id == mestre_id).first()
    if not mestre:
        raise HTTPException(status_code=404, detail="Série não encontrada")

    corte = dados.a_partir_de or date.today()
    for parcela in mestre.parcelas:
        if (parcela.status_pagamento == StatusPagamento.PENDENTE
                and parcela.data_vencimento >= corte):
            if dados.novo_valor is not None:
                parcela.valor = dados.novo_valor
            if dados.nova_descricao is not None:
                parcela.descricao = dados.nova_descricao

    if dados.novo_valor is not None:
        mestre.valor = dados.novo_valor

    db.commit()
    db.refresh(mestre)
    return mestre


@router.post("/mestres/{mestre_id}/cancelar-serie")
def cancelar_serie(
    mestre_id: int,
    dados: CancelarSerieRequest,
    db: Session = Depends(get_db),
):
    mestre = db.query(LancamentoMestre).filter(LancamentoMestre.id == mestre_id).first()
    if not mestre:
        raise HTTPException(status_code=404, detail="Série não encontrada")

    corte = dados.a_partir_de or date.today()
    canceladas = 0
    for parcela in mestre.parcelas:
        if (parcela.status_pagamento == StatusPagamento.PENDENTE
                and parcela.data_vencimento >= corte):
            parcela.status_pagamento = StatusPagamento.CANCELADO
            canceladas += 1

    if not dados.a_partir_de:
        mestre.ativo = False

    db.commit()
    return {"canceladas": canceladas, "serie_encerrada": not dados.a_partir_de}
