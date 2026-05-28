import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import api_client

st.title("📈 Previsão de Vendas")

# ── DADOS ─────────────────────────────────────────────────────────────────────
vendas = api_client.listar_vendas()

STATUS_RECEITA  = {"Aprovado", "Em Andamento", "Concluído"}
STATUS_PIPELINE = {"Orçamento", "Negociação"}

aprovadas = [v for v in vendas if v["status_venda"] in STATUS_RECEITA]
pipeline  = [v for v in vendas if v["status_venda"] in STATUS_PIPELINE]
canceladas = [v for v in vendas if v["status_venda"] == "Cancelado"]

# ── AGRUPAMENTO MENSAL ────────────────────────────────────────────────────────
def _mes(v: dict) -> str:
    """Retorna 'YYYY-MM' a partir da data de orçamento."""
    dt = v.get("data_orcamento") or ""
    return dt[:7] if len(dt) >= 7 else "0000-00"

if not aprovadas:
    st.info("Nenhuma venda aprovada encontrada. Importe ou cadastre vendas para gerar a previsão.")
    st.stop()

df = (
    pd.DataFrame(aprovadas)
    .assign(mes=lambda d: d.apply(_mes, axis=1),
            valor=lambda d: d["valor_final"].astype(float))
    .groupby("mes", as_index=False)["valor"].sum()
    .sort_values("mes")
)

# Remove mês "0000-00" se houver dado sem data
df = df[df["mes"] != "0000-00"].reset_index(drop=True)

meses      = df["mes"].tolist()
receitas   = df["valor"].tolist()
n          = len(meses)
MESES_MIN  = 2   # mínimo para calcular tendência

# ── MÉTRICAS RÁPIDAS ──────────────────────────────────────────────────────────
tot_pipeline   = sum(float(v["valor_final"]) for v in pipeline)
total_hist     = len([v for v in vendas if v["status_venda"] != "Cancelado"])
total_aprov    = len(aprovadas)
taxa_conv      = total_aprov / total_hist if total_hist else 0
receita_esp    = tot_pipeline * taxa_conv

c1, c2, c3, c4 = st.columns(4)
c1.metric("Meses com dados", n)
c2.metric("Taxa de conversão histórica", f"{taxa_conv:.0%}")
c3.metric("Pipeline atual", f"R$ {tot_pipeline:,.2f}")
c4.metric("Receita esperada do pipeline", f"R$ {receita_esp:,.2f}",
          help="Pipeline × taxa de conversão histórica")

st.markdown("---")

# ── REGRESSÃO LINEAR ──────────────────────────────────────────────────────────
X = np.arange(n, dtype=float)
y = np.array(receitas, dtype=float)

if n >= MESES_MIN:
    coef = np.polyfit(X, y, 1)          # coef[0]=slope, coef[1]=intercept
    fn   = np.poly1d(coef)

    # Calcula R²
    y_pred = fn(X)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2     = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # Projeção: 3 meses à frente
    N_PROJ = 3
    ultimo_mes = pd.Period(meses[-1], freq="M")
    meses_proj  = [(ultimo_mes + i).strftime("%Y-%m") for i in range(1, N_PROJ + 1)]
    X_proj      = np.arange(n, n + N_PROJ, dtype=float)
    y_proj      = fn(X_proj).clip(min=0)   # receita não pode ser negativa

    # Rótulos formatados (Jan/26, Fev/26 …)
    _MESES_PT = ["Jan","Fev","Mar","Abr","Mai","Jun",
                 "Jul","Ago","Set","Out","Nov","Dez"]
    def _rotulo(ym: str) -> str:
        y_, m_ = int(ym[:4]), int(ym[5:7])
        return f"{_MESES_PT[m_-1]}/{str(y_)[2:]}"

    rot_hist = [_rotulo(m) for m in meses]
    rot_proj = [_rotulo(m) for m in meses_proj]
    todos_rot = rot_hist + rot_proj
    todos_X   = np.arange(n + N_PROJ, dtype=float)

    # ── GRÁFICO ───────────────────────────────────────────────────────────────
    fig = go.Figure()

    # Barras históricas
    fig.add_trace(go.Bar(
        x=rot_hist, y=receitas,
        name="Receita realizada",
        marker_color="#E6B400",
        text=[f"R$ {v:,.0f}" for v in receitas],
        textposition="outside",
    ))

    # Barras de projeção
    fig.add_trace(go.Bar(
        x=rot_proj, y=y_proj.tolist(),
        name="Projeção",
        marker_color="rgba(100, 180, 100, 0.6)",
        marker_line=dict(color="green", width=1.5, dash="dot"),
        text=[f"R$ {v:,.0f}" for v in y_proj],
        textposition="outside",
    ))

    # Linha de tendência (sobre todo o período)
    fig.add_trace(go.Scatter(
        x=todos_rot, y=fn(todos_X).clip(min=0).tolist(),
        name="Tendência (regressão linear)",
        mode="lines",
        line=dict(color="rgba(220,50,50,0.8)", width=2, dash="dash"),
    ))

    fig.update_layout(
        title=f"Receita Mensal · Tendência · Projeção  —  R² = {r2:.2f}",
        xaxis_title="Mês",
        yaxis_title="R$",
        barmode="group",
        legend=dict(orientation="h", y=-0.2),
        plot_bgcolor="white",
        height=420,
    )
    fig.update_yaxes(tickprefix="R$ ", tickformat=",.0f", gridcolor="#EEEEEE")

    st.plotly_chart(fig, use_container_width=True)

    # ── INTERPRETAÇÃO ─────────────────────────────────────────────────────────
    tendencia = coef[0]
    col_a, col_b, col_c = st.columns(3)

    col_a.metric(
        "Tendência mensal",
        f"R$ {tendencia:+,.2f}",
        delta=f"{'crescente' if tendencia >= 0 else 'decrescente'}",
        delta_color="normal" if tendencia >= 0 else "inverse",
    )
    col_b.metric("Próximo mês projetado", f"R$ {y_proj[0]:,.2f}")
    col_c.metric("R² do modelo", f"{r2:.2f}",
                 help="Quanto o modelo explica a variação histórica. 1.0 = perfeito.")

    if r2 < 0.4:
        st.caption(
            "⚠️ R² baixo: a receita ainda tem muita variação não-linear. "
            "A projeção é uma estimativa inicial — melhora com mais meses de dados."
        )

    # ── TABELA DETALHE ────────────────────────────────────────────────────────
    with st.expander("Ver tabela detalhada"):
        df_tab = pd.DataFrame({
            "Mês":        rot_hist,
            "Receita":    [f"R$ {v:,.2f}" for v in receitas],
            "Tendência":  [f"R$ {fn(x):,.2f}" for x in X],
        })
        df_proj_tab = pd.DataFrame({
            "Mês":       rot_proj,
            "Receita":   ["—"] * N_PROJ,
            "Tendência": [f"R$ {v:,.2f}" for v in y_proj],
        })
        st.dataframe(
            pd.concat([df_tab, df_proj_tab], ignore_index=True),
            use_container_width=True, hide_index=True,
        )

else:
    st.warning(
        f"São necessários pelo menos {MESES_MIN} meses de vendas aprovadas para calcular a tendência. "
        f"Atualmente há {n} mês/meses com dados."
    )
    if n == 1:
        st.metric("Receita do único mês registrado",
                  f"R$ {receitas[0]:,.2f}", label_visibility="visible")
