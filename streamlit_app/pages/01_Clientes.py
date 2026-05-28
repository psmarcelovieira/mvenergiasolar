import streamlit as st
import pandas as pd
import api_client

st.title("👥 Clientes")

UFS = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS",
       "MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]

ESCOLARIDADES = ["Fundamental", "Médio", "Superior", "Pós-graduação"]
TIPOS_IMOVEL  = ["Residencial", "Comercial", "Rural", "Industrial"]
ORIGENS_LEAD  = ["Indicação", "Google", "Instagram", "Facebook", "WhatsApp", "Site", "Evento", "Outros"]
STATUS_LISTA  = ["Ativo", "Inativo", "Prospecto", "Bloqueado"]

tab_lista, tab_novo, tab_edit = st.tabs(["📋 Lista", "➕ Novo Cliente", "✏️ Editar / Excluir"])

# ── LISTA ──────────────────────────────────────────────────────────────────────
with tab_lista:
    clientes_lista = api_client.listar_clientes()
    if not clientes_lista:
        st.info("Nenhum cliente cadastrado ainda.")
    else:
        col_f1, col_f2, col_f3 = st.columns([3, 2, 2])
        busca         = col_f1.text_input("🔍 Buscar por nome", placeholder="Digite o nome...")
        filtro_status = col_f2.selectbox("Status", ["Todos"] + STATUS_LISTA, key="f_st_cli")
        cidades       = ["Todas"] + sorted({c["cidade"] for c in clientes_lista if c.get("cidade")})
        filtro_cidade = col_f3.selectbox("Cidade", cidades, key="f_cid_cli")

        resultado = clientes_lista
        if busca:
            resultado = [c for c in resultado if busca.lower() in c["nome"].lower()]
        if filtro_status != "Todos":
            resultado = [c for c in resultado if c["status"] == filtro_status]
        if filtro_cidade != "Todas":
            resultado = [c for c in resultado if c.get("cidade") == filtro_cidade]

        st.caption(f"{len(resultado)} cliente(s) encontrado(s)")

        if resultado:
            def _wapp(tel):
                if not tel:
                    return None
                d = "".join(filter(str.isdigit, str(tel)))
                return f"https://wa.me/55{d}" if d else None

            df = pd.DataFrame(resultado)
            df["📱"] = df["telefone"].apply(_wapp)
            df["Conta Energia"] = df["conta_energia"].apply(lambda x: f"R$ {x:,.2f}" if x else "—")
            df_show = df[["id","nome","tipo_pessoa","cidade","uf","Conta Energia","origem_lead","status","📱"]].copy()
            df_show.columns = ["ID","Nome","Tipo","Cidade","UF","Conta Energia","Origem","Status","📱"]
            st.dataframe(
                df_show,
                use_container_width=True,
                hide_index=True,
                column_config={"📱": st.column_config.LinkColumn("📱 WhatsApp", display_text="Abrir")}
            )
        else:
            st.info("Nenhum cliente encontrado com esses filtros.")

# ── NOVO CLIENTE ───────────────────────────────────────────────────────────────
with tab_novo:
    with st.form("form_cliente"):
        st.subheader("Dados Básicos")
        col1, col2 = st.columns(2)

        with col1:
            tipo_pessoa = st.selectbox("Tipo de Pessoa *", ["PF", "PJ"])
            nome        = st.text_input("Nome *")
            cpf_cnpj    = st.text_input("CPF (11 dígitos) ou CNPJ (14 dígitos) *")
            email       = st.text_input("Email *")

        with col2:
            telefone = st.text_input("Telefone *")
            cidade   = st.text_input("Cidade *")
            uf       = st.selectbox("UF *", UFS, index=UFS.index("SP"))
            endereco = st.text_input("Endereço")
            bairro   = st.text_input("Bairro")

        st.markdown("---")
        st.subheader("Perfil para Análise de Vendas")
        col3, col4 = st.columns(2)

        with col3:
            conta_energia = st.number_input(
                "Conta de Energia Mensal (R$)",
                min_value=0.0, step=50.0,
                help="Principal indicador de ROI para energia solar"
            )
            tipo_imovel_sel = st.selectbox("Tipo de Imóvel", ["(não informado)"] + TIPOS_IMOVEL)
            origem_lead_sel = st.selectbox("Como nos conheceu?", ["(não informado)"] + ORIGENS_LEAD)

        with col4:
            renda_mensal    = st.number_input("Renda Mensal (R$)", min_value=0.0, step=500.0)
            escolaridade_sel = st.selectbox("Escolaridade", ["(não informado)"] + ESCOLARIDADES)
            profissao       = st.text_input("Profissão")

        salvar = st.form_submit_button("Cadastrar Cliente", type="primary")

        if salvar:
            if not all([nome, cpf_cnpj, email, telefone, cidade]):
                st.error("Preencha todos os campos obrigatórios.")
            else:
                resp = api_client.criar_cliente({
                    "tipo_pessoa"  : tipo_pessoa,
                    "nome"         : nome,
                    "cpf_cnpj"     : cpf_cnpj,
                    "email"        : email,
                    "telefone"     : telefone,
                    "cidade"       : cidade,
                    "uf"           : uf,
                    "endereco"     : endereco.strip() or None,
                    "bairro"       : bairro.strip() or None,
                    "conta_energia": conta_energia if conta_energia > 0 else None,
                    "tipo_imovel"  : None if tipo_imovel_sel == "(não informado)" else tipo_imovel_sel,
                    "origem_lead"  : None if origem_lead_sel == "(não informado)" else origem_lead_sel,
                    "renda_mensal" : renda_mensal if renda_mensal > 0 else None,
                    "escolaridade" : None if escolaridade_sel == "(não informado)" else escolaridade_sel,
                    "profissao"    : profissao.strip() or None,
                })
                if resp.status_code == 201:
                    st.success(f"✅ Cliente **{nome}** cadastrado com sucesso!")
                    st.rerun()
                elif resp.status_code == 409:
                    st.error("CPF/CNPJ já cadastrado.")
                else:
                    st.error(f"Erro: {resp.json().get('detail', 'Erro desconhecido')}")

# ── EDITAR / EXCLUIR ───────────────────────────────────────────────────────────
with tab_edit:
    clientes_edit = api_client.listar_clientes()
    if not clientes_edit:
        st.info("Nenhum cliente cadastrado.")
    else:
        op = {f"[#{c['id']}] {c['nome']}": c for c in clientes_edit}
        selecionado = st.selectbox("Selecione o cliente", list(op.keys()))
        c = op[selecionado]

        col_btn1, col_btn2, _ = st.columns([1, 1, 4])
        acao_editar  = col_btn1.button("✏️ Editar",  key="btn_edit_cli")
        acao_excluir = col_btn2.button("🗑️ Excluir", key="btn_del_cli")

        if acao_editar:
            st.session_state["editar_cliente_id"] = c["id"]

        if acao_excluir:
            resp = api_client.excluir_cliente(c["id"])
            if resp.status_code == 204:
                st.success(f"Cliente **{c['nome']}** excluído.")
                st.session_state.pop("editar_cliente_id", None)
                st.rerun()
            else:
                st.error(resp.json().get("detail", "Erro ao excluir"))

        if st.session_state.get("editar_cliente_id") == c["id"]:
            st.markdown("---")
            st.subheader(f"Editando: {c['nome']}")

            with st.form("form_edit_cliente"):
                st.markdown("**Dados Básicos**")
                col1, col2 = st.columns(2)

                with col1:
                    nome_e     = st.text_input("Nome",    value=c["nome"])
                    email_e    = st.text_input("Email",   value=c["email"])
                    telefone_e = st.text_input("Telefone",value=c["telefone"])
                    cidade_e   = st.text_input("Cidade",  value=c["cidade"])

                with col2:
                    uf_idx   = UFS.index(c["uf"]) if c["uf"] in UFS else 0
                    uf_e     = st.selectbox("UF", UFS, index=uf_idx)
                    st_idx   = STATUS_LISTA.index(c["status"]) if c["status"] in STATUS_LISTA else 0
                    status_e = st.selectbox("Status", STATUS_LISTA, index=st_idx)
                    endereco_e = st.text_input("Endereço", value=c.get("endereco") or "")
                    bairro_e   = st.text_input("Bairro",   value=c.get("bairro") or "")

                st.markdown("**Perfil para Análise de Vendas**")
                col3, col4 = st.columns(2)

                conta_atual  = float(c["conta_energia"]) if c.get("conta_energia") else 0.0
                renda_atual  = float(c["renda_mensal"])  if c.get("renda_mensal")  else 0.0

                ti_atual = c.get("tipo_imovel") or "(não informado)"
                ol_atual = c.get("origem_lead") or "(não informado)"
                es_atual = c.get("escolaridade") or "(não informado)"

                ti_opts = ["(não informado)"] + TIPOS_IMOVEL
                ol_opts = ["(não informado)"] + ORIGENS_LEAD
                es_opts = ["(não informado)"] + ESCOLARIDADES

                with col3:
                    conta_e      = st.number_input("Conta de Energia (R$)", min_value=0.0, step=50.0, value=conta_atual)
                    ti_idx       = ti_opts.index(ti_atual) if ti_atual in ti_opts else 0
                    tipo_imovel_e = st.selectbox("Tipo de Imóvel", ti_opts, index=ti_idx)
                    ol_idx       = ol_opts.index(ol_atual) if ol_atual in ol_opts else 0
                    origem_e     = st.selectbox("Como nos conheceu?", ol_opts, index=ol_idx)

                with col4:
                    renda_e      = st.number_input("Renda Mensal (R$)", min_value=0.0, step=500.0, value=renda_atual)
                    es_idx       = es_opts.index(es_atual) if es_atual in es_opts else 0
                    escolar_e    = st.selectbox("Escolaridade", es_opts, index=es_idx)
                    profissao_e  = st.text_input("Profissão", value=c.get("profissao") or "")

                salvar_e = st.form_submit_button("💾 Salvar Alterações", type="primary")

                if salvar_e:
                    payload = {
                        "nome"         : (nome_e or "").strip(),
                        "email"        : (email_e or "").strip(),
                        "telefone"     : (telefone_e or "").strip(),
                        "cidade"       : (cidade_e or "").strip(),
                        "uf"           : uf_e,
                        "status"       : status_e,
                        "endereco"     : endereco_e.strip() or None,
                        "bairro"       : bairro_e.strip() or None,
                        "conta_energia": conta_e if conta_e > 0 else None,
                        "tipo_imovel"  : None if tipo_imovel_e == "(não informado)" else tipo_imovel_e,
                        "origem_lead"  : None if origem_e == "(não informado)" else origem_e,
                        "renda_mensal" : renda_e if renda_e > 0 else None,
                        "escolaridade" : None if escolar_e == "(não informado)" else escolar_e,
                        "profissao"    : profissao_e.strip() or None,
                    }
                    resp = api_client.atualizar_cliente(c["id"], payload)
                    if resp.status_code == 200:
                        st.success("✅ Cliente atualizado!")
                        st.session_state.pop("editar_cliente_id", None)
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail", "Erro ao atualizar"))
