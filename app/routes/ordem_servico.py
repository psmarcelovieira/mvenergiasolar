from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.ordem_servico import OrdemServico
from app.models.cliente import Cliente
from app.models.financeiro import Financeiro
from app.schemas.ordem_servico import OSCreate, OSUpdate, OSResponse
from app.enums import (
    StatusOS, TipoServico,
    TipoLancamento, CategoriaFinanceiro, StatusPagamento
)

router = APIRouter(prefix="/ordens-servico", tags=["Ordens de Serviço"])


def gerar_id_os(db: Session) -> str:
    ultima = db.query(OrdemServico).order_by(OrdemServico.id_os.desc()).first()
    numero = int(ultima.id_os[2:]) + 1 if ultima else 1
    return f"OS{numero:04d}"


@router.post("/", response_model=OSResponse, status_code=201)
def criar_os(dados: OSCreate, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == dados.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    os_ = OrdemServico(**dados.model_dump(), id_os=gerar_id_os(db))
    db.add(os_)
    db.commit()
    db.refresh(os_)
    return os_


@router.get("/", response_model=list[OSResponse])
def listar_os(db: Session = Depends(get_db)):
    return db.query(OrdemServico).all()


@router.get("/{os_id}", response_model=OSResponse)
def buscar_os(os_id: str, db: Session = Depends(get_db)):
    os_ = db.query(OrdemServico).filter(OrdemServico.id_os == os_id).first()
    if not os_:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    return os_


@router.patch("/{os_id}", response_model=OSResponse)
def atualizar_os(os_id: str, dados: OSUpdate, db: Session = Depends(get_db)):
    os_ = db.query(OrdemServico).filter(OrdemServico.id_os == os_id).first()
    if not os_:
        raise HTTPException(status_code=404, detail="OS não encontrada")

    status_anterior = os_.status_os
    atualizacoes    = dados.model_dump(exclude_none=True)

    # Preenche data_conclusao automaticamente ao concluir
    novo_status = atualizacoes.get("status_os")
    if novo_status == StatusOS.CONCLUIDA and not atualizacoes.get("data_conclusao"):
        atualizacoes["data_conclusao"] = date.today()

    for campo, valor in atualizacoes.items():
        setattr(os_, campo, valor)

    # Gera lançamento financeiro ao concluir (apenas uma vez, e só se tiver custo)
    concluindo_agora = (
        novo_status == StatusOS.CONCLUIDA
        and status_anterior is not StatusOS.CONCLUIDA
        and os_.tipo_servico is not TipoServico.GARANTIA
        and float(os_.custo_total or 0) > 0
    )
    if concluindo_agora:
        db.add(Financeiro(
            tipo             = TipoLancamento.RECEITA,
            categoria        = CategoriaFinanceiro.MANUTENCAO,
            descricao        = f"OS {os_.id_os} — {os_.tipo_servico.value}",
            valor            = os_.custo_total,
            data_vencimento  = date.today(),
            status_pagamento = StatusPagamento.PENDENTE,
            forma_pagamento  = os_.forma_pagamento,
        ))

    db.commit()
    db.refresh(os_)
    return os_


@router.delete("/{os_id}", status_code=204)
def excluir_os(os_id: str, db: Session = Depends(get_db)):
    os_ = db.query(OrdemServico).filter(OrdemServico.id_os == os_id).first()
    if not os_:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    db.delete(os_)
    db.commit()
