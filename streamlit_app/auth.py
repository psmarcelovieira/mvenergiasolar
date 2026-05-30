import streamlit as st
from datetime import datetime


def verificar_auth():
    """Redireciona para login se não estiver autenticado."""
    if "usuario" not in st.session_state:
        st.warning("Faça login para acessar o sistema.")
        st.rerun()
    return st.session_state["usuario"]


def verificar_admin():
    """Bloqueia acesso se o perfil não for Admin."""
    usuario = verificar_auth()
    if usuario["perfil"] != "Admin":
        st.error("⛔ Acesso restrito a administradores.")
        st.stop()
    return usuario


def _formatar_ultimo_login(iso_str: str | None) -> str:
    if not iso_str:
        return "Primeiro acesso"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "—"


def rodape_usuario():
    """Exibe usuário logado, perfil, último acesso e botão de logout na sidebar."""
    usuario = st.session_state.get("usuario")
    if not usuario:
        return
    with st.sidebar:
        st.markdown("---")
        perfil_icone = "👑" if usuario["perfil"] == "Admin" else "👤"
        st.markdown(
            f"**{perfil_icone} {usuario['nome']}**  \n"
            f"<small>🔑 {usuario['perfil']}</small>  \n"
            f"<small>🕐 Último acesso: {_formatar_ultimo_login(usuario.get('ultimo_login'))}</small>",
            unsafe_allow_html=True,
        )
        if st.button("Sair", key="btn_logout_sidebar", use_container_width=True):
            del st.session_state["usuario"]
            st.rerun()
