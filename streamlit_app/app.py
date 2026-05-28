from typing import cast
import os
import streamlit as st
import requests
import api_client

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

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
from auth import rodape_usuario  # noqa: E402
rodape_usuario()

usuario = st.session_state["usuario"]
st.title("☀️ MV Energia Solar")
st.markdown(f"Bem-vindo de volta, **{usuario['nome']}**! 👋")
st.markdown("---")

try:
    dados = cast(dict, api_client.get_dashboard())
except Exception:
    st.error("API offline. Verifique se o servidor FastAPI está rodando.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Vendas",  dados["total_vendas"])
col2.metric("Receita Aprovada", f"R$ {dados['receita_aprovada']:,.2f}")
col3.metric("Pipeline",         f"R$ {dados['pipeline']:,.2f}")
col4.metric("Saldo Financeiro", f"R$ {dados['saldo_financeiro']:,.2f}")

st.markdown("---")
col5, col6, col7 = st.columns(3)
col5.metric("Ticket Médio",     f"R$ {dados['ticket_medio']:,.2f}")
col7.metric("Valor em Estoque", f"R$ {dados['valor_em_estoque']:,.2f}")

alerta = dados["itens_em_alerta"]
with col6:
    if alerta > 0:
        st.metric("⚠️ Itens em Alerta", alerta)
    else:
        st.metric("✅ Itens em Alerta", alerta)
