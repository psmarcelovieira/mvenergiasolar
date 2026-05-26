from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.prestacao_contas import PrestacaoContas
from app.models.financeiro import Financeiro
from app.schemas.prestacao_contas import PrestacaoResponse
from app.enums import StatusPrestacao, TipoLancamento, CategoriaFinanceiro, StatusPagamento, FormaPagamento

router = APIRouter(prefix="/prestacoes", tags=["Prestação de Contas"])


def gerar_id_prestacao(db: Session) -> str:
    ultima = db.query(PrestacaoContas).order_by(PrestacaoContas.id_prestacao.desc()).first()
    numero = int(ultima.id_prestacao[2:]) + 1 if ultima else 1
    return f"PC{numero:04d}"


@router.get("/", response_model=list[PrestacaoResponse])
def listar_prestacoes(db: Session = Depends(get_db)):
    return db.query(PrestacaoContas).all()


@router.get("/{prestacao_id}", response_model=PrestacaoResponse)
def buscar_prestacao(prestacao_id: str, db: Session = Depends(get_db)):
    prestacao = db.query(PrestacaoContas).filter(
        PrestacaoContas.id_prestacao == prestacao_id
    ).first()
    if not prestacao:
        raise HTTPException(status_code=404, detail="Prestação não encontrada")
    return prestacao


@router.patch("/{prestacao_id}/pagar", response_model=PrestacaoResponse)
def pagar_prestacao(prestacao_id: str, db: Session = Depends(get_db)):
    prestacao = db.query(PrestacaoContas).filter(
        PrestacaoContas.id_prestacao == prestacao_id
    ).first()
    if not prestacao:
        raise HTTPException(status_code=404, detail="Prestação não encontrada")

    if prestacao.status_pagto == StatusPrestacao.PAGA:
        raise HTTPException(status_code=409, detail="Comissão já foi paga")

    prestacao.status_pagto = StatusPrestacao.PAGA
    prestacao.data_pagto   = date.today()

    db.add(Financeiro(
        tipo             = TipoLancamento.DESPESA,
        categoria        = CategoriaFinanceiro.COMISSAO,
        descricao        = f"Comissão {prestacao.id_colaborador} - Venda #{prestacao.id_venda}",
        valor            = prestacao.valor_comissao,
        data_vencimento  = date.today(),
        data_pagamento   = date.today(),
        status_pagamento = StatusPagamento.PAGO,
        forma_pagamento  = FormaPagamento.PIX,
        id_venda         = prestacao.id_venda,
    ))

    db.commit()
    db.refresh(prestacao)
    return prestacao
