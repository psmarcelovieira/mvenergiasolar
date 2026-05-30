import bcrypt
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.venda import Venda
from app.models.item_venda import ItemVenda
from app.models.cliente import Cliente
from app.models.produto import Produto
from app.models.estoque import EstoqueMovimentacao
from app.models.financeiro import Financeiro
from app.models.cancelamento_venda import CancelamentoVenda
from app.models.usuario import Usuario
from app.schemas.venda import VendaCreate, VendaResponse
from app.schemas.cancelamento import CancelamentoRequest, CancelamentoResponse
from app.enums import (
    StatusVenda, TipoMovimento,
    TipoLancamento, CategoriaFinanceiro, StatusPagamento
)
from app.models.prestacao_contas import PrestacaoContas
from app.enums import StatusPrestacao
from app.models.colaborador import Colaborador


router = APIRouter(prefix="/vendas", tags=["Vendas"])


@router.post("/", response_model=VendaResponse, status_code=201)
def criar_venda(dados: VendaCreate, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == dados.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    if not dados.itens:
        raise HTTPException(status_code=422, detail="A venda deve ter pelo menos um item")

    venda = Venda(
        cliente_id       = dados.cliente_id,
        id_responsavel   = dados.id_responsavel,
        data_orcamento   = date.today(),
        status_venda     = StatusVenda.ORCAMENTO,
        valor_instalacao = dados.valor_instalacao,
        desconto         = dados.desconto,
        forma_pagamento  = dados.forma_pagamento,
        parcelas         = dados.parcelas,
        observacoes      = dados.observacoes,
    )
    db.add(venda)
    db.flush()

    for item_data in dados.itens:
        produto = db.query(Produto).filter(Produto.id == item_data.produto_id).first()
        if not produto:
            raise HTTPException(status_code=404,
                detail=f"Produto id={item_data.produto_id} não encontrado")

        preco = item_data.preco_unitario if item_data.preco_unitario else float(produto.preco_venda)

        item = ItemVenda(
            venda_id       = venda.id,
            produto_id     = item_data.produto_id,
            quantidade     = item_data.quantidade,
            preco_unitario = preco,
        )
        db.add(item)

    db.commit()
    db.refresh(venda)
    return venda


@router.get("/", response_model=list[VendaResponse])
def listar_vendas(db: Session = Depends(get_db)):
    return db.query(Venda).all()


@router.get("/{venda_id}", response_model=VendaResponse)
def buscar_venda(venda_id: int, db: Session = Depends(get_db)):
    venda = db.query(Venda).filter(Venda.id == venda_id).first()
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    return venda


@router.patch("/{venda_id}/aprovar", response_model=VendaResponse)
def aprovar_venda(venda_id: int, db: Session = Depends(get_db)):
    venda = db.query(Venda).filter(Venda.id == venda_id).first()
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")

    if venda.status_venda != StatusVenda.ORCAMENTO:
        raise HTTPException(status_code=409,
            detail=f"Venda com status '{venda.status_venda.value}' não pode ser aprovada")

    # 1. Muda status
    venda.status_venda   = StatusVenda.APROVADO
    venda.data_aprovacao = date.today()

    # 2. Valida estoque antes de qualquer baixa
    for item in venda.itens:
        produto = db.query(Produto).filter(Produto.id == item.produto_id).first()
        if produto.qtd_estoque < float(item.quantidade):
            raise HTTPException(
                status_code=422,
                detail=f"Estoque insuficiente para '{produto.nome}'. "
                       f"Disponível: {produto.qtd_estoque}, solicitado: {float(item.quantidade)}"
            )

    # 3. Baixa de estoque
    for item in venda.itens:
        mov = EstoqueMovimentacao(
            tipo_mov       = TipoMovimento.SAIDA,
            id_produto     = item.produto_id,
            quantidade     = item.quantidade,
            valor_unitario = item.preco_unitario,
            id_venda       = venda.id,
            responsavel    = "Sistema",
            observacoes    = f"Baixa automática - Venda #{venda.id}",
        )
        db.add(mov)

    # 3. Lançamentos financeiros pendentes
    db.add(Financeiro(
        tipo             = TipoLancamento.RECEITA,
        categoria        = CategoriaFinanceiro.VENDA_EQUIPAMENTOS,
        descricao        = f"Equipamentos - Venda #{venda.id}",
        valor            = venda.valor_equipamentos,
        data_vencimento  = date.today(),
        status_pagamento = StatusPagamento.PENDENTE,
        forma_pagamento  = venda.forma_pagamento,
        id_venda         = venda.id,
    ))

    if float(venda.valor_instalacao or 0) > 0:
        db.add(Financeiro(
            tipo             = TipoLancamento.RECEITA,
            categoria        = CategoriaFinanceiro.SERVICO_INSTALACAO,
            descricao        = f"Instalação - Venda #{venda.id}",
            valor            = venda.valor_instalacao,
            data_vencimento  = date.today(),
            status_pagamento = StatusPagamento.PENDENTE,
            forma_pagamento  = venda.forma_pagamento,
            id_venda         = venda.id,
        ))

     # 4. Prestação de contas (se tiver responsável)
    if venda.id_responsavel:
        colaborador = db.query(Colaborador).filter(
            Colaborador.id_colaborador == venda.id_responsavel
        ).first()

        ultima = db.query(PrestacaoContas).with_for_update().order_by(
            PrestacaoContas.id_prestacao.desc()
        ).first()
        numero = int(ultima.id_prestacao[2:]) + 1 if ultima else 1
        novo_id = f"PC{numero:04d}"

        db.add(PrestacaoContas(
            id_prestacao        = novo_id,
            data                = date.today(),
            id_venda            = venda.id,
            id_colaborador      = venda.id_responsavel,
            valor_recebido      = venda.valor_equipamentos,
            custo_instalacao    = venda.valor_instalacao or 0,
            percentual_comissao = colaborador.percentual_comissao,
            status_pagto        = StatusPrestacao.PENDENTE,
        ))

    db.commit()
    db.refresh(venda)
    return venda


@router.delete("/{venda_id}", status_code=204)
def excluir_venda(venda_id: int, db: Session = Depends(get_db)):
    venda = db.query(Venda).filter(Venda.id == venda_id).first()
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")

    if venda.status_venda is not StatusVenda.ORCAMENTO:
        raise HTTPException(status_code=409,
            detail="Apenas vendas em Orçamento podem ser excluídas")

    for item in venda.itens:
        db.delete(item)
    db.delete(venda)
    db.commit()


@router.post("/{venda_id}/cancelar", response_model=CancelamentoResponse)
def cancelar_venda(venda_id: int, dados: CancelamentoRequest, db: Session = Depends(get_db)):
    # ── 1. Localiza a venda ────────────────────────────────────────────────────
    venda = db.query(Venda).filter(Venda.id == venda_id).first()
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")

    if venda.status_venda == StatusVenda.CANCELADO:
        raise HTTPException(status_code=409, detail="Venda já está cancelada")

    # ── 2. Valida credenciais do autorizador (deve ser Admin) ─────────────────
    autorizador = db.query(Usuario).filter(Usuario.login == dados.autorizador_login).first()
    if not autorizador:
        raise HTTPException(status_code=401, detail="Credenciais de autorização inválidas")

    if not bcrypt.checkpw(dados.autorizador_senha.encode(), autorizador.senha_hash.encode()):
        raise HTTPException(status_code=401, detail="Credenciais de autorização inválidas")

    if autorizador.perfil.value != "Admin":
        raise HTTPException(status_code=403,
            detail="Apenas administradores podem autorizar cancelamentos")

    # ── 3. Localiza o solicitante ──────────────────────────────────────────────
    solicitante = db.query(Usuario).filter(Usuario.login == dados.solicitante_login).first()
    if not solicitante:
        raise HTTPException(status_code=404, detail="Usuário solicitante não encontrado")

    # ── 4. Reverte estoque (apenas se venda estava aprovada / em andamento) ───
    estoque_revertido = False
    status_com_estoque = {StatusVenda.APROVADO, StatusVenda.EM_ANDAMENTO, StatusVenda.CONCLUIDO}

    if venda.status_venda in status_com_estoque:
        for item in venda.itens:
            db.add(EstoqueMovimentacao(
                tipo_mov       = TipoMovimento.ENTRADA,
                id_produto     = item.produto_id,
                quantidade     = item.quantidade,
                valor_unitario = item.preco_unitario,
                id_venda       = venda.id,
                responsavel    = autorizador.nome,
                observacoes    = f"Estorno - Cancelamento da Venda #{venda.id}",
            ))
        estoque_revertido = True

    # ── 5. Estorna todos os lançamentos financeiros da venda ─────────────────
    # Inclui PAGO e ATRASADO — a Despesa/Comissão criada ao pagar a prestação
    # também fica vinculada ao id_venda e precisa ser revertida aqui.
    financeiro_tratado = False
    lancamentos = db.query(Financeiro).filter(
        Financeiro.id_venda == venda.id,
        Financeiro.status_pagamento != StatusPagamento.CANCELADO,
    ).all()

    for lanc in lancamentos:
        lanc.status_pagamento = StatusPagamento.CANCELADO
        financeiro_tratado = True

    # ── 6. Cancela prestação de contas (PENDENTE ou PAGA) ────────────────────
    prestacao = db.query(PrestacaoContas).filter(
        PrestacaoContas.id_venda == venda.id,
        PrestacaoContas.status_pagto != StatusPrestacao.CANCELADA,
    ).first()
    if prestacao:
        prestacao.status_pagto = StatusPrestacao.CANCELADA

    # ── 7. Muda status da venda para CANCELADO ────────────────────────────────
    venda.status_venda = StatusVenda.CANCELADO

    # ── 8. Grava trilha de auditoria imutável ─────────────────────────────────
    registro = CancelamentoVenda(
        venda_id           = venda.id,
        solicitante_id     = solicitante.id,
        autorizador_id     = autorizador.id,
        motivo             = dados.motivo,
        data_cancelamento  = datetime.now(),
        estoque_revertido  = estoque_revertido,
        financeiro_tratado = financeiro_tratado,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)

    return CancelamentoResponse.model_validate(registro, from_attributes=True)


@router.get("/{venda_id}/cancelamento", response_model=CancelamentoResponse)
def buscar_cancelamento(venda_id: int, db: Session = Depends(get_db)):
    registro = db.query(CancelamentoVenda).filter(
        CancelamentoVenda.venda_id == venda_id
    ).first()
    if not registro:
        raise HTTPException(status_code=404, detail="Cancelamento não encontrado para esta venda")

    return CancelamentoResponse.model_validate(registro, from_attributes=True)
