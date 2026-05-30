import logging
import bcrypt
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.database import Base, engine, SessionLocal, DATABASE_URL
from app.models import cliente as _c
from app.models import produto as _p
from app.models import venda as _v
from app.models import item_venda as _i
from app.models import colaborador as _col
from app.models import estoque as _e
from app.models import financeiro as _f
from app.models import lancamento_mestre as _lm
from app.models import prestacao_contas as _pc
from app.models import projeto as _proj
from app.models import ordem_servico as _os
from app.models import cancelamento_venda as _cv
from app.models.usuario import Usuario
from app.enums import PerfilUsuario
from app.routes import (
    cliente, produto, venda, colaborador, estoque, financeiro,
    prestacao_contas, dashboard, projeto, ordem_servico, usuario,
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("solar")

# ── Banco ─────────────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

db_type = "PostgreSQL" if DATABASE_URL.startswith("postgresql") else "SQLite (FALLBACK!)"
logger.info("=" * 50)
logger.info(f"  DATABASE: {db_type}")
logger.info(f"  URL prefix: {DATABASE_URL[:40]}...")
logger.info("=" * 50)


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
            logger.info("Usuário admin criado com senha padrão 'solar123'")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _seed_admin()
    yield


app = FastAPI(title="Sistema Solar", version="1.0", lifespan=lifespan)


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def handle_unhandled_exception(request: Request, exc: Exception):
    logger.error(
        "Erro não tratado em %s %s: %s",
        request.method, request.url.path, exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor. Tente novamente."},
    )


# ── Rotas ─────────────────────────────────────────────────────────────────────
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
