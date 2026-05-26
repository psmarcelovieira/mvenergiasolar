import streamlit as st


def verificar_auth():
    """Redireciona para login se não estiver autenticado."""
    if "usuario" not in st.session_state:
        st.warning("Faça login para acessar o sistema.")
        st.switch_page("app.py")
        st.stop()
    return st.session_state["usuario"]


def verificar_admin():
    """Bloqueia acesso se o perfil for Vendedor."""
    usuario = verificar_auth()
    if usuario["perfil"] != "Admin":
        st.error("⛔ Acesso restrito a administradores.")
        st.stop()
    return usuario


def rodape_usuario():
    """Exibe usuário logado e botão de logout na sidebar."""
    usuario = st.session_state.get("usuario")
    if not usuario:
        return
    with st.sidebar:
        st.markdown("---")
        st.caption(f"👤 {usuario['nome']}  \n🔑 {usuario['perfil']}")
        if st.button("Sair", key="btn_logout_sidebar"):
            del st.session_state["usuario"]
            st.switch_page("app.py")
