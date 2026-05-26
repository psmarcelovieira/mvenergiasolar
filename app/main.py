import bcrypt
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import Base, engine, SessionLocal
from app.models import cliente as _c
from app.models import produto as _p
from app.models import venda as _v
from app.models import item_venda as _i
from app.models import colaborador as _col
from app.models import estoque as _e
from app.models import financeiro as _f
from app.models import prestacao_contas as _pc
from app.models import projeto as _proj
from app.models import ordem_servico as _os
from app.models.usuario import Usuario
from app.enums import PerfilUsuario
from app.routes import (
    cliente, produto, venda, colaborador, estoque, financeiro,
    prestacao_contas, dashboard, projeto, ordem_servico, usuario,
)

Base.metadata.create_all(bind=engine)


def _seed_admin():
    db = SessionLocal()
    try:
        if not db.query(Usuario).first():
            senha_padrao = "solar123"
            db.add(Usuario(
                nome       = "Administrador",
                login      = "admin",
                senha_hash = bcrypt.hashpw(senha_padrao.encode(), bcrypt.gensalt()).decode(),
                perfil     = PerfilUsuario.ADMIN,
            ))
            db.commit()
            print("=" * 50)
            print("  Usuário admin criado com senha: solar123")
            print("  Altere a senha após o primeiro acesso!")
            print("=" * 50)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _seed_admin()
    yield


app = FastAPI(title="Sistema Solar", version="1.0", lifespan=lifespan)

app.include_router(cliente.router)
app.include_router(produto.router)
app.include_router(venda.router)
app.include_router(colaborador.router)
app.include_router(estoque.router)
app.include_router(financeiro.router)
app.include_router(prestacao_contas.router)
app.include_router(dashboard.router)
app.include_router(projeto.router)
app.include_router(ordem_servico.router)
app.include_router(usuario.router)
