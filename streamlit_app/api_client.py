import os
import requests
import streamlit as st

# Em produção: defina API_URL nos Secrets do Streamlit Cloud
def _base_url() -> str:
    try:
        url = st.secrets["API_URL"]
        if url:
            return url.rstrip("/")
    except Exception:
        pass
    return os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")

BASE_URL = _base_url()


def _get(url) -> list | dict:
    """GET com tratamento de erro centralizado. Retorna [] ou {} e exibe aviso."""
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ API offline. Certifique-se de que o uvicorn está rodando e recarregue a página.")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao comunicar com a API: {e}")
        st.stop()


def get_dashboard():
    return _get(f"{BASE_URL}/dashboard/")

def listar_clientes():
    return _get(f"{BASE_URL}/clientes/")

def criar_cliente(dados: dict):
    return requests.post(f"{BASE_URL}/clientes/", json=dados)

def atualizar_cliente(cliente_id: int, dados: dict):
    return requests.patch(f"{BASE_URL}/clientes/{cliente_id}", json=dados)

def excluir_cliente(cliente_id: int):
    return requests.delete(f"{BASE_URL}/clientes/{cliente_id}")

def listar_produtos():
    return _get(f"{BASE_URL}/produtos/")

def criar_produto(dados: dict):
    return requests.post(f"{BASE_URL}/produtos/", json=dados)

def atualizar_produto(produto_id: int, dados: dict):
    return requests.patch(f"{BASE_URL}/produtos/{produto_id}", json=dados)

def excluir_produto(produto_id: int):
    return requests.delete(f"{BASE_URL}/produtos/{produto_id}")

def listar_colaboradores():
    return _get(f"{BASE_URL}/colaboradores/")

def criar_colaborador(dados: dict):
    return requests.post(f"{BASE_URL}/colaboradores/", json=dados)

def atualizar_colaborador(colaborador_id: str, dados: dict):
    return requests.patch(f"{BASE_URL}/colaboradores/{colaborador_id}", json=dados)

def excluir_colaborador(colaborador_id: str):
    return requests.delete(f"{BASE_URL}/colaboradores/{colaborador_id}")

def listar_vendas():
    return _get(f"{BASE_URL}/vendas/")

def criar_venda(dados: dict):
    return requests.post(f"{BASE_URL}/vendas/", json=dados)

def aprovar_venda(venda_id: int):
    return requests.patch(f"{BASE_URL}/vendas/{venda_id}/aprovar")

def cancelar_venda(venda_id: int, solicitante_login: str,
                   autorizador_login: str, autorizador_senha: str, motivo: str):
    return requests.post(f"{BASE_URL}/vendas/{venda_id}/cancelar", json={
        "solicitante_login": solicitante_login,
        "autorizador_login": autorizador_login,
        "autorizador_senha": autorizador_senha,
        "motivo":            motivo,
    })

def buscar_cancelamento(venda_id: int):
    return requests.get(f"{BASE_URL}/vendas/{venda_id}/cancelamento")

def excluir_venda(venda_id: int):
    return requests.delete(f"{BASE_URL}/vendas/{venda_id}")

def listar_lancamentos():
    return _get(f"{BASE_URL}/financeiro/")

def pagar_lancamento(lancamento_id: int):
    return requests.patch(f"{BASE_URL}/financeiro/{lancamento_id}/pagar")

def cancelar_lancamento(lancamento_id: int):
    return requests.patch(f"{BASE_URL}/financeiro/{lancamento_id}/cancelar")

def editar_lancamento(lancamento_id: int, dados: dict):
    return requests.patch(f"{BASE_URL}/financeiro/{lancamento_id}", json=dados)

def criar_lancamento_lote(dados: dict):
    return requests.post(f"{BASE_URL}/financeiro/lote", json=dados)

def listar_mestres():
    return _get(f"{BASE_URL}/financeiro/mestres")

def buscar_mestre(mestre_id: int):
    return _get(f"{BASE_URL}/financeiro/mestres/{mestre_id}")

def editar_parcelas_futuras(mestre_id: int, dados: dict):
    return requests.patch(f"{BASE_URL}/financeiro/mestres/{mestre_id}/parcelas-futuras", json=dados)

def cancelar_serie(mestre_id: int, a_partir_de: str | None = None):
    body = {"a_partir_de": a_partir_de} if a_partir_de else {}
    return requests.post(f"{BASE_URL}/financeiro/mestres/{mestre_id}/cancelar-serie", json=body)

def get_fluxo_caixa(meses: int = 6):
    return _get(f"{BASE_URL}/dashboard/fluxo-caixa?meses={meses}")

def saldo_produto(produto_id: int):
    return _get(f"{BASE_URL}/estoque/produtos/{produto_id}/saldo")

def registrar_movimentacao(dados: dict):
    return requests.post(f"{BASE_URL}/estoque/movimentacoes", json=dados)

def listar_projetos():
    return _get(f"{BASE_URL}/projetos/")

def criar_projeto(dados: dict):
    return requests.post(f"{BASE_URL}/projetos/", json=dados)

def atualizar_projeto(projeto_id: int, dados: dict):
    return requests.patch(f"{BASE_URL}/projetos/{projeto_id}", json=dados)

def excluir_projeto(projeto_id: int):
    return requests.delete(f"{BASE_URL}/projetos/{projeto_id}")

def listar_ordens_servico():
    return _get(f"{BASE_URL}/ordens-servico/")

def criar_os(dados: dict):
    return requests.post(f"{BASE_URL}/ordens-servico/", json=dados)

def atualizar_os(os_id: int, dados: dict):
    return requests.patch(f"{BASE_URL}/ordens-servico/{os_id}", json=dados)

def excluir_os(os_id: int):
    return requests.delete(f"{BASE_URL}/ordens-servico/{os_id}")

def listar_prestacoes():
    return _get(f"{BASE_URL}/prestacoes/")

def pagar_prestacao(prestacao_id: str):
    return requests.patch(f"{BASE_URL}/prestacoes/{prestacao_id}/pagar")

def listar_usuarios():
    return _get(f"{BASE_URL}/usuarios/")

def criar_usuario(dados: dict):
    return requests.post(f"{BASE_URL}/usuarios/", json=dados)

def atualizar_usuario(usuario_id: int, dados: dict):
    return requests.patch(f"{BASE_URL}/usuarios/{usuario_id}", json=dados)

def excluir_usuario(usuario_id: int):
    return requests.delete(f"{BASE_URL}/usuarios/{usuario_id}")
