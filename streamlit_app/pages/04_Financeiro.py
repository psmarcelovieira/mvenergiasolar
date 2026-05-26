import streamlit as st
import pandas as pd
import api_client

st.set_page_config(page_title="Financeiro", layout="wide")
from auth import verificar_admin, rodape_usuario
verificar_admin()
rodape_usuario()
st.title("💰 Financeiro")

TIPO_ICONE = {"Receita": "🟢", "Despesa": "🔴"}
STATUS_COR  = {"Pendente": "🟡", "Pago": "✅"}

tab_lista, tab_saldo = st.tabs(["📋 Lançamentos", "📊 Saldo"])

# ── LANÇAMENTOS ────────────────────────────────────────────────────────────────
with tab_lista:

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_tipo   = st.selectbox("Filtrar por Tipo", ["Todos", "Receita", "Despesa"])
    with col_f2:
        filtro_status = st.selectbox("Filtrar por Status", ["Todos", "Pendente", "Pago"])

    lancamentos = api_client.listar_lancamentos()

    if filtro_tipo != "Todos":
        lancamentos = [l for l in lancamentos if l["tipo"] == filtro_tipo]
    if filtro_status != "Todos":
        lancamentos = [l for l in lancamentos if l["status_pagamento"] == filtro_status]

    if not lancamentos:
        st.info("Nenhum lançamento encontrado.")
    else:
        cab = st.columns([1, 2, 3, 2, 2, 2, 2])
        for col, titulo in zip(cab, ["#", "Tipo", "Descrição", "Valor", "Vencimento", "Status", "Ação"]):
            col.markdown(f"**{titulo}**")
        st.divider()

        for l in lancamentos:
            tipo   = l["tipo"]
            status = l["status_pagamento"]
            c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 2, 3, 2, 2, 2, 2])
            c1.write(f"#{l['id']}")
            c2.write(f"{TIPO_ICONE.get(tipo, '')} {tipo}")
            c3.write(l["descricao"])
            c4.write(f"R$ {l['valor']:,.2f}")
            c5.write(l["data_vencimento"])
            c6.write(f"{STATUS_COR.get(status, '')} {status}")

            if status == "Pendente":
                if c7.button("✅ Pagar", key=f"pagar_{l['id']}"):
                    resp = api_client.pagar_lancamento(l["id"])
                    if resp.status_code == 200:
                        st.success(f"Lançamento #{l['id']} marcado como pago!")
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail", "Erro ao pagar"))
            else:
                c7.write(l.get("data_pagamento") or "—")

# ── SALDO ──────────────────────────────────────────────────────────────────────
with tab_saldo:
    todos = api_client.listar_lancamentos()

    receitas_pagas   = sum(l["valor"] for l in todos if l["tipo"] == "Receita" and l["status_pagamento"] == "Pago")
    despesas_pagas   = sum(l["valor"] for l in todos if l["tipo"] == "Despesa" and l["status_pagamento"] == "Pago")
    receitas_pend    = sum(l["valor"] for l in todos if l["tipo"] == "Receita" and l["status_pagamento"] == "Pendente")
    despesas_pend    = sum(l["valor"] for l in todos if l["tipo"] == "Despesa" and l["status_pagamento"] == "Pendente")
    saldo            = receitas_pagas - despesas_pagas

    col1, col2, col3 = st.columns(3)
    col1.metric("Receitas Pagas",   f"R$ {receitas_pagas:,.2f}")
    col2.metric("Despesas Pagas",   f"R$ {despesas_pagas:,.2f}")
    col3.metric("Saldo em Caixa",   f"R$ {saldo:,.2f}",
                delta=f"R$ {saldo:,.2f}" if saldo >= 0 else None)

    st.markdown("---")
    col4, col5 = st.columns(2)
    col4.metric("Receitas Pendentes",  f"R$ {receitas_pend:,.2f}")
    col5.metric("Despesas Pendentes",  f"R$ {despesas_pend:,.2f}")

    if todos:
        st.markdown("---")
        st.subheader("Composição por Categoria")
        df = pd.DataFrame(todos)
        resumo = (
            df.groupby(["tipo", "categoria"])["valor"]
            .sum()
            .reset_index()
            .rename(columns={"tipo": "Tipo", "categoria": "Categoria", "valor": "Total (R$)"})
        )
        resumo["Total (R$)"] = resumo["Total (R$)"].map(lambda x: f"R$ {x:,.2f}")
        st.dataframe(resumo, use_container_width=True, hide_index=True)
