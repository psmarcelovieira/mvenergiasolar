import streamlit as st
from datetime import date, timedelta
import api_client
import pdf_reports

st.title("📄 Relatórios em PDF")

tab_proposta, tab_financeiro, tab_os = st.tabs([
    "🧾 Proposta Comercial",
    "💰 Extrato Financeiro",
    "🔧 Ordens de Serviço",
])

# ── PROPOSTA COMERCIAL ─────────────────────────────────────────────────────────
with tab_proposta:
    st.subheader("Gerar Proposta Comercial")

    vendas        = api_client.listar_vendas()
    clientes      = api_client.listar_clientes()
    produtos      = api_client.listar_produtos()
    colaboradores = api_client.listar_colaboradores()

    map_clientes  = {c["id"]: c for c in clientes}
    map_produtos  = {p["id"]: p["nome"] for p in produtos}
    map_colab     = {c["id_colaborador"]: c for c in colaboradores}

    if not vendas:
        st.info("Nenhuma venda cadastrada.")
    else:
        op_vendas = {
            f"#{v['id']} — {map_clientes.get(v['cliente_id'], {}).get('nome','?')} "
            f"— R$ {v['valor_final']:,.2f} ({v['status_venda']})": v
            for v in vendas
        }
        selecionada = st.selectbox("Selecione a venda", list(op_vendas.keys()))
        venda = op_vendas[selecionada]
        cliente = map_clientes.get(venda["cliente_id"], {})
        colab   = map_colab.get(venda.get("id_responsavel")) if venda.get("id_responsavel") else None

        col1, col2, col3 = st.columns(3)
        col1.metric("Cliente",      cliente.get("nome", "—"))
        col2.metric("Valor Total",  f"R$ {venda['valor_final']:,.2f}")
        col3.metric("Status",       venda["status_venda"])

        if st.button("📄 Gerar Proposta", type="primary"):
            try:
                pdf_bytes = pdf_reports.gerar_proposta(
                    venda      = venda,
                    cliente    = cliente,
                    itens      = venda.get("itens", []),
                    map_produtos = map_produtos,
                    colaborador  = colab,
                )
                nome_arquivo = f"proposta_{venda['id']}_{cliente.get('nome','cliente').split()[0]}.pdf"
                st.download_button(
                    "⬇️ Baixar Proposta PDF",
                    data      = pdf_bytes,
                    file_name = nome_arquivo,
                    mime      = "application/pdf",
                )
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")

# ── EXTRATO FINANCEIRO ─────────────────────────────────────────────────────────
with tab_financeiro:
    st.subheader("Gerar Extrato Financeiro")

    col1, col2 = st.columns(2)
    data_ini_f = col1.date_input("De",  value=date.today().replace(day=1), key="f_ini_ext")
    data_fim_f = col2.date_input("Até", value=date.today(),                key="f_fim_ext")

    STATUS_F = ["Todos", "Pendente", "Pago", "Atrasado"]
    filtro_st = st.selectbox("Status do lançamento", STATUS_F, key="f_st_ext")

    if st.button("📄 Gerar Extrato", type="primary"):
        lancamentos = api_client.listar_lancamentos()

        resultado = [
            l for l in lancamentos
            if data_ini_f.isoformat() <= l["data_vencimento"] <= data_fim_f.isoformat()
        ]
        if filtro_st != "Todos":
            resultado = [l for l in resultado if l["status_pagamento"] == filtro_st]

        if not resultado:
            st.warning("Nenhum lançamento encontrado nesse período.")
        else:
            try:
                pdf_bytes = pdf_reports.gerar_extrato_financeiro(
                    lancamentos = resultado,
                    data_ini    = data_ini_f.strftime("%d/%m/%Y"),
                    data_fim    = data_fim_f.strftime("%d/%m/%Y"),
                )
                nome_arquivo = f"extrato_{data_ini_f}_{data_fim_f}.pdf"
                st.download_button(
                    "⬇️ Baixar Extrato PDF",
                    data      = pdf_bytes,
                    file_name = nome_arquivo,
                    mime      = "application/pdf",
                )
                receitas = sum(float(l["valor"]) for l in resultado if l["tipo"] == "Receita")
                despesas = sum(float(l["valor"]) for l in resultado if l["tipo"] == "Despesa")
                c1, c2, c3 = st.columns(3)
                c1.metric("Receitas",  f"R$ {receitas:,.2f}")
                c2.metric("Despesas",  f"R$ {despesas:,.2f}")
                c3.metric("Saldo",     f"R$ {receitas - despesas:,.2f}")
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")

# ── RELATÓRIO DE OS ────────────────────────────────────────────────────────────
with tab_os:
    st.subheader("Gerar Relatório de Ordens de Serviço")

    col1, col2 = st.columns(2)
    data_ini_os = col1.date_input("De",  value=date.today() - timedelta(days=30), key="f_ini_os")
    data_fim_os = col2.date_input("Até", value=date.today(),                      key="f_fim_os")

    STATUS_OS  = ["Todos", "Aberta", "Em Andamento", "Concluída", "Cancelada"]
    TIPOS_OS   = ["Todos", "Preventiva", "Corretiva", "Limpeza", "Inspeção", "Garantia", "Outros"]
    col3, col4 = st.columns(2)
    filtro_st_os  = col3.selectbox("Status",       STATUS_OS,  key="f_st_os")
    filtro_tipo   = col4.selectbox("Tipo de OS",   TIPOS_OS,   key="f_tipo_os")

    if st.button("📄 Gerar Relatório de OS", type="primary"):
        ordens    = api_client.listar_ordens_servico()
        clientes  = api_client.listar_clientes()
        map_cli   = {c["id"]: c["nome"] for c in clientes}

        resultado = [
            o for o in ordens
            if data_ini_os.isoformat() <= o["data_abertura"] <= data_fim_os.isoformat()
        ]
        if filtro_st_os != "Todos":
            resultado = [o for o in resultado if o["status_os"] == filtro_st_os]
        if filtro_tipo != "Todos":
            resultado = [o for o in resultado if o["tipo_servico"] == filtro_tipo]

        if not resultado:
            st.warning("Nenhuma OS encontrada nesse período.")
        else:
            try:
                pdf_bytes = pdf_reports.gerar_relatorio_os(
                    ordens       = resultado,
                    map_clientes = map_cli,
                    data_ini     = data_ini_os.strftime("%d/%m/%Y"),
                    data_fim     = data_fim_os.strftime("%d/%m/%Y"),
                )
                nome_arquivo = f"os_{data_ini_os}_{data_fim_os}.pdf"
                st.download_button(
                    "⬇️ Baixar Relatório PDF",
                    data      = pdf_bytes,
                    file_name = nome_arquivo,
                    mime      = "application/pdf",
                )
                total = sum(float(o.get("custo_total") or 0) for o in resultado)
                c1, c2, c3 = st.columns(3)
                c1.metric("OS no período",  len(resultado))
                c2.metric("Concluídas",     sum(1 for o in resultado if o["status_os"] == "Concluída"))
                c3.metric("Total faturado", f"R$ {total:,.2f}")
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")
