import streamlit as st
import api_client

st.set_page_config(page_title="Prestações de Contas", layout="wide")
from auth import verificar_admin, rodape_usuario
verificar_admin()
rodape_usuario()
st.title("🤝 Prestações de Contas")

STATUS_ICONE = {"Pendente": "🟡", "Paga": "✅"}

prestacoes = api_client.listar_prestacoes()

if not prestacoes:
    st.info("Nenhuma prestação de contas encontrada. Prestações são criadas automaticamente ao aprovar uma venda com responsável.")
else:
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_status = st.selectbox("Filtrar por Status", ["Todos", "Pendente", "Paga"])
    with col_f2:
        colaboradores  = api_client.listar_colaboradores()
        nomes_colab    = ["Todos"] + [c["nome"] for c in colaboradores]
        ids_colab      = {c["nome"]: c["id_colaborador"] for c in colaboradores}
        filtro_colab   = st.selectbox("Filtrar por Colaborador", nomes_colab)

    if filtro_status != "Todos":
        prestacoes = [p for p in prestacoes if p["status_pagto"] == filtro_status]
    if filtro_colab != "Todos":
        id_filtro  = ids_colab[filtro_colab]
        prestacoes = [p for p in prestacoes if p["id_colaborador"] == id_filtro]

    cab = st.columns([1, 2, 1, 2, 2, 2, 2, 2])
    for col, titulo in zip(cab, ["ID", "Colaborador", "Venda", "Valor Venda", "Comissão", "Data", "Status", "Ação"]):
        col.markdown(f"**{titulo}**")
    st.divider()

    map_colab = {c["id_colaborador"]: c["nome"] for c in colaboradores}

    for p in prestacoes:
        status = p["status_pagto"]
        c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1, 2, 1, 2, 2, 2, 2, 2])
        c1.write(p["id_prestacao"])
        c2.write(map_colab.get(p["id_colaborador"], p["id_colaborador"]))
        c3.write(f"#{p['id_venda']}")
        c4.write(f"R$ {p['valor_recebido']:,.2f}")
        c5.write(f"R$ {p['valor_comissao']:,.2f} ({p['percentual_comissao']*100:.1f}%)")
        c6.write(p["data"])
        c7.write(f"{STATUS_ICONE.get(status, '')} {status}")

        if status == "Pendente":
            if c8.button("💸 Pagar", key=f"pagar_{p['id_prestacao']}"):
                resp = api_client.pagar_prestacao(p["id_prestacao"])
                if resp.status_code == 200:
                    st.success(f"Comissão {p['id_prestacao']} paga!")
                    st.rerun()
                else:
                    st.error(resp.json().get("detail", "Erro ao pagar"))
        else:
            c8.write(p.get("data_pagto") or "—")

    st.markdown("---")
    pendentes = [p for p in api_client.listar_prestacoes() if p["status_pagto"] == "Pendente"]
    pagas     = [p for p in api_client.listar_prestacoes() if p["status_pagto"] == "Paga"]

    total_pendente = sum(p["valor_comissao"] for p in pendentes)
    total_pago     = sum(p["valor_comissao"] for p in pagas)

    col1, col2, col3 = st.columns(3)
    col1.metric("Comissões Pendentes",  f"R$ {total_pendente:,.2f}", delta=f"{len(pendentes)} registro(s)")
    col2.metric("Comissões Pagas",      f"R$ {total_pago:,.2f}",     delta=f"{len(pagas)} registro(s)")
    col3.metric("Total de Comissões",   f"R$ {total_pendente + total_pago:,.2f}")
