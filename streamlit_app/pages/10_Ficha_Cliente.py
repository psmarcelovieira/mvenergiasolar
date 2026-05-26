import streamlit as st
import api_client

st.set_page_config(page_title="Ficha do Cliente", layout="wide")
from auth import verificar_auth, rodape_usuario
verificar_auth()
rodape_usuario()

st.title("📋 Ficha do Cliente")

clientes = api_client.listar_clientes()
if not clientes:
    st.info("Nenhum cliente cadastrado.")
    st.stop()

op = {f"[#{c['id']}] {c['nome']}": c for c in clientes}
selecionado = st.selectbox("Selecione o cliente", list(op.keys()))
c = op[selecionado]

# ── CABEÇALHO ─────────────────────────────────────────────────────────────────
st.markdown("---")
col_h1, col_h2, col_h3, col_h4 = st.columns(4)
col_h1.metric("Status",    c["status"])
col_h2.metric("Tipo",      c["tipo_pessoa"])
col_h3.metric("Origem",    c.get("origem_lead") or "—")
col_h4.metric("Imóvel",    c.get("tipo_imovel") or "—")

col_c1, col_c2, col_c3, col_c4 = st.columns(4)
col_c1.markdown(f"📞 **{c.get('telefone') or '—'}**")
col_c2.markdown(f"📧 {c.get('email') or '—'}")
col_c3.markdown(f"🏙️ {(c.get('cidade') or '')} {(c.get('uf') or '')}")
col_c4.markdown(f"📍 {c.get('bairro') or '—'}")

if c.get("telefone"):
    digits = "".join(filter(str.isdigit, c["telefone"]))
    nome_enc = c["nome"].split()[0]
    wapp_url = f"https://wa.me/55{digits}?text=Ol%C3%A1%20{nome_enc}%2C%20tudo%20bem%3F"
    st.link_button("📱 Abrir WhatsApp", wapp_url)

# ── PERFIL ────────────────────────────────────────────────────────────────────
tem_perfil = any(c.get(f) for f in ["conta_energia","renda_mensal","escolaridade","profissao"])
if tem_perfil:
    st.markdown("---")
    st.subheader("Perfil")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Conta de Energia",
              f"R$ {float(c['conta_energia']):,.2f}" if c.get("conta_energia") else "—")
    p2.metric("Renda Mensal",
              f"R$ {float(c['renda_mensal']):,.2f}" if c.get("renda_mensal") else "—")
    p3.metric("Escolaridade", c.get("escolaridade") or "—")
    p4.metric("Profissão",    c.get("profissao") or "—")

# ── HISTÓRICO ─────────────────────────────────────────────────────────────────
st.markdown("---")
tab_vendas, tab_os, tab_proj = st.tabs(["🛒 Vendas", "🔧 Ordens de Serviço", "📡 Projetos de Homologação"])

with tab_vendas:
    vendas_cli = [v for v in api_client.listar_vendas() if v["cliente_id"] == c["id"]]
    if not vendas_cli:
        st.info("Nenhuma venda registrada para este cliente.")
    else:
        total = sum(v["valor_final"] for v in vendas_cli)
        st.metric("Total em vendas", f"R$ {total:,.2f}", delta=f"{len(vendas_cli)} venda(s)")
        st.markdown("")
        STATUS_ICONE = {
            "Orçamento":"🟡","Negociação":"🟠","Aprovado":"🟢",
            "Em Andamento":"🔵","Concluído":"⚫","Cancelado":"🔴",
        }
        cab = st.columns([1, 2, 2, 2, 2])
        for col, t in zip(cab, ["#", "Status", "Valor Final", "Forma Pag.", "Data"]):
            col.markdown(f"**{t}**")
        st.divider()
        for v in vendas_cli:
            c1, c2, c3, c4, c5 = st.columns([1, 2, 2, 2, 2])
            c1.write(f"#{v['id']}")
            c2.write(f"{STATUS_ICONE.get(v['status_venda'],'')} {v['status_venda']}")
            c3.write(f"R$ {v['valor_final']:,.2f}")
            c4.write(v.get("forma_pagamento") or "—")
            c5.write(v["data_orcamento"])

with tab_os:
    os_cli = [o for o in api_client.listar_ordens_servico() if o["cliente_id"] == c["id"]]
    if not os_cli:
        st.info("Nenhuma ordem de serviço para este cliente.")
    else:
        STATUS_OS = {"Aberta":"🟡","Em Andamento":"🔵","Concluída":"🟢","Cancelada":"🔴"}
        cab = st.columns([1, 2, 2, 2, 2])
        for col, t in zip(cab, ["OS", "Tipo", "Status", "Custo", "Abertura"]):
            col.markdown(f"**{t}**")
        st.divider()
        for o in os_cli:
            c1, c2, c3, c4, c5 = st.columns([1, 2, 2, 2, 2])
            c1.write(o["id_os"])
            c2.write(o["tipo_servico"])
            c3.write(f"{STATUS_OS.get(o['status_os'],'')} {o['status_os']}")
            c4.write(f"R$ {float(o['custo_total']):,.2f}" if o.get("custo_total") else "—")
            c5.write(o["data_abertura"])

with tab_proj:
    proj_cli = [p for p in api_client.listar_projetos() if p["cliente_id"] == c["id"]]
    if not proj_cli:
        st.info("Nenhum projeto de homologação para este cliente.")
    else:
        STATUS_P = {"Em Análise":"🟡","Aprovado":"🟢","Aprovado c/ Obras":"🔵","Falta TRT":"🟠","Cancelado":"🔴"}
        cab = st.columns([2, 2, 2, 2])
        for col, t in zip(cab, ["UC", "Status", "Entrada", "Resultado"]):
            col.markdown(f"**{t}**")
        st.divider()
        for p in proj_cli:
            c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
            c1.write(p.get("uc") or "—")
            c2.write(f"{STATUS_P.get(p['status_projeto'],'')} {p['status_projeto']}")
            c3.write(p.get("data_entrada") or "—")
            c4.write(p.get("data_resultado") or "—")
