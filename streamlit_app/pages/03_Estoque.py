import streamlit as st
import pandas as pd
import api_client

st.title("📦 Estoque")

tab_saldo, tab_mov, tab_novo, tab_edit = st.tabs(["📊 Saldo por Produto", "📝 Registrar Movimentação", "➕ Novo Produto", "✏️ Editar / Excluir"])

TIPOS_MOV = ["Entrada", "Saída", "Ajuste+", "Ajuste-"]

# ── SALDO ──────────────────────────────────────────────────────────────────────
with tab_saldo:
    produtos = api_client.listar_produtos()
    if not produtos:
        st.info("Nenhum produto cadastrado.")
    else:
        CATS_F = ["Todas","Painel","Inversor","Cabo","Estrutura","Acessório","Serviço"]
        col_f1, col_f2, col_f3 = st.columns([3, 2, 2])
        busca_prod  = col_f1.text_input("🔍 Buscar produto", placeholder="Nome ou código...")
        filtro_cat  = col_f2.selectbox("Categoria", CATS_F, key="f_cat_est")
        so_alertas  = col_f3.checkbox("⚠️ Só itens em alerta")

        resultado = produtos
        if busca_prod:
            t = busca_prod.lower()
            resultado = [p for p in resultado
                         if t in p["nome"].lower() or t in p["codigo"].lower()]
        if filtro_cat != "Todas":
            resultado = [p for p in resultado if p["categoria"] == filtro_cat]
        if so_alertas:
            resultado = [p for p in resultado if p["alerta_estoque"]]

        st.caption(f"{len(resultado)} produto(s) encontrado(s)")

        if resultado:
            df = pd.DataFrame(resultado)[[
                "codigo","nome","categoria","qtd_estoque",
                "qtd_minima","alerta_estoque","custo_unitario","preco_venda","margem_pct"
            ]]
            df.columns = [
                "Código","Nome","Categoria","Estoque",
                "Mínimo","Alerta","Custo","Preço Venda","Margem %"
            ]
            df["Margem %"] = (df["Margem %"] * 100).round(1).astype(str) + "%"

            def colorir_alerta(row):
                cor = "background-color: #5c1c1c; color: #ffaaaa" if row["Alerta"] else ""
                return [cor] * len(row)

            st.dataframe(
                df.style.apply(colorir_alerta, axis=1),
                use_container_width=True,
                hide_index=True
            )

        alertas = sum(1 for p in produtos if p["alerta_estoque"])
        if alertas:
            st.warning(f"⚠️ {alertas} produto(s) abaixo do estoque mínimo.")
        else:
            st.success("✅ Todos os produtos dentro do estoque mínimo.")

# ── MOVIMENTAÇÃO ───────────────────────────────────────────────────────────────
with tab_mov:
    produtos = api_client.listar_produtos()
    op_produtos = {p["nome"]: p for p in produtos}

    with st.form("form_mov"):
        col1, col2 = st.columns(2)

        with col1:
            tipo_mov     = st.selectbox("Tipo de Movimentação", TIPOS_MOV)
            produto_nome = st.selectbox("Produto", list(op_produtos.keys()))
            responsavel  = st.text_input("Responsável")

        with col2:
            quantidade     = st.number_input("Quantidade", min_value=1, step=1, value=1)
            valor_unitario = st.number_input("Valor Unitário (R$)", min_value=0.0, step=10.0)
            observacoes    = st.text_area("Observações", height=95)

        salvar = st.form_submit_button("Registrar Movimentação", type="primary")

        if salvar:
            prod = op_produtos[produto_nome]
            resp = api_client.registrar_movimentacao({
                "tipo_mov"      : tipo_mov,
                "id_produto"    : prod["id"],
                "quantidade"    : quantidade,
                "valor_unitario": valor_unitario,
                "responsavel"   : responsavel,
                "observacoes"   : observacoes or None,
            })
            if resp.status_code == 201:
                st.success(f"✅ Movimentação registrada — {tipo_mov} de {quantidade} unidade(s) de **{produto_nome}**.")
                st.rerun()
            else:
                st.error(f"Erro: {resp.json().get('detail', 'Erro desconhecido')}")

# ── NOVO PRODUTO ───────────────────────────────────────────────────────────────
with tab_novo:
    CATEGORIAS = ["Painel", "Inversor", "Cabo", "Estrutura", "Acessório", "Serviço"]
    UNIDADES   = ["UN", "M", "KG", "KWP"]

    with st.form("form_produto"):
        col1, col2 = st.columns(2)

        with col1:
            codigo     = st.text_input("Código *", placeholder="EX: PAI-001")
            nome       = st.text_input("Nome *")
            categoria  = st.selectbox("Categoria *", CATEGORIAS)
            unidade    = st.selectbox("Unidade *", UNIDADES)
            qtd_minima = st.number_input("Estoque Mínimo", min_value=0, step=1, value=0)

        with col2:
            custo_unitario = st.number_input("Custo Unitário (R$) *", min_value=0.0, step=10.0)
            preco_venda    = st.number_input("Preço de Venda (R$) *", min_value=0.0, step=10.0)
            fabricante     = st.text_input("Fabricante")
            modelo         = st.text_input("Modelo")
            potencia_w     = st.number_input("Potência (W)", min_value=0.0, step=10.0)

        salvar = st.form_submit_button("💾 Cadastrar Produto", type="primary")

        if salvar:
            if not codigo or not nome:
                st.error("Código e Nome são obrigatórios.")
            elif preco_venda <= 0:
                st.error("Preço de Venda deve ser maior que zero.")
            else:
                payload = {
                    "codigo"        : codigo.strip(),
                    "nome"          : nome.strip(),
                    "categoria"     : categoria,
                    "unidade"       : unidade,
                    "custo_unitario": custo_unitario,
                    "preco_venda"   : preco_venda,
                    "qtd_minima"    : int(qtd_minima),
                    "fabricante"    : fabricante.strip() or None,
                    "modelo"        : modelo.strip() or None,
                    "potencia_w"    : potencia_w if potencia_w > 0 else None,
                }
                resp = api_client.criar_produto(payload)
                if resp.status_code == 201:
                    st.success(f"✅ Produto **{nome}** cadastrado com sucesso!")
                    st.rerun()
                elif resp.status_code == 409:
                    st.error("Código já cadastrado. Use um código diferente.")
                else:
                    st.error(f"Erro: {resp.json().get('detail', 'Erro desconhecido')}")

# ── EDITAR / EXCLUIR PRODUTO ───────────────────────────────────────────────────
with tab_edit:
    produtos_edit = api_client.listar_produtos()
    if not produtos_edit:
        st.info("Nenhum produto cadastrado.")
    else:
        CATEGORIAS = ["Painel", "Inversor", "Cabo", "Estrutura", "Acessório", "Serviço"]
        UNIDADES   = ["UN", "M", "KG", "KWP"]

        op = {f"[{p['codigo']}] {p['nome']}": p for p in produtos_edit}
        selecionado = st.selectbox("Selecione o produto", list(op.keys()))
        p = op[selecionado]

        col_btn1, col_btn2, _ = st.columns([1, 1, 4])
        acao_editar  = col_btn1.button("✏️ Editar",  key="btn_edit_prod")
        acao_excluir = col_btn2.button("🗑️ Excluir", key="btn_del_prod")

        if acao_editar:
            st.session_state["editar_produto_id"] = p["id"]

        if acao_excluir:
            resp = api_client.excluir_produto(p["id"])
            if resp.status_code == 204:
                st.success(f"Produto **{p['nome']}** excluído.")
                st.session_state.pop("editar_produto_id", None)
                st.rerun()
            else:
                st.error(resp.json().get("detail", "Erro ao excluir"))

        if st.session_state.get("editar_produto_id") == p["id"]:
            st.markdown("---")
            st.subheader(f"Editando: {p['nome']}")

            with st.form("form_edit_produto"):
                col1, col2 = st.columns(2)

                with col1:
                    nome_e      = st.text_input("Nome",      value=p["nome"])
                    cat_idx     = CATEGORIAS.index(p["categoria"]) if p["categoria"] in CATEGORIAS else 0
                    categoria_e = st.selectbox("Categoria", CATEGORIAS, index=cat_idx)
                    uni_idx     = UNIDADES.index(p["unidade"]) if p["unidade"] in UNIDADES else 0
                    unidade_e   = st.selectbox("Unidade",   UNIDADES, index=uni_idx)
                    qtd_min_e   = st.number_input("Estoque Mínimo", min_value=0, step=1, value=int(p["qtd_minima"]))

                with col2:
                    custo_e     = st.number_input("Custo Unitário (R$)", min_value=0.0, step=10.0, value=float(p["custo_unitario"]))
                    preco_e     = st.number_input("Preço de Venda (R$)", min_value=0.0, step=10.0, value=float(p["preco_venda"]))
                    fabric_e    = st.text_input("Fabricante", value=p.get("fabricante") or "")
                    modelo_e    = st.text_input("Modelo",     value=p.get("modelo") or "")
                    pot_e       = st.number_input("Potência (W)", min_value=0.0, step=10.0, value=float(p.get("potencia_w") or 0))

                salvar_e = st.form_submit_button("💾 Salvar Alterações", type="primary")

                if salvar_e:
                    payload = {
                        "nome"          : (nome_e or "").strip(),
                        "categoria"     : categoria_e,
                        "unidade"       : unidade_e,
                        "custo_unitario": custo_e,
                        "preco_venda"   : preco_e,
                        "qtd_minima"    : int(qtd_min_e),
                        "fabricante"    : fabric_e.strip() or None,
                        "modelo"        : modelo_e.strip() or None,
                        "potencia_w"    : pot_e if pot_e > 0 else None,
                    }
                    resp = api_client.atualizar_produto(p["id"], payload)
                    if resp.status_code == 200:
                        st.success("✅ Produto atualizado!")
                        st.session_state.pop("editar_produto_id", None)
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail", "Erro ao atualizar"))
