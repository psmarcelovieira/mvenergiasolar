from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.financeiro import Financeiro
from app.schemas.financeiro import LancamentoCreate, LancamentoResponse
from app.enums import StatusPagamento, TipoLancamento

router = APIRouter(prefix="/financeiro", tags=["Financeiro"])


@router.post("/", response_model=LancamentoResponse, status_code=201)
def criar_lancamento(dados: LancamentoCreate, db: Session = Depends(get_db)):
    lancamento = Financeiro(**dados.model_dump())
    db.add(lancamento)
    db.commit()
    db.refresh(lancamento)
    return lancamento


@router.get("/", response_model=list[LancamentoResponse])
def listar_lancamentos(db: Session = Depends(get_db)):
    return db.query(Financeiro).all()


@router.patch("/{lancamento_id}/pagar", response_model=LancamentoResponse)
def pagar_lancamento(lancamento_id: int, db: Session = Depends(get_db)):
    lancamento = db.query(Financeiro).filter(Financeiro.id == lancamento_id).first()
    if not lancamento:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado")

    if lancamento.status_pagamento == StatusPagamento.PAGO:
        raise HTTPException(status_code=409, detail="Lançamento já está pago")

    lancamento.status_pagamento = StatusPagamento.PAGO
    lancamento.data_pagamento   = date.today()
    db.commit()
    db.refresh(lancamento)
    return lancamento


@router.get("/saldo")
def saldo_financeiro(db: Session = Depends(get_db)):
    lancamentos = db.query(Financeiro).filter(
        Financeiro.status_pagamento == StatusPagamento.PAGO
    ).all()

    receitas  = sum(float(l.valor) for l in lancamentos if l.tipo == TipoLancamento.RECEITA)
    despesas  = sum(float(l.valor) for l in lancamentos if l.tipo == TipoLancamento.DESPESA)

    return {
        "receitas_pagas" : receitas,
        "despesas_pagas" : despesas,
        "saldo"          : receitas - despesas,
    }
