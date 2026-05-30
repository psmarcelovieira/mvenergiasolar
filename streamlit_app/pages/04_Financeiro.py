import streamlit as st
import pandas as pd
from datetime import date
import api_client

st.title("💰 Financeiro")

TIPO_ICONE   = {"Receita": "🟢", "Despesa": "🔴"}
STATUS_COR   = {"Pendente": "🟡", "Pago": "✅", "Cancelado": "❌", "Atrasado": "⚠️"}
TIPO_REC_OPT = ["Único", "Parcelado", "Recorrente"]

tab_lista, tab_series, tab_novo, tab_saldo, tab_fluxo = st.tabs([
    "📋 Lançamentos", "🔁 Séries", "➕ Novo", "📊 Saldo", "📈 Fluxo de Caixa"
])

# ══════════════════════════════════════════════════════════════════════════════
# ABA: LANÇAMENTOS
# ══════════════════════════════════════════════════════════════════════════════
with tab_lista:
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filtro_tipo   = st.selectbox("Tipo",   ["Todos", "Receita", "Despesa"], key="ft")
    with col_f2:
        filtro_status = st.selectbox("Status", ["Todos", "Pendente", "Pago", "Cancelado"], key="fs")
    with col_f3:
        filtro_origem = st.selectbox("Origem", ["Todos", "Avulso", "Série/Parcelado"], key="fo")

    lancamentos = api_client.listar_lancamentos()

    if filtro_tipo   != "Todos":
        lancamentos = [l for l in lancamentos if l["tipo"] == filtro_tipo]
    if filtro_status != "Todos":
        lancamentos = [l for l in lancamentos if l["status_pagamento"] == filtro_status]
    if filtro_origem == "Avulso":
        lancamentos = [l for l in lancamentos if not l.get("lancamento_mestre_id")]
    elif filtro_origem == "Série/Parcelado":
        lancamentos = [l for l in lancamentos if l.get("lancamento_mestre_id")]

    if not lancamentos:
        st.info("Nenhum lançamento encontrado.")
    else:
        cab = st.columns([1, 2, 4, 2, 2, 2, 3])
        for col, titulo in zip(cab, ["#", "Tipo", "Descrição", "Valor", "Vencimento", "Status", "Ação"]):
            col.markdown(f"**{titulo}**")
        st.divider()

        for l in lancamentos:
            tipo   = l["tipo"]
            status = l["status_pagamento"]
            c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 2, 4, 2, 2, 2, 3])
            c1.write(f"#{l['id']}")
            c2.write(f"{TIPO_ICONE.get(tipo, '')} {tipo}")
            c3.write(l["descricao"])
            c4.write(f"R$ {l['valor']:,.2f}")
            c5.write(l["data_vencimento"])
            c6.write(f"{STATUS_COR.get(status, '')} {status}")

            with c7:
                if status == "Pendente":
                    cols_btn = st.columns(2)
                    if cols_btn[0].button("✅", key=f"pagar_{l['id']}", help="Marcar como pago"):
                        resp = api_client.pagar_lancamento(l["id"])
                        if resp.status_code == 200:
                            st.rerun()
                        else:
                            st.error(resp.json().get("detail", "Erro"))
                    if cols_btn[1].button("❌", key=f"canc_{l['id']}", help="Cancelar parcela"):
                        resp = api_client.cancelar_lancamento(l["id"])
                        if resp.status_code == 200:
                            st.rerun()
                        else:
                            st.error(resp.json().get("detail", "Erro"))
                else:
                    st.write(l.get("data_pagamento") or "—")


# ══════════════════════════════════════════════════════════════════════════════
# ABA: SÉRIES (LancamentoMestre)
# ══════════════════════════════════════════════════════════════════════════════
with tab_series:
    mestres = api_client.listar_mestres()

    if not mestres:
        st.info("Nenhuma série ou parcelamento cadastrado.")
    else:
        for m in mestres:
            tipo_icon = TIPO_ICONE.get(m["tipo"], "")
            ativo_tag = "🟢 Ativa" if m["ativo"] else "🔴 Encerrada"
            with st.expander(
                f"{tipo_icon} {m['descricao']} — {m['tipo_recorrencia']} | {ativo_tag}",
                expanded=False,
            ):
                col_i1, col_i2, col_i3, col_i4 = st.columns(4)
                col_i1.metric("Valor por parcela", f"R$ {m['valor']:,.2f}")
                col_i2.metric("Intervalo", f"{m['intervalo_meses']} mês(es)")
                col_i3.metric("Início", m["data_inicio"])
                col_i4.metric("Término", m["data_fim"] or "Aberta")

                parcelas = m.get("parcelas", [])
                pagas    = sum(1 for p in parcelas if p["status_pagamento"] == "Pago")
                pend     = sum(1 for p in parcelas if p["status_pagamento"] == "Pendente")
                st.caption(f"Parcelas: {len(parcelas)} total | {pagas} pagas | {pend} pendentes")

                if parcelas:
                    df = pd.DataFrame([{
                        "Nº":         p.get("parcela_num", "—"),
                        "Vencimento": p["data_vencimento"],
                        "Valor":      f"R$ {p['valor']:,.2f}",
                        "Status":     f"{STATUS_COR.get(p['status_pagamento'], '')} {p['status_pagamento']}",
                    } for p in parcelas])
                    st.dataframe(df, use_container_width=True, hide_index=True)

                st.markdown("**Ações na série**")
                col_a1, col_a2 = st.columns(2)

                # Editar parcelas futuras
                with col_a1:
                    with st.form(f"edit_serie_{m['id']}"):
                        st.markdown("✏️ Alterar parcelas futuras")
                        novo_val = st.number_input("Novo valor (deixe 0 para não alterar)",
                                                   min_value=0.0, value=0.0, format="%.2f",
                                                   key=f"nv_{m['id']}")
                        nova_desc = st.text_input("Nova descrição (opcional)", key=f"nd_{m['id']}")
                        a_partir  = st.date_input("A partir de", value=date.today(), key=f"ap_{m['id']}")
                        if st.form_submit_button("Salvar alterações"):
                            payload = {"a_partir_de": str(a_partir)}
                            if novo_val > 0:
                                payload["novo_valor"] = novo_val
                            if nova_desc.strip():
                                payload["nova_descricao"] = nova_desc.strip()
                            resp = api_client.editar_parcelas_futuras(m["id"], payload)
                            if resp.status_code == 200:
                                st.success("Parcelas atualizadas!")
                                st.rerun()
                            else:
                                st.error(resp.json().get("detail", "Erro"))

                # Cancelar série
                with col_a2:
                    with st.form(f"canc_serie_{m['id']}"):
                        st.markdown("🚫 Cancelar parcelas")
                        apenas_futuras = st.checkbox("Apenas a partir de hoje", value=True,
                                                     key=f"apf_{m['id']}")
                        if st.form_submit_button("Cancelar série", type="primary"):
                            a_partir_de = str(date.today()) if apenas_futuras else None
                            resp = api_client.cancelar_serie(m["id"], a_partir_de)
                            if resp.status_code == 200:
                                dados = resp.json()
                                st.success(f"{dados['canceladas']} parcela(s) cancelada(s).")
                                st.rerun()
                            else:
                                st.error(resp.json().get("detail", "Erro"))


# ══════════════════════════════════════════════════════════════════════════════
# ABA: NOVO LANÇAMENTO
# ══════════════════════════════════════════════════════════════════════════════
with tab_novo:
    CATEGORIAS = [
        "Venda Equipamentos", "Serviço Instalação", "Manutenção", "Comissão",
        "Fornecedor", "Salário", "Aluguel", "Marketing", "Imposto", "Outras",
    ]
    FORMAS_PAG = ["PIX", "Boleto", "Dinheiro", "Cartão", "Financiamento"]

    tipo_rec = st.radio("Tipo de lançamento", TIPO_REC_OPT, horizontal=True)

    with st.form("form_novo_lancamento"):
        col1, col2 = st.columns(2)
        with col1:
            tipo       = st.selectbox("Tipo",       ["Receita", "Despesa"])
            categoria  = st.selectbox("Categoria",  CATEGORIAS)
            descricao  = st.text_input("Descrição *")
            valor      = st.number_input("Valor (R$) *", min_value=0.01, format="%.2f")
        with col2:
            forma_pag  = st.selectbox("Forma de pagamento", FORMAS_PAG)
            data_ini   = st.date_input("Data do 1º vencimento *", value=date.today())
            observ     = st.text_area("Observações", height=80)

        # Campos extras por tipo
        num_parcelas    = None
        intervalo_meses = 1
        data_fim        = None

        if tipo_rec == "Parcelado":
            col_p1, col_p2 = st.columns(2)
            num_parcelas    = col_p1.number_input("Número de parcelas *", min_value=2, value=12)
            intervalo_meses = col_p2.number_input("Intervalo (meses)", min_value=1, value=1)

        elif tipo_rec == "Recorrente":
            col_r1, col_r2 = st.columns(2)
            intervalo_meses = col_r1.number_input("Intervalo (meses)", min_value=1, value=1)
            tem_fim = col_r2.checkbox("Tem data de término?")
            if tem_fim:
                data_fim = st.date_input("Data de término")

        submeter = st.form_submit_button("💾 Criar lançamento", type="primary")

    if submeter:
        if not descricao.strip():
            st.error("Descrição é obrigatória.")
        elif valor <= 0:
            st.error("Valor deve ser maior que zero.")
        else:
            tipo_rec_map = {"Único": "Único", "Parcelado": "Parcelado", "Recorrente": "Recorrente"}

            if tipo_rec == "Único":
                payload = {
                    "tipo":            tipo,
                    "categoria":       categoria,
                    "descricao":       descricao.strip(),
                    "valor":           valor,
                    "data_vencimento": str(data_ini),
                    "forma_pagamento": forma_pag,
                    "observacoes":     observ.strip() or None,
                }
                resp = api_client.criar_lancamento(payload)
            else:
                payload = {
                    "tipo":             tipo,
                    "categoria":        categoria,
                    "descricao":        descricao.strip(),
                    "valor":            valor,
                    "tipo_recorrencia": tipo_rec_map[tipo_rec],
                    "data_inicio":      str(data_ini),
                    "forma_pagamento":  forma_pag,
                    "intervalo_meses":  int(intervalo_meses),
                    "observacoes":      observ.strip() or None,
                }
                if tipo_rec == "Parcelado":
                    payload["num_parcelas"] = int(num_parcelas)
                if data_fim:
                    payload["data_fim"] = str(data_fim)
                resp = api_client.criar_lancamento_lote(payload)

            if resp.status_code in (200, 201):
                dados = resp.json()
                if tipo_rec == "Único":
                    st.success(f"Lançamento #{dados['id']} criado!")
                else:
                    n = len(dados.get("parcelas", []))
                    st.success(f"Série criada com {n} parcela(s)!")
                st.rerun()
            else:
                st.error(resp.json().get("detail", "Erro ao criar lançamento"))


def _criar_lancamento_avulso(dados: dict):
    return api_client.criar_lancamento(dados)


# ══════════════════════════════════════════════════════════════════════════════
# ABA: SALDO
# ══════════════════════════════════════════════════════════════════════════════
with tab_saldo:
    todos = api_client.listar_lancamentos()

    rec_pagas  = sum(l["valor"] for l in todos if l["tipo"] == "Receita" and l["status_pagamento"] == "Pago")
    desp_pagas = sum(l["valor"] for l in todos if l["tipo"] == "Despesa" and l["status_pagamento"] == "Pago")
    rec_pend   = sum(l["valor"] for l in todos if l["tipo"] == "Receita" and l["status_pagamento"] == "Pendente")
    desp_pend  = sum(l["valor"] for l in todos if l["tipo"] == "Despesa" and l["status_pagamento"] == "Pendente")
    saldo      = rec_pagas - desp_pagas

    col1, col2, col3 = st.columns(3)
    col1.metric("Receitas Pagas",   f"R$ {rec_pagas:,.2f}")
    col2.metric("Despesas Pagas",   f"R$ {desp_pagas:,.2f}")
    col3.metric("Saldo em Caixa",   f"R$ {saldo:,.2f}")

    st.markdown("---")
    col4, col5, col6 = st.columns(3)
    col4.metric("A Receber (Pendente)", f"R$ {rec_pend:,.2f}")
    col5.metric("A Pagar (Pendente)",   f"R$ {desp_pend:,.2f}")
    col6.metric("Saldo Projetado",      f"R$ {saldo + rec_pend - desp_pend:,.2f}")

    if todos:
        st.markdown("---")
        st.subheader("Composição por Categoria")
        df = pd.DataFrame(todos)
        ativos = df[df["status_pagamento"] != "Cancelado"]
        resumo = (
            ativos.groupby(["tipo", "categoria"])["valor"]
            .sum()
            .reset_index()
            .rename(columns={"tipo": "Tipo", "categoria": "Categoria", "valor": "Total (R$)"})
        )
        resumo["Total (R$)"] = resumo["Total (R$)"].map(lambda x: f"R$ {x:,.2f}")
        st.dataframe(resumo, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# ABA: FLUXO DE CAIXA
# ══════════════════════════════════════════════════════════════════════════════
with tab_fluxo:
    import plotly.graph_objects as go

    meses = st.slider("Meses para projetar", min_value=1, max_value=24, value=6)
    fluxo = api_client.get_fluxo_caixa(meses)

    if not fluxo:
        st.info("Sem dados para exibir.")
    else:
        df_f = pd.DataFrame(fluxo)

        # Tabela resumo
        df_display = df_f.rename(columns={
            "mes":                "Mês",
            "receitas_pagas":     "Receitas Pagas",
            "despesas_pagas":     "Despesas Pagas",
            "receitas_previstas": "A Receber",
            "despesas_previstas": "A Pagar",
            "saldo_real":         "Saldo Real",
            "saldo_projetado":    "Saldo Projetado",
        })
        for col in df_display.columns[1:]:
            df_display[col] = df_display[col].map(lambda x: f"R$ {x:,.2f}")
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        st.markdown("---")
        # Gráfico de barras agrupadas
        fig = go.Figure()
        fig.add_bar(name="Receitas Pagas",    x=df_f["mes"], y=df_f["receitas_pagas"],     marker_color="#2ecc71")
        fig.add_bar(name="Despesas Pagas",    x=df_f["mes"], y=df_f["despesas_pagas"],     marker_color="#e74c3c")
        fig.add_bar(name="A Receber (prev.)", x=df_f["mes"], y=df_f["receitas_previstas"], marker_color="#27ae60", opacity=0.5)
        fig.add_bar(name="A Pagar (prev.)",   x=df_f["mes"], y=df_f["despesas_previstas"], marker_color="#c0392b", opacity=0.5)
        fig.update_layout(barmode="group", title="Fluxo de Caixa Mensal",
                          xaxis_title="Mês", yaxis_title="R$", height=400)
        st.plotly_chart(fig, use_container_width=True)

        # Linha de saldo projetado
        fig2 = go.Figure()
        fig2.add_scatter(name="Saldo Real",      x=df_f["mes"], y=df_f["saldo_real"],
                         mode="lines+markers", line=dict(color="#3498db", width=2))
        fig2.add_scatter(name="Saldo Projetado", x=df_f["mes"], y=df_f["saldo_projetado"],
                         mode="lines+markers", line=dict(color="#9b59b6", width=2, dash="dash"))
        fig2.update_layout(title="Evolução do Saldo", xaxis_title="Mês",
                           yaxis_title="R$", height=350)
        st.plotly_chart(fig2, use_container_width=True)
