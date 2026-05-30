from typing import cast
import streamlit as st
import api_client

usuario = st.session_state["usuario"]
st.title("☀️ MV Energia Solar")
st.markdown(f"Bem-vindo de volta, **{usuario['nome']}**! 👋")
st.markdown("---")

try:
    dados = cast(dict, api_client.get_dashboard())
except Exception:
    st.error("API offline. Verifique se o servidor FastAPI está rodando.")
    st.stop()

# ── KPIs de Vendas ─────────────────────────────────────────────────────────────
st.subheader("Vendas")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Vendas",  dados["total_vendas"])
col2.metric("Receita Aprovada", f"R$ {dados['receita_aprovada']:,.2f}")
col3.metric("Pipeline",         f"R$ {dados['pipeline']:,.2f}")
col4.metric("Ticket Médio",     f"R$ {dados['ticket_medio']:,.2f}")

st.markdown("---")

# ── KPIs Financeiros ───────────────────────────────────────────────────────────
st.subheader("Financeiro")
col5, col6, col7, col8 = st.columns(4)
col5.metric("Saldo em Caixa",   f"R$ {dados['saldo_financeiro']:,.2f}")
col6.metric("A Receber",        f"R$ {dados['contas_a_receber']:,.2f}")
col7.metric("A Pagar",          f"R$ {dados['contas_a_pagar']:,.2f}")
saldo_proj = dados['saldo_financeiro'] + dados['contas_a_receber'] - dados['contas_a_pagar']
col8.metric("Saldo Projetado",  f"R$ {saldo_proj:,.2f}",
            delta=f"R$ {saldo_proj - dados['saldo_financeiro']:,.2f}")

st.markdown("---")

# ── KPIs de Estoque ────────────────────────────────────────────────────────────
st.subheader("Estoque")
col9, col10 = st.columns([1, 3])
col9.metric("Valor em Estoque", f"R$ {dados['valor_em_estoque']:,.2f}")
alerta = dados["itens_em_alerta"]
with col10:
    if alerta > 0:
        st.metric("⚠️ Itens em Alerta de Estoque", alerta)
    else:
        st.metric("✅ Itens em Alerta de Estoque", alerta)
