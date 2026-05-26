import streamlit as st
from datetime import date
import api_client

st.set_page_config(page_title="Ordens de Serviço", layout="wide")
from auth import verificar_auth, rodape_usuario
verificar_auth()
rodape_usuario()
st.title("🔧 Ordens de Serviço")

STATUS_ICONE  = {"Aberta": "🟡", "Em Andamento": "🔵", "Concluída": "🟢", "Cancelada": "🔴"}
TIPOS_SERVICO = ["Preventiva", "Corretiva", "Limpeza", "Inspeção", "Garantia", "Outros"]
STATUS_LISTA  = ["Aberta", "Em Andamento", "Concluída", "Cancelada"]
FORMAS_PAG    = ["PIX", "Boleto", "Dinheiro", "Cartão", "Financiamento"]

clientes      = api_client.listar_clientes()
colaboradores = api_client.listar_colaboradores()
map_clientes  = {c["id"]: c["nome"] for c in clientes}
op_clientes   = {c["nome"]: c["id"] for c in clientes}
op_tecnicos   = {"(sem técnico)": None}
op_tecnicos.update({c["nome"]: c["id_colaborador"] for c in colaboradores})
map_tecnicos  = {c["id_colaborador"]: c["nome"] for c in colaboradores}

tab_lista, tab_nova, tab_edit = st.tabs(["📋 Lista", "➕ Nova OS", "✏️ Editar / Excluir"])

# ── LISTA ──────────────────────────────────────────────────────────────────────
with tab_lista:
    col_f1, col_f2 = st.columns(2)
    filtro_status = col_f1.selectbox("Status", ["Todos"] + STATUS_LISTA)
    filtro_tipo   = col_f2.selectbox("Tipo",   ["Todos"] + TIPOS_SERVICO)

    ordens = api_client.listar_ordens_servico()

    if filtro_status != "Todos":
        ordens = [o for o in ordens if o["status_os"] == filtro_status]
    if filtro_tipo != "Todos":
        ordens = [o for o in ordens if o["tipo_servico"] == filtro_tipo]

    todas  = api_client.listar_ordens_servico()
    abertas = sum(1 for o in todas if o["status_os"] in ("Aberta", "Em Andamento"))
    if abertas:
        st.info(f"🔧 {abertas} ordem(ns) em aberto.")

    if not ordens:
        st.info("Nenhuma ordem de serviço encontrada.")
    else:
        cab = st.columns([1, 3, 2, 2, 2, 2, 2])
        for col, titulo in zip(cab, ["OS", "Cliente", "Tipo", "Técnico", "Abertura", "Agendamento", "Status"]):
            col.markdown(f"**{titulo}**")
        st.divider()

        for o in ordens:
            c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 3, 2, 2, 2, 2, 2])
            c1.write(o["id_os"])
            c2.write(map_clientes.get(o["cliente_id"], f"#{o['cliente_id']}"))
            c3.write(o["tipo_servico"])
            c4.write(map_tecnicos.get(o.get("id_tecnico"), "—"))
            c5.write(o["data_abertura"])
            c6.write(o.get("data_agendamento") or "—")
            c7.write(f"{STATUS_ICONE.get(o['status_os'], '')} {o['status_os']}")

# ── NOVA OS ────────────────────────────────────────────────────────────────────
with tab_nova:
    if not clientes:
        st.warning("Cadastre pelo menos um cliente antes de abrir uma OS.")
    else:
        with st.form("form_os"):
            col1, col2 = st.columns(2)

            with col1:
                cliente_sel  = st.selectbox("Cliente *", list(op_clientes.keys()))
                tipo_sel     = st.selectbox("Tipo de Serviço *", TIPOS_SERVICO)
                tecnico_sel  = st.selectbox("Técnico Responsável", list(op_tecnicos.keys()))
                data_aber    = st.date_input("Data de Abertura", value=date.today())
                data_agend   = st.date_input("Data de Agendamento", value=None)

            with col2:
                forma_pag    = st.selectbox("Forma de Pagamento", FORMAS_PAG)
                custo        = st.number_input("Custo do Serviço (R$)", min_value=0.0, step=50.0,
                                               help="OS do tipo Garantia não gera lançamento financeiro")
                descricao    = st.text_area("Descrição do Serviço *", height=100)
                observacoes  = st.text_area("Observações", height=68)

            salvar = st.form_submit_button("💾 Abrir OS", type="primary")

            if salvar:
                if not descricao.strip():
                    st.error("Descrição é obrigatória.")
                else:
                    payload = {
                        "cliente_id"      : op_clientes[cliente_sel],
                        "id_tecnico"      : op_tecnicos[tecnico_sel],
                        "tipo_servico"    : tipo_sel,
                        "descricao"       : descricao.strip(),
                        "data_abertura"   : str(data_aber),
                        "data_agendamento": str(data_agend) if data_agend else None,
                        "forma_pagamento" : forma_pag,
                        "custo_total"     : custo if custo > 0 else None,
                        "observacoes"     : observacoes.strip() or None,
                    }
                    resp = api_client.criar_os(payload)
                    if resp.status_code == 201:
                        st.success(f"✅ {resp.json()['id_os']} aberta!")
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail", "Erro ao criar OS"))

# ── EDITAR / EXCLUIR ───────────────────────────────────────────────────────────
with tab_edit:
    ordens_edit = api_client.listar_ordens_servico()
    if not ordens_edit:
        st.info("Nenhuma OS cadastrada.")
    else:
        op_os = {
            f"[{o['id_os']}] {map_clientes.get(o['cliente_id'], '?')} — {o['tipo_servico']} ({o['status_os']})": o
            for o in ordens_edit
        }
        selecionado = st.selectbox("Selecione a OS", list(op_os.keys()))
        o = op_os[selecionado]

        col_b1, col_b2, _ = st.columns([1, 1, 4])
        if col_b1.button("✏️ Editar",  key="btn_edit_os"):
            st.session_state["editar_os_id"] = o["id_os"]
        if col_b2.button("🗑️ Excluir", key="btn_del_os"):
            resp = api_client.excluir_os(o["id_os"])
            if resp.status_code == 204:
                st.success("OS excluída.")
                st.session_state.pop("editar_os_id", None)
                st.rerun()
            else:
                st.error(resp.json().get("detail", "Erro ao excluir"))

        if st.session_state.get("editar_os_id") == o["id_os"]:
            st.markdown("---")
            st.subheader(f"Editando {o['id_os']} — {map_clientes.get(o['cliente_id'], '?')}")

            if o["status_os"] == "Concluída":
                st.warning("⚠️ Esta OS já está concluída. Alterar o status irá reabri-la sem estornar o lançamento financeiro.")

            with st.form("form_edit_os"):
                col1, col2 = st.columns(2)

                ti_idx  = TIPOS_SERVICO.index(o["tipo_servico"]) if o["tipo_servico"] in TIPOS_SERVICO else 0
                st_idx  = STATUS_LISTA.index(o["status_os"])     if o["status_os"]     in STATUS_LISTA  else 0
                fp_idx  = FORMAS_PAG.index(o["forma_pagamento"]) if o.get("forma_pagamento") in FORMAS_PAG else 0
                tec_key = next((k for k, v in op_tecnicos.items() if v == o.get("id_tecnico")), "(sem técnico)")
                tec_idx = list(op_tecnicos.keys()).index(tec_key)

                da = o.get("data_agendamento")
                dc = o.get("data_conclusao")

                with col1:
                    tipo_e    = st.selectbox("Tipo",   TIPOS_SERVICO, index=ti_idx)
                    status_e  = st.selectbox("Status", STATUS_LISTA,  index=st_idx)
                    tecnico_e = st.selectbox("Técnico", list(op_tecnicos.keys()), index=tec_idx)
                    agend_e   = st.date_input("Agendamento",
                                              value=date.fromisoformat(da) if da else None)

                with col2:
                    forma_e  = st.selectbox("Forma de Pagamento", FORMAS_PAG, index=fp_idx)
                    concl_e  = st.date_input("Conclusão",
                                             value=date.fromisoformat(dc) if dc else None)
                    custo_e  = st.number_input("Custo (R$)", min_value=0.0, step=50.0,
                                               value=float(o.get("custo_total") or 0))
                    desc_e   = st.text_area("Descrição",   value=o.get("descricao") or "",   height=80)
                    obs_e    = st.text_area("Observações", value=o.get("observacoes") or "", height=60)

                salvar_e = st.form_submit_button("💾 Salvar", type="primary")

                if salvar_e:
                    payload = {
                        "tipo_servico"    : tipo_e,
                        "status_os"       : status_e,
                        "id_tecnico"      : op_tecnicos[tecnico_e],
                        "data_agendamento": str(agend_e) if agend_e else None,
                        "data_conclusao"  : str(concl_e) if concl_e else None,
                        "forma_pagamento" : forma_e,
                        "custo_total"     : custo_e if custo_e > 0 else None,
                        "descricao"       : desc_e.strip(),
                        "observacoes"     : obs_e.strip() or None,
                    }
                    resp = api_client.atualizar_os(o["id_os"], payload)
                    if resp.status_code == 200:
                        concluiu = status_e == "Concluída" and o["status_os"] != "Concluída"
                        msg = "✅ OS concluída! Lançamento financeiro gerado." if concluiu else "✅ OS atualizada!"
                        st.success(msg)
                        st.session_state.pop("editar_os_id", None)
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail", "Erro ao atualizar"))
