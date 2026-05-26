import streamlit as st
import pandas as pd
from datetime import date, timedelta
import api_client

st.set_page_config(page_title="Prospecção", layout="wide")
from auth import verificar_auth, rodape_usuario
verificar_auth()
rodape_usuario()

st.title("🎯 Painel de Prospecção")

clientes = api_client.listar_clientes()
vendas   = api_client.listar_vendas()
ordens   = api_client.listar_ordens_servico()

clientes_com_venda = {v["cliente_id"] for v in vendas}
clientes_com_os    = {o["cliente_id"] for o in ordens}

ORIGENS = ["Todas", "Indicação", "Google", "Instagram", "Facebook", "WhatsApp", "Site", "Evento", "Outros"]
IMOVEIS = ["Todos", "Residencial", "Comercial", "Rural", "Industrial"]
STATUS_C = ["Todos", "Ativo", "Prospecto", "Inativo", "Bloqueado"]


def wapp(tel):
    if not tel:
        return None
    d = "".join(filter(str.isdigit, str(tel)))
    return f"https://wa.me/55{d}" if d else None


def df_com_wapp(lista, cols, renomes):
    df = pd.DataFrame(lista)[cols].copy()
    df["📱"] = pd.DataFrame(lista)["telefone"].apply(wapp)
    df.columns = renomes + ["📱"]
    return df


tab_seg, tab_prospects, tab_manutencao = st.tabs([
    "📊 Segmentação", "🎯 Prospects sem Venda", "🔧 Oportunidades de Manutenção"
])

# ── SEGMENTAÇÃO ────────────────────────────────────────────────────────────────
with tab_seg:
    st.subheader("Distribuição por Origem de Lead")

    origens_vals = [c.get("origem_lead") or "Não informado" for c in clientes]
    df_orig = pd.Series(origens_vals).value_counts().reset_index()
    df_orig.columns = ["Origem", "Qtd"]

    col_g, col_t = st.columns([3, 1])
    col_g.bar_chart(df_orig.set_index("Origem"))
    col_t.dataframe(df_orig, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.subheader("Filtrar por Perfil")

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    f_origem   = col_f1.selectbox("Origem do Lead", ORIGENS)
    f_imovel   = col_f2.selectbox("Tipo de Imóvel", IMOVEIS)
    conta_min  = col_f3.number_input("Conta de Energia mín. (R$)", min_value=0.0, step=50.0)
    f_status   = col_f4.selectbox("Status", STATUS_C)

    resultado = clientes
    if f_origem != "Todas":
        resultado = [c for c in resultado if c.get("origem_lead") == f_origem]
    if f_imovel != "Todos":
        resultado = [c for c in resultado if c.get("tipo_imovel") == f_imovel]
    if conta_min > 0:
        resultado = [c for c in resultado if float(c.get("conta_energia") or 0) >= conta_min]
    if f_status != "Todos":
        resultado = [c for c in resultado if c.get("status") == f_status]

    st.caption(f"{len(resultado)} cliente(s) neste segmento")

    if resultado:
        df_seg = pd.DataFrame(resultado)
        df_seg["📱"] = df_seg["telefone"].apply(wapp)
        df_seg["conta_energia"] = df_seg["conta_energia"].apply(
            lambda x: f"R$ {float(x):,.2f}" if x else "—"
        )
        colunas = ["nome", "cidade", "telefone", "conta_energia", "origem_lead", "tipo_imovel", "status", "📱"]
        df_show = df_seg[colunas].copy()
        df_show.columns = ["Nome", "Cidade", "Telefone", "Conta Energia", "Origem", "Imóvel", "Status", "📱"]
        st.dataframe(
            df_show,
            use_container_width=True,
            hide_index=True,
            column_config={"📱": st.column_config.LinkColumn("📱 WhatsApp", display_text="Abrir")}
        )

# ── PROSPECTS SEM VENDA ────────────────────────────────────────────────────────
with tab_prospects:
    prospects = [c for c in clientes
                 if c["status"] == "Prospecto" and c["id"] not in clientes_com_venda]

    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Prospects sem nenhuma venda", len(prospects))
    col_m2.metric("Total de prospects",
                  sum(1 for c in clientes if c["status"] == "Prospecto"))

    if prospects:
        df_p = pd.DataFrame(prospects)
        df_p["📱"] = df_p["telefone"].apply(wapp)
        df_p["conta_energia"] = df_p["conta_energia"].apply(
            lambda x: f"R$ {float(x):,.2f}" if x else "—"
        )
        df_show = df_p[["nome","cidade","telefone","conta_energia","origem_lead","📱"]].copy()
        df_show.columns = ["Nome","Cidade","Telefone","Conta Energia","Origem","📱"]
        st.dataframe(
            df_show,
            use_container_width=True,
            hide_index=True,
            column_config={"📱": st.column_config.LinkColumn("📱 WhatsApp", display_text="Abrir")}
        )
    else:
        st.success("✅ Todos os prospects já possuem pelo menos uma venda!")

# ── OPORTUNIDADES DE MANUTENÇÃO ────────────────────────────────────────────────
with tab_manutencao:
    meses = st.slider("Clientes sem OS há mais de X meses", min_value=1, max_value=36, value=6)
    corte = date.today() - timedelta(days=meses * 30)

    # Última OS por cliente
    ultima_os: dict[int, str] = {}
    for o in ordens:
        cid  = o["cliente_id"]
        data = o["data_abertura"]
        if cid not in ultima_os or data > ultima_os[cid]:
            ultima_os[cid] = data

    # Clientes ativos que já compraram mas estão sem OS recente
    sem_manut = []
    for c in clientes:
        if c["status"] != "Ativo" or c["id"] not in clientes_com_venda:
            continue
        ultima = ultima_os.get(c["id"])
        if not ultima or date.fromisoformat(ultima) < corte:
            sem_manut.append({**c, "_ultima_os": ultima or "Nunca"})

    st.metric(f"Clientes sem OS nos últimos {meses} meses", len(sem_manut))

    if sem_manut:
        df_m = pd.DataFrame(sem_manut)
        df_m["📱"] = df_m["telefone"].apply(wapp)
        df_show = df_m[["nome","cidade","telefone","_ultima_os","📱"]].copy()
        df_show.columns = ["Nome","Cidade","Telefone","Última OS","📱"]
        st.dataframe(
            df_show,
            use_container_width=True,
            hide_index=True,
            column_config={"📱": st.column_config.LinkColumn("📱 WhatsApp", display_text="Abrir")}
        )
    else:
        st.success(f"✅ Todos os clientes ativos têm OS nos últimos {meses} meses!")
