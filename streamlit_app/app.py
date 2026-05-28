import os
import streamlit as st
import requests

st.set_page_config(page_title="MV Energia Solar", page_icon="☀️", layout="wide")


def _api_url() -> str:
    try:
        url = st.secrets["API_URL"]
        if url:
            return url.rstrip("/")
    except Exception:
        pass
    return os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")


# ── TELA DE LOGIN ──────────────────────────────────────────────────────────────
if "usuario" not in st.session_state:
    _, col_form, _ = st.columns([1, 1, 1])
    with col_form:
        st.markdown(
            "<h2 style='text-align:center;margin-bottom:0'>☀️ MV Energia Solar</h2>"
            "<p style='text-align:center;color:gray;margin-top:4px'>Sistema de Gestão</p>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        with st.form("form_login"):
            login = st.text_input("Login", placeholder="seu.login")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)

        if entrar:
            if not login or not senha:
                st.error("Preencha login e senha.")
            else:
                BASE_URL = _api_url()
                try:
                    resp = requests.post(
                        f"{BASE_URL}/usuarios/login",
                        json={"login": login, "senha": senha},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        st.session_state["usuario"] = resp.json()
                        st.rerun()
                    else:
                        detalhe = resp.json().get("detail", "Erro desconhecido")
                        if resp.status_code == 429:
                            st.warning(f"🔒 {detalhe}")
                        else:
                            st.error(f"❌ {detalhe}")
                except requests.exceptions.ConnectionError:
                    st.error("⚠️ API offline. Tente novamente em instantes.")
                except requests.exceptions.Timeout:
                    st.error("⚠️ API demorou demais. Tente novamente.")
    st.stop()

# ── SIDEBAR: usuário logado ────────────────────────────────────────────────────
from auth import rodape_usuario  # noqa: E402
rodape_usuario()

# ── NAVEGAÇÃO POR GRUPOS ───────────────────────────────────────────────────────
usuario = st.session_state["usuario"]
is_admin = usuario["perfil"] == "Admin"

_pages: dict = {
    "Início": [
        st.Page("pages/dashboard.py",        title="Dashboard",        icon="🏠"),
    ],
    "Comercial": [
        st.Page("pages/01_Clientes.py",       title="Clientes",         icon="👥"),
        st.Page("pages/02_Vendas.py",         title="Vendas",           icon="🛒"),
        st.Page("pages/10_Ficha_Cliente.py",  title="Ficha do Cliente", icon="📋"),
        st.Page("pages/11_Prospeccao.py",     title="Prospecção",       icon="🎯"),
    ],
    "Operações": [
        st.Page("pages/07_Projetos.py",       title="Projetos",         icon="⚡"),
        st.Page("pages/08_Manutencao.py",     title="Manutenção",       icon="🔧"),
        st.Page("pages/03_Estoque.py",        title="Estoque",          icon="📦"),
    ],
    "Relatórios": [
        st.Page("pages/12_Relatorios.py",     title="Relatórios PDF",   icon="📄"),
        st.Page("pages/14_Previsao.py",       title="Previsão de Vendas", icon="📈"),
    ],
}

if is_admin:
    _pages["Financeiro"] = [
        st.Page("pages/04_Financeiro.py",     title="Lançamentos",      icon="💰"),
        st.Page("pages/05_Prestacoes.py",     title="Prestações",       icon="🤝"),
    ]
    _pages["Administração"] = [
        st.Page("pages/06_Colaboradores.py",  title="Colaboradores",    icon="👤"),
        st.Page("pages/09_Usuarios.py",       title="Usuários",         icon="🔑"),
        st.Page("pages/13_Importacao.py",     title="Importação",       icon="📂"),
    ]

pg = st.navigation(_pages)
pg.run()
