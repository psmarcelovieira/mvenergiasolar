import bcrypt
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario, MAX_TENTATIVAS, BLOQUEIO_MINUTOS
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse, LoginRequest

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


def _hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def _verificar(senha: str, hash_: str) -> bool:
    return bcrypt.checkpw(senha.encode(), hash_.encode())


@router.post("/login", response_model=UsuarioResponse)
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.login == dados.login).first()

    if not usuario:
        raise HTTPException(status_code=401, detail="Login ou senha incorretos")

    agora = datetime.now()

    # Conta bloqueada por tentativas excessivas
    if usuario.bloqueado_ate and usuario.bloqueado_ate > agora:
        restante = int((usuario.bloqueado_ate - agora).total_seconds() / 60) + 1
        raise HTTPException(
            status_code=429,
            detail=f"Conta bloqueada. Tente novamente em {restante} minuto(s).",
        )

    # Senha incorreta
    if not _verificar(dados.senha, usuario.senha_hash):
        usuario.tentativas_falhas = (usuario.tentativas_falhas or 0) + 1
        if usuario.tentativas_falhas >= MAX_TENTATIVAS:
            usuario.bloqueado_ate = agora + timedelta(minutes=BLOQUEIO_MINUTOS)
            db.commit()
            raise HTTPException(
                status_code=429,
                detail=f"Conta bloqueada após {MAX_TENTATIVAS} tentativas. "
                       f"Aguarde {BLOQUEIO_MINUTOS} minuto(s).",
            )
        db.commit()
        restantes = MAX_TENTATIVAS - usuario.tentativas_falhas
        raise HTTPException(
            status_code=401,
            detail=f"Login ou senha incorretos. "
                   f"{restantes} tentativa(s) antes do bloqueio.",
        )

    # Sucesso: reseta contadores e registra último acesso
    usuario.tentativas_falhas = 0
    usuario.bloqueado_ate     = None
    usuario.ultimo_login      = agora
    db.commit()
    db.refresh(usuario)
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
