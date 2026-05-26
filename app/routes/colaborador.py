from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.colaborador import Colaborador
from app.schemas.colaborador import ColaboradorCreate, ColaboradorUpdate, ColaboradorResponse
from app.models.venda import Venda
from app.enums import StatusColaborador

router = APIRouter(prefix="/colaboradores", tags=["Colaboradores"])


def gerar_id_colaborador(db: Session) -> str:
    ultimo = (
        db.query(Colaborador)
        .order_by(Colaborador.id_colaborador.desc())
        .first()
    )
    numero = int(ultimo.id_colaborador[3:]) + 1 if ultimo else 1
    return f"COL{numero:03d}"


@router.post("/", response_model=ColaboradorResponse, status_code=201)
def criar_colaborador(dados: ColaboradorCreate, db: Session = Depends(get_db)):
    if dados.cpf:
        existente = db.query(Colaborador).filter(Colaborador.cpf == dados.cpf).first()
        if existente:
            raise HTTPException(status_code=409, detail="CPF já cadastrado")

    colaborador = Colaborador(
        **dados.model_dump(),
        id_colaborador=gerar_id_colaborador(db),
        status=StatusColaborador.ATIVO,
    )
    db.add(colaborador)
    db.commit()
    db.refresh(colaborador)
    return colaborador


@router.get("/", response_model=list[ColaboradorResponse])
def listar_colaboradores(db: Session = Depends(get_db)):
    return db.query(Colaborador).all()


@router.get("/{colaborador_id}", response_model=ColaboradorResponse)
def buscar_colaborador(colaborador_id: str, db: Session = Depends(get_db)):
    colaborador = db.query(Colaborador).filter(
        Colaborador.id_colaborador == colaborador_id
    ).first()
    if not colaborador:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado")
    return colaborador


@router.patch("/{colaborador_id}", response_model=ColaboradorResponse)
def atualizar_colaborador(colaborador_id: str, dados: ColaboradorUpdate, db: Session = Depends(get_db)):
    colaborador = db.query(Colaborador).filter(
        Colaborador.id_colaborador == colaborador_id
    ).first()
    if not colaborador:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado")

    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(colaborador, campo, valor)

    db.commit()
    db.refresh(colaborador)
    return colaborador


@router.delete("/{colaborador_id}", status_code=204)
def excluir_colaborador(colaborador_id: str, db: Session = Depends(get_db)):
    colaborador = db.query(Colaborador).filter(
        Colaborador.id_colaborador == colaborador_id
    ).first()
    if not colaborador:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado")

    tem_venda = db.query(Venda).filter(Venda.id_responsavel == colaborador_id).first()
    if tem_venda:
        raise HTTPException(status_code=409,
            detail="Colaborador possui vendas associadas. Inative-o em vez de excluir.")

    db.delete(colaborador)
    db.commit()
