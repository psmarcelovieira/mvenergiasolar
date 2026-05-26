import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse, LoginRequest

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


def _hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def _verificar(senha: str, hash_: str) -> bool:
    return bcrypt.checkpw(senha.encode(), hash_.encode())


@router.post("/login", response_model=UsuarioResponse)
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.login == dados.login).first()
    if not usuario or not _verificar(dados.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Login ou senha incorretos")
    return usuario


@router.get("/", response_model=list[UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).all()


@router.post("/", response_model=UsuarioResponse, status_code=201)
def criar_usuario(dados: UsuarioCreate, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.login == dados.login).first():
        raise HTTPException(status_code=409, detail="Login já cadastrado")
    usuario = Usuario(
        nome       = dados.nome,
        login      = dados.login,
        senha_hash = _hash(dados.senha),
        perfil     = dados.perfil,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.patch("/{usuario_id}", response_model=UsuarioResponse)
def atualizar_usuario(usuario_id: int, dados: UsuarioUpdate, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    atualizacoes = dados.model_dump(exclude_none=True)
    if "senha" in atualizacoes:
        atualizacoes["senha_hash"] = _hash(atualizacoes.pop("senha"))

    for campo, valor in atualizacoes.items():
        setattr(usuario, campo, valor)

    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete("/{usuario_id}", status_code=204)
def excluir_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    total = db.query(Usuario).count()
    if total == 1:
        raise HTTPException(status_code=409, detail="Não é possível excluir o único usuário")
    db.delete(usuario)
    db.commit()
