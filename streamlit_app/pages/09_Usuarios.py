import streamlit as st
import api_client

st.set_page_config(page_title="Usuários", layout="wide")
from auth import verificar_admin, rodape_usuario
verificar_admin()
rodape_usuario()

st.title("🔐 Usuários do Sistema")

PERFIS = ["Admin", "Vendedor"]

tab_lista, tab_novo, tab_edit = st.tabs(["📋 Lista", "➕ Novo Usuário", "✏️ Editar / Excluir"])

# ── LISTA ──────────────────────────────────────────────────────────────────────
with tab_lista:
    usuarios = api_client.listar_usuarios()
    if not usuarios:
        st.info("Nenhum usuário cadastrado.")
    else:
        cab = st.columns([1, 3, 3, 2])
        for col, titulo in zip(cab, ["ID", "Nome", "Login", "Perfil"]):
            col.markdown(f"**{titulo}**")
        st.divider()
        for u in usuarios:
            c1, c2, c3, c4 = st.columns([1, 3, 3, 2])
            c1.write(u["id"])
            c2.write(u["nome"])
            c3.write(u["login"])
            c4.write(u["perfil"])

# ── NOVO USUÁRIO ───────────────────────────────────────────────────────────────
with tab_novo:
    with st.form("form_novo_usuario"):
        col1, col2 = st.columns(2)
        with col1:
            nome_n  = st.text_input("Nome *")
            login_n = st.text_input("Login *")
        with col2:
            senha_n  = st.text_input("Senha *", type="password")
            perfil_n = st.selectbox("Perfil *", PERFIS)

        salvar = st.form_submit_button("💾 Criar Usuário", type="primary")

        if salvar:
            if not nome_n or not login_n or not senha_n:
                st.error("Nome, login e senha são obrigatórios.")
            else:
                resp = api_client.criar_usuario({
                    "nome":   nome_n.strip(),
                    "login":  login_n.strip(),
                    "senha":  senha_n,
                    "perfil": perfil_n,
                })
                if resp.status_code == 201:
                    st.success(f"✅ Usuário **{nome_n}** criado!")
                    st.rerun()
                elif resp.status_code == 409:
                    st.error("Login já cadastrado.")
                else:
                    st.error(resp.json().get("detail", "Erro ao criar usuário"))

# ── EDITAR / EXCLUIR ───────────────────────────────────────────────────────────
with tab_edit:
    usuarios_edit = api_client.listar_usuarios()
    if not usuarios_edit:
        st.info("Nenhum usuário cadastrado.")
    else:
        op = {f"[{u['id']}] {u['nome']} ({u['login']})": u for u in usuarios_edit}
        selecionado = st.selectbox("Selecione o usuário", list(op.keys()))
        u = op[selecionado]

        col_b1, col_b2, _ = st.columns([1, 1, 4])
        if col_b1.button("✏️ Editar",  key="btn_edit_usr"):
            st.session_state["editar_usr_id"] = u["id"]
        if col_b2.button("🗑️ Excluir", key="btn_del_usr"):
            resp = api_client.excluir_usuario(u["id"])
            if resp.status_code == 204:
                st.success("Usuário excluído.")
                st.session_state.pop("editar_usr_id", None)
                st.rerun()
            else:
                st.error(resp.json().get("detail", "Erro ao excluir"))

        if st.session_state.get("editar_usr_id") == u["id"]:
            st.markdown("---")
            st.subheader(f"Editando: {u['nome']}")

            with st.form("form_edit_usuario"):
                col1, col2 = st.columns(2)
                with col1:
                    nome_e  = st.text_input("Nome",  value=u["nome"])
                    login_e = st.text_input("Login", value=u["login"])
                with col2:
                    senha_e  = st.text_input("Nova Senha (deixe em branco para manter)", type="password")
                    perf_idx = PERFIS.index(u["perfil"]) if u["perfil"] in PERFIS else 0
                    perfil_e = st.selectbox("Perfil", PERFIS, index=perf_idx)

                salvar_e = st.form_submit_button("💾 Salvar", type="primary")

                if salvar_e:
                    payload: dict = {
                        "nome":   nome_e.strip(),
                        "login":  login_e.strip(),
                        "perfil": perfil_e,
                    }
                    if senha_e:
                        payload["senha"] = senha_e

                    resp = api_client.atualizar_usuario(u["id"], payload)
                    if resp.status_code == 200:
                        usuario_logado = st.session_state.get("usuario", {})
                        if usuario_logado.get("id") == u["id"]:
                            st.session_state["usuario"] = resp.json()
                        st.success("✅ Usuário atualizado!")
                        st.session_state.pop("editar_usr_id", None)
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail", "Erro ao atualizar"))
