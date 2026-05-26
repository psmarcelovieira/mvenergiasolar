import streamlit as st
import pandas as pd
from datetime import date, timedelta
import api_client

st.set_page_config(page_title="Projetos de Homologação", layout="wide")
from auth import verificar_auth, rodape_usuario
verificar_auth()
rodape_usuario()
st.title("📋 Projetos de Homologação")

STATUS_ICONE = {
    "Em Análise"       : "🟡",
    "Aprovado"         : "🟢",
    "Aprovado c/ Obras": "🔵",
    "Falta TRT"        : "🟠",
    "Cancelado"        : "🔴",
}
VISTORIA_ICONE = {
    "Não Solicitado": "⬜",
    "Solicitado"    : "🟡",
    "Realizado"     : "✅",
}
STATUS_LISTA  = ["Em Análise", "Aprovado", "Aprovado c/ Obras", "Falta TRT", "Cancelado"]
VISTORIA_LIST = ["Não Solicitado", "Solicitado", "Realizado"]

tab_lista, tab_novo, tab_edit = st.tabs(["📊 Lista", "➕ Novo Projeto", "✏️ Editar / Excluir"])

clientes     = api_client.listar_clientes()
map_clientes = {c["id"]: c["nome"] for c in clientes}
op_clientes  = {c["nome"]: c["id"] for c in clientes}

# ── LISTA ──────────────────────────────────────────────────────────────────────
with tab_lista:
    col_f1, col_f2, col_f3 = st.columns(3)
    busca_proj      = col_f1.text_input("🔍 Buscar cliente / UC", placeholder="Nome ou UC...")
    filtro_status   = col_f2.selectbox("Status", ["Todos"] + STATUS_LISTA)
    filtro_vistoria = col_f3.selectbox("Vistoria", ["Todos"] + VISTORIA_LIST)

    projetos = api_client.listar_projetos()

    if busca_proj:
        t = busca_proj.lower()
        projetos = [p for p in projetos
                    if t in map_clientes.get(p["cliente_id"], "").lower()
                    or t in (p.get("uc") or "").lower()]
    if filtro_status != "Todos":
        projetos = [p for p in projetos if p["status_projeto"] == filtro_status]
    if filtro_vistoria != "Todos":
        projetos = [p for p in projetos if p["status_vistoria"] == filtro_vistoria]

    hoje = date.today()
    atrasados = [p for p in projetos
                 if p.get("data_resultado") and date.fromisoformat(p["data_resultado"]) < hoje
                 and p["status_projeto"] not in ("Aprovado", "Cancelado")]
    if atrasados:
        st.warning(f"⚠️ {len(atrasados)} projeto(s) com prazo vencido.")

    if not projetos:
        st.info("Nenhum projeto encontrado.")
    else:
        cab = st.columns([3, 2, 2, 2, 2, 2])
        for col, titulo in zip(cab, ["Cliente", "UC", "Entrada", "Resultado", "Status", "Vistoria"]):
            col.markdown(f"**{titulo}**")
        st.divider()

        for p in projetos:
            nome    = map_clientes.get(p["cliente_id"], f"#{p['cliente_id']}")
            status  = p["status_projeto"]
            vistoria = p["status_vistoria"]

            dr = p.get("data_resultado")
            atrasado = dr and date.fromisoformat(dr) < hoje and status not in ("Aprovado", "Cancelado")

            c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 2, 2, 2, 2])
            c1.write(f"{'🔴 ' if atrasado else ''}{nome}")
            c2.write(p.get("uc") or "—")
            c3.write(p.get("data_entrada") or "—")
            c4.write(dr or "—")
            c5.write(f"{STATUS_ICONE.get(status, '')} {status}")
            c6.write(f"{VISTORIA_ICONE.get(vistoria, '')} {vistoria}")

# ── NOVO PROJETO ───────────────────────────────────────────────────────────────
with tab_novo:
    if not clientes:
        st.warning("Cadastre pelo menos um cliente antes de criar um projeto.")
    else:
        with st.form("form_projeto"):
            col1, col2 = st.columns(2)

            with col1:
                cliente_sel    = st.selectbox("Cliente *", list(op_clientes.keys()))
                uc             = st.text_input("Unidade Consumidora (UC)")
                protocolo      = st.text_input("Protocolo")
                status_sel     = st.selectbox("Status", STATUS_LISTA)

            with col2:
                data_entrada   = st.date_input("Data de Entrada", value=date.today())
                data_resultado = st.date_input("Data do Resultado",
                                               value=date.today() + timedelta(days=15))
                vistoria_sel   = st.selectbox("Status da Vistoria", VISTORIA_LIST)
                kwp            = st.number_input("kWp do Sistema", min_value=0.0, step=0.1)
                inversor       = st.text_input("Inversor")

            obs = st.text_area("Observações")
            salvar = st.form_submit_button("💾 Criar Projeto", type="primary")

            if salvar:
                payload = {
                    "cliente_id"     : op_clientes[cliente_sel],
                    "uc"             : uc.strip() or None,
                    "data_entrada"   : str(data_entrada),
                    "data_resultado" : str(data_resultado),
                    "protocolo"      : protocolo.strip() or None,
                    "status_projeto" : status_sel,
                    "status_vistoria": vistoria_sel,
                    "kwp"            : kwp if kwp > 0 else None,
                    "inversor"       : inversor.strip() or None,
                    "observacoes"    : obs.strip() or None,
                }
                resp = api_client.criar_projeto(payload)
                if resp.status_code == 201:
                    st.success("✅ Projeto criado!")
                    st.rerun()
                else:
                    st.error(resp.json().get("detail", "Erro ao criar projeto"))

# ── EDITAR / EXCLUIR ───────────────────────────────────────────────────────────
with tab_edit:
    projetos_edit = api_client.listar_projetos()
    if not projetos_edit:
        st.info("Nenhum projeto cadastrado.")
    else:
        op_proj = {
            f"[#{p['id']}] {map_clientes.get(p['cliente_id'], '?')} — UC: {p.get('uc') or 'sem UC'}": p
            for p in projetos_edit
        }
        selecionado = st.selectbox("Selecione o projeto", list(op_proj.keys()))
        p = op_proj[selecionado]

        col_b1, col_b2, _ = st.columns([1, 1, 4])
        if col_b1.button("✏️ Editar",  key="btn_edit_proj"):
            st.session_state["editar_projeto_id"] = p["id"]
        if col_b2.button("🗑️ Excluir", key="btn_del_proj"):
            resp = api_client.excluir_projeto(p["id"])
            if resp.status_code == 204:
                st.success("Projeto excluído.")
                st.session_state.pop("editar_projeto_id", None)
                st.rerun()
            else:
                st.error(resp.json().get("detail", "Erro ao excluir"))

        if st.session_state.get("editar_projeto_id") == p["id"]:
            st.markdown("---")
            cliente_nome = map_clientes.get(p["cliente_id"], "?")
            st.subheader(f"Editando: {cliente_nome}")

            with st.form("form_edit_proj"):
                col1, col2 = st.columns(2)

                de = p.get("data_entrada")
                dr = p.get("data_resultado")
                st_idx = STATUS_LISTA.index(p["status_projeto"]) if p["status_projeto"] in STATUS_LISTA else 0
                vi_idx = VISTORIA_LIST.index(p["status_vistoria"]) if p["status_vistoria"] in VISTORIA_LIST else 0

                with col1:
                    uc_e        = st.text_input("UC", value=p.get("uc") or "")
                    protocolo_e = st.text_input("Protocolo", value=p.get("protocolo") or "")
                    status_e    = st.selectbox("Status", STATUS_LISTA, index=st_idx)
                    vistoria_e  = st.selectbox("Vistoria", VISTORIA_LIST, index=vi_idx)

                with col2:
                    entrada_e   = st.date_input("Data de Entrada",
                                                value=date.fromisoformat(de) if de else date.today())
                    result_e    = st.date_input("Data do Resultado",
                                                value=date.fromisoformat(dr) if dr else date.today())
                    kwp_e       = st.number_input("kWp", min_value=0.0, step=0.1,
                                                  value=float(p.get("kwp") or 0))
                    inversor_e  = st.text_input("Inversor", value=p.get("inversor") or "")

                obs_e = st.text_area("Observações", value=p.get("observacoes") or "")
                salvar_e = st.form_submit_button("💾 Salvar", type="primary")

                if salvar_e:
                    payload = {
                        "uc"             : uc_e.strip() or None,
                        "protocolo"      : protocolo_e.strip() or None,
                        "status_projeto" : status_e,
                        "status_vistoria": vistoria_e,
                        "data_entrada"   : str(entrada_e),
                        "data_resultado" : str(result_e),
                        "kwp"            : kwp_e if kwp_e > 0 else None,
                        "inversor"       : inversor_e.strip() or None,
                        "observacoes"    : obs_e.strip() or None,
                    }
                    resp = api_client.atualizar_projeto(p["id"], payload)
                    if resp.status_code == 200:
                        st.success("✅ Projeto atualizado!")
                        st.session_state.pop("editar_projeto_id", None)
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail", "Erro ao atualizar"))
