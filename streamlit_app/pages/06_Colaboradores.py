import streamlit as st
import api_client

st.title("👥 Colaboradores")

STATUS_ICONE = {"Ativo": "🟢", "Inativo": "⚫"}
CONTRATOS    = ["CLT", "Autônomo", "PJ"]
STATUS_LISTA = ["Ativo", "Inativo"]

tab_lista, tab_novo, tab_edit = st.tabs(["📋 Lista de Colaboradores", "➕ Novo Colaborador", "✏️ Editar / Excluir"])

# ── LISTA ──────────────────────────────────────────────────────────────────────
with tab_lista:
    colaboradores = api_client.listar_colaboradores()
    if not colaboradores:
        st.info("Nenhum colaborador cadastrado ainda.")
    else:
        cab = st.columns([1, 3, 2, 2, 2, 2])
        for col, titulo in zip(cab, ["ID", "Nome", "Cargo", "Contrato", "Comissão", "Status"]):
            col.markdown(f"**{titulo}**")
        st.divider()

        for c in colaboradores:
            status = c["status"]
            c1, c2, c3, c4, c5, c6 = st.columns([1, 3, 2, 2, 2, 2])
            c1.write(c["id_colaborador"])
            c2.write(c["nome"])
            c3.write(c.get("cargo") or "—")
            c4.write(c["tipo_contrato"])
            c5.write(f"{c['percentual_comissao'] * 100:.1f}%")
            c6.write(f"{STATUS_ICONE.get(status, '')} {status}")

# ── NOVO COLABORADOR ───────────────────────────────────────────────────────────
with tab_novo:
    with st.form("form_colaborador"):
        col1, col2 = st.columns(2)

        with col1:
            nome          = st.text_input("Nome *")
            cpf           = st.text_input("CPF *", placeholder="000.000.000-00")
            cargo         = st.text_input("Cargo")
            tipo_contrato = st.selectbox("Tipo de Contrato *", CONTRATOS)

        with col2:
            comissao_pct  = st.number_input(
                "Comissão (%)", min_value=0.0, max_value=100.0, step=0.5, value=3.0,
                help="Ex: 5 = 5% de comissão sobre o valor da venda"
            )
            telefone      = st.text_input("Telefone")
            email         = st.text_input("E-mail")
            data_admissao = st.date_input("Data de Admissão")

        salvar = st.form_submit_button("💾 Cadastrar Colaborador", type="primary")

        if salvar:
            if not nome or not cpf:
                st.error("Nome e CPF são obrigatórios.")
            else:
                payload = {
                    "nome"                : nome.strip(),
                    "cpf"                 : cpf.strip(),
                    "cargo"               : cargo.strip() or None,
                    "tipo_contrato"       : tipo_contrato,
                    "percentual_comissao" : comissao_pct / 100,
                    "telefone"            : telefone.strip() or None,
                    "email"               : email.strip() or None,
                    "data_admissao"       : str(data_admissao),
                }
                resp = api_client.criar_colaborador(payload)
                if resp.status_code == 201:
                    st.success(f"✅ Colaborador **{nome}** cadastrado com sucesso!")
                    st.rerun()
                elif resp.status_code == 409:
                    st.error("CPF já cadastrado.")
                else:
                    st.error(f"Erro: {resp.json().get('detail', 'Erro desconhecido')}")

# ── EDITAR / EXCLUIR COLABORADOR ───────────────────────────────────────────────
with tab_edit:
    colaboradores_edit = api_client.listar_colaboradores()
    if not colaboradores_edit:
        st.info("Nenhum colaborador cadastrado.")
    else:
        op = {f"[{c['id_colaborador']}] {c['nome']}": c for c in colaboradores_edit}
        selecionado = st.selectbox("Selecione o colaborador", list(op.keys()))
        c = op[selecionado]

        col_btn1, col_btn2, _ = st.columns([1, 1, 4])
        acao_editar  = col_btn1.button("✏️ Editar",  key="btn_edit_col")
        acao_excluir = col_btn2.button("🗑️ Excluir", key="btn_del_col")

        if acao_editar:
            st.session_state["editar_colab_id"] = c["id_colaborador"]

        if acao_excluir:
            resp = api_client.excluir_colaborador(c["id_colaborador"])
            if resp.status_code == 204:
                st.success(f"Colaborador **{c['nome']}** excluído.")
                st.session_state.pop("editar_colab_id", None)
                st.rerun()
            else:
                st.error(resp.json().get("detail", "Erro ao excluir"))

        if st.session_state.get("editar_colab_id") == c["id_colaborador"]:
            st.markdown("---")
            st.subheader(f"Editando: {c['nome']}")

            with st.form("form_edit_colab"):
                col1, col2 = st.columns(2)

                with col1:
                    nome_e    = st.text_input("Nome",  value=c["nome"])
                    cargo_e   = st.text_input("Cargo", value=c.get("cargo") or "")
                    cont_idx  = CONTRATOS.index(c["tipo_contrato"]) if c["tipo_contrato"] in CONTRATOS else 0
                    contrato_e = st.selectbox("Tipo de Contrato", CONTRATOS, index=cont_idx)
                    stat_idx  = STATUS_LISTA.index(c["status"]) if c["status"] in STATUS_LISTA else 0
                    status_e  = st.selectbox("Status", STATUS_LISTA, index=stat_idx)

                with col2:
                    comissao_e = st.number_input(
                        "Comissão (%)", min_value=0.0, max_value=100.0, step=0.5,
                        value=round(float(c["percentual_comissao"]) * 100, 2),
                        help="Ex: 5 = 5%"
                    )
                    telefone_e = st.text_input("Telefone", value=c.get("telefone") or "")
                    email_e    = st.text_input("E-mail",   value=c.get("email") or "")

                salvar_e = st.form_submit_button("💾 Salvar Alterações", type="primary")

                if salvar_e:
                    payload = {
                        "nome"                : nome_e.strip(),
                        "cargo"               : cargo_e.strip() or None,
                        "tipo_contrato"       : contrato_e,
                        "percentual_comissao" : comissao_e / 100,
                        "telefone"            : telefone_e.strip() or None,
                        "email"               : email_e.strip() or None,
                        "status"              : status_e,
                    }
                    resp = api_client.atualizar_colaborador(c["id_colaborador"], payload)
                    if resp.status_code == 200:
                        st.success("✅ Colaborador atualizado!")
                        st.session_state.pop("editar_colab_id", None)
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail", "Erro ao atualizar"))
