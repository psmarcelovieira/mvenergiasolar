import streamlit as st
import pandas as pd
import api_client

st.title("🛒 Vendas")

clientes      = api_client.listar_clientes()
produtos      = api_client.listar_produtos()
colaboradores = api_client.listar_colaboradores()

map_clientes = {c["id"]: c["nome"] for c in clientes}

STATUS_ICONE = {
    "Orçamento": "🟡", "Negociação": "🟠", "Aprovado": "🟢",
    "Em Andamento": "🔵", "Concluído": "⚫", "Cancelado": "🔴",
}

tab_lista, tab_nova = st.tabs(["📋 Lista de Vendas", "➕ Nova Venda"])

# ── LISTA ──────────────────────────────────────────────────────────────────────
with tab_lista:
    vendas = api_client.listar_vendas()
    if not vendas:
        st.info("Nenhuma venda cadastrada ainda.")
    else:
        STATUS_V = ["Todos","Orçamento","Negociação","Aprovado","Em Andamento","Concluído","Cancelado"]
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        filtro_st  = col_f1.selectbox("Status", STATUS_V, key="f_st_venda")
        busca_cli  = col_f2.text_input("🔍 Cliente", placeholder="Nome do cliente...", key="f_cli_venda")
        data_ini   = col_f3.date_input("De",  value=None, key="f_ini_venda")
        data_fim   = col_f4.date_input("Até", value=None, key="f_fim_venda")

        resultado = vendas
        if filtro_st != "Todos":
            resultado = [v for v in resultado if v["status_venda"] == filtro_st]
        if busca_cli:
            resultado = [v for v in resultado
                         if busca_cli.lower() in map_clientes.get(v["cliente_id"], "").lower()]
        if data_ini:
            resultado = [v for v in resultado if v["data_orcamento"] >= str(data_ini)]
        if data_fim:
            resultado = [v for v in resultado if v["data_orcamento"] <= str(data_fim)]

        st.caption(f"{len(resultado)} venda(s) encontrada(s)")

        cab = st.columns([1, 3, 2, 2, 2, 2])
        for col, titulo in zip(cab, ["#", "Cliente", "Status", "Valor Final", "Data", "Ação"]):
            col.markdown(f"**{titulo}**")
        st.divider()

        CANCELAVEIS = {"Orçamento", "Negociação", "Aprovado", "Em Andamento", "Concluído"}

        for v in resultado:
            status = v["status_venda"]
            col1, col2, col3, col4, col5, col6 = st.columns([1, 3, 2, 2, 2, 2])
            col1.write(f"#{v['id']}")
            col2.write(map_clientes.get(v["cliente_id"], f"#{v['cliente_id']}"))
            col3.write(f"{STATUS_ICONE.get(status, '⚪')} {status}")
            col4.write(f"R$ {v['valor_final']:,.2f}")
            col5.write(v["data_orcamento"])

            if status == "Orçamento":
                btn_apr, btn_del, btn_canc = col6.columns(3)
                if btn_apr.button("✅", key=f"apr_{v['id']}", help="Aprovar venda"):
                    resp = api_client.aprovar_venda(v["id"])
                    if resp.status_code == 200:
                        st.success(f"Venda #{v['id']} aprovada!")
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail"))
                if btn_del.button("🗑️", key=f"del_{v['id']}", help="Excluir orçamento"):
                    resp = api_client.excluir_venda(v["id"])
                    if resp.status_code == 204:
                        st.success(f"Venda #{v['id']} excluída.")
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail"))
                if btn_canc.button("🚫", key=f"canc_btn_{v['id']}", help="Cancelar venda"):
                    st.session_state[f"cancelar_{v['id']}"] = True

            elif status in CANCELAVEIS - {"Orçamento"}:
                if col6.button("🚫 Cancelar", key=f"canc_btn_{v['id']}", help="Cancelar venda"):
                    st.session_state[f"cancelar_{v['id']}"] = True

            # ── Modal de cancelamento ──────────────────────────────────────────
            if st.session_state.get(f"cancelar_{v['id']}"):
                with st.expander(f"🚫 Cancelar Venda #{v['id']} — Autorização Administrativa",
                                 expanded=True):
                    st.warning(
                        "Esta ação é **irreversível**. "
                        "O cancelamento será registrado com trilha de auditoria.",
                        icon="⚠️",
                    )
                    if status in {"Aprovado", "Em Andamento", "Concluído"}:
                        st.info("✅ Estoque será revertido automaticamente.", icon="📦")
                        st.info("✅ Lançamentos financeiros pendentes serão cancelados.", icon="💰")

                    motivo = st.text_area(
                        "Motivo do cancelamento *",
                        placeholder="Descreva o motivo (mínimo 10 caracteres)...",
                        key=f"motivo_{v['id']}",
                    )
                    st.markdown("**Credenciais do Administrador**")
                    col_a, col_b = st.columns(2)
                    admin_login = col_a.text_input("Login do Admin *", key=f"adm_login_{v['id']}")
                    admin_senha = col_b.text_input("Senha do Admin *", type="password",
                                                   key=f"adm_senha_{v['id']}")

                    col_conf, col_abort = st.columns([1, 3])
                    if col_conf.button("Confirmar Cancelamento", type="primary",
                                       key=f"conf_canc_{v['id']}"):
                        usuario_logado = st.session_state.get("usuario", {})
                        if not motivo or len(motivo.strip()) < 10:
                            st.error("Motivo deve ter pelo menos 10 caracteres.")
                        elif not admin_login or not admin_senha:
                            st.error("Informe as credenciais do administrador.")
                        else:
                            resp = api_client.cancelar_venda(
                                venda_id          = v["id"],
                                solicitante_login = usuario_logado.get("login", ""),
                                autorizador_login = admin_login,
                                autorizador_senha = admin_senha,
                                motivo            = motivo,
                            )
                            if resp.status_code == 200:
                                dados_canc = resp.json()
                                st.success(
                                    f"Venda #{v['id']} cancelada por "
                                    f"**{dados_canc['autorizador_nome']}**. "
                                    f"Estoque revertido: {'✅' if dados_canc['estoque_revertido'] else '—'} | "
                                    f"Financeiro tratado: {'✅' if dados_canc['financeiro_tratado'] else '—'}"
                                )
                                del st.session_state[f"cancelar_{v['id']}"]
                                st.rerun()
                            else:
                                detalhe = resp.json().get("detail", "Erro desconhecido")
                                st.error(f"Cancelamento recusado: {detalhe}")

                    if col_abort.button("Voltar", key=f"abort_canc_{v['id']}"):
                        del st.session_state[f"cancelar_{v['id']}"]
                        st.rerun()

# ── NOVA VENDA ─────────────────────────────────────────────────────────────────
with tab_nova:
    if not clientes:
        st.warning("Cadastre pelo menos um cliente antes de criar uma venda.")
    elif not produtos:
        st.warning("Cadastre pelo menos um produto antes de criar uma venda.")
    else:
        if "itens_venda" not in st.session_state:
            st.session_state.itens_venda = []

        st.subheader("Dados da Venda")
        col1, col2 = st.columns(2)

        with col1:
            op_clientes = {c["nome"]: c["id"] for c in clientes}
            cliente_id  = op_clientes[st.selectbox("Cliente *", list(op_clientes.keys()))]

            op_colab = {"(sem responsável)": None}
            op_colab.update({c["nome"]: c["id_colaborador"] for c in colaboradores})
            id_responsavel = op_colab[st.selectbox("Responsável", list(op_colab.keys()))]

            forma_pagamento = st.selectbox("Forma de Pagamento *",
                ["PIX", "Boleto", "Dinheiro", "Cartão", "Financiamento"])

        with col2:
            valor_instalacao = st.number_input("Valor Instalação (R$)", min_value=0.0, step=100.0)
            desconto         = st.number_input("Desconto (R$)", min_value=0.0, step=50.0)
            parcelas         = st.number_input("Parcelas", min_value=1, max_value=60, value=1)

        st.markdown("---")
        st.subheader("Itens da Venda")

        op_produtos = {p["nome"]: p for p in produtos}
        c1, c2, c3 = st.columns([4, 2, 2])

        with c1:
            prod_nome = st.selectbox("Produto", list(op_produtos.keys()))
        with c2:
            quantidade = st.number_input("Quantidade", min_value=1, step=1, value=1)
        with c3:
            st.write("")
            st.write("")
            if st.button("➕ Adicionar Item"):
                prod = op_produtos[prod_nome]
                st.session_state.itens_venda.append({
                    "produto_id"    : prod["id"],
                    "nome"          : prod["nome"],
                    "quantidade"    : quantidade,
                    "preco_unitario": prod["preco_venda"],
                })
                st.rerun()

        if st.session_state.itens_venda:
            df = pd.DataFrame(st.session_state.itens_venda)
            df["subtotal"] = df["quantidade"] * df["preco_unitario"]
            st.dataframe(
                df[["nome","quantidade","preco_unitario","subtotal"]].rename(columns={
                    "nome":"Produto","quantidade":"Qtd",
                    "preco_unitario":"Preço Unit.","subtotal":"Subtotal"
                }),
                use_container_width=True, hide_index=True
            )
            total_equip = df["subtotal"].sum()
            valor_final = total_equip + valor_instalacao - desconto
            st.markdown(f"**Equipamentos:** R$ {total_equip:,.2f} &nbsp;|&nbsp; **Instalação:** R$ {valor_instalacao:,.2f} &nbsp;|&nbsp; **Total:** R$ {valor_final:,.2f}")

            c_limpar, c_salvar = st.columns([1, 4])
            if c_limpar.button("🗑️ Limpar"):
                st.session_state.itens_venda = []
                st.rerun()

            if c_salvar.button("💾 Criar Venda", type="primary"):
                payload = {
                    "cliente_id"      : cliente_id,
                    "id_responsavel"  : id_responsavel,
                    "valor_instalacao": valor_instalacao,
                    "desconto"        : desconto,
                    "forma_pagamento" : forma_pagamento,
                    "parcelas"        : int(parcelas),
                    "itens"           : [
                        {"produto_id": i["produto_id"], "quantidade": i["quantidade"]}
                        for i in st.session_state.itens_venda
                    ],
                }
                resp = api_client.criar_venda(payload)
                if resp.status_code == 201:
                    st.success("✅ Venda criada com sucesso!")
                    st.session_state.itens_venda = []
                    st.rerun()
                else:
                    st.error(f"Erro: {resp.json().get('detail', 'Erro desconhecido')}")
        else:
            st.info("Adicione pelo menos um produto para criar a venda.")
