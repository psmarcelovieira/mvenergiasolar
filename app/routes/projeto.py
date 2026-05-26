from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.projeto import HomologacaoProjeto
from app.models.cliente import Cliente
from app.schemas.projeto import ProjetoCreate, ProjetoUpdate, ProjetoResponse

router = APIRouter(prefix="/projetos", tags=["Projetos"])


@router.post("/", response_model=ProjetoResponse, status_code=201)
def criar_projeto(dados: ProjetoCreate, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == dados.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    projeto = HomologacaoProjeto(**dados.model_dump())
    db.add(projeto)
    db.commit()
    db.refresh(projeto)
    return projeto


@router.get("/", response_model=list[ProjetoResponse])
def listar_projetos(db: Session = Depends(get_db)):
    return db.query(HomologacaoProjeto).all()


@router.get("/{projeto_id}", response_model=ProjetoResponse)
def buscar_projeto(projeto_id: int, db: Session = Depends(get_db)):
    projeto = db.query(HomologacaoProjeto).filter(HomologacaoProjeto.id == projeto_id).first()
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return projeto


@router.patch("/{projeto_id}", response_model=ProjetoResponse)
def atualizar_projeto(projeto_id: int, dados: ProjetoUpdate, db: Session = Depends(get_db)):
    projeto = db.query(HomologacaoProjeto).filter(HomologacaoProjeto.id == projeto_id).first()
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(projeto, campo, valor)

    db.commit()
    db.refresh(projeto)
    return projeto


@router.delete("/{projeto_id}", status_code=204)
def excluir_projeto(projeto_id: int, db: Session = Depends(get_db)):
    projeto = db.query(HomologacaoProjeto).filter(HomologacaoProjeto.id == projeto_id).first()
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    db.delete(projeto)
    db.commit()
