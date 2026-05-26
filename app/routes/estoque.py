from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.estoque import EstoqueMovimentacao
from app.models.produto import Produto
from app.schemas.estoque import MovimentacaoCreate, MovimentacaoResponse

router = APIRouter(prefix="/estoque", tags=["Estoque"])


@router.post("/movimentacoes", response_model=MovimentacaoResponse, status_code=201)
def registrar_movimentacao(dados: MovimentacaoCreate, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == dados.id_produto).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    mov = EstoqueMovimentacao(**dados.model_dump())
    db.add(mov)
    db.commit()
    db.refresh(mov)
    return mov


@router.get("/movimentacoes", response_model=list[MovimentacaoResponse])
def listar_movimentacoes(db: Session = Depends(get_db)):
    return db.query(EstoqueMovimentacao).all()


@router.get("/produtos/{produto_id}/saldo")
def saldo_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return {
        "produto_id"    : produto.id,
        "nome"          : produto.nome,
        "qtd_estoque"   : produto.qtd_estoque,
        "qtd_minima"    : produto.qtd_minima,
        "alerta_estoque": produto.alerta_estoque,
    }
