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
