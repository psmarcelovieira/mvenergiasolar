"""Geração de relatórios PDF para o Sistema MV Energia Solar."""
from fpdf import FPDF
from datetime import date as _date

# Caracteres fora do charset Latin-1 do Helvetica precisam ser substituídos
_SUBS = str.maketrans({
    "—": "-",   # em dash —
    "–": "-",   # en dash –
    "‘": "'",   # aspas esquerda '
    "’": "'",   # aspas direita '
    "“": '"',   # aspas dupla esquerda "
    "”": '"',   # aspas dupla direita "
    "•": "*",   # bullet •
    "°": "o",   # grau °
})


def _s(texto) -> str:
    """Sanitiza texto para o charset Latin-1 usado pelo Helvetica."""
    return str(texto).translate(_SUBS)


EMPRESA = "MV Energia Solar"
AMARELO = (230, 180, 0)
CINZA   = (128, 128, 128)
PRETO   = (0, 0, 0)


class _PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(*PRETO)
        self.cell(0, 8, EMPRESA, ln=True, align="C")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*CINZA)
        self.cell(0, 5, "Energia Solar Fotovoltaica", ln=True, align="C")
        self.set_text_color(*PRETO)
        self.set_draw_color(*AMARELO)
        self.set_line_width(0.8)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(6)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*CINZA)
        self.cell(0, 5,
                  f"Gerado em {_date.today().strftime('%d/%m/%Y')}  -  Pag. {self.page_no()}",
                  align="C")


def _titulo_secao(pdf: _PDF, texto: str):
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(*AMARELO)
    pdf.set_text_color(*PRETO)
    pdf.cell(0, 7, _s(f"  {texto}"), ln=True, fill=True)
    pdf.ln(2)


def _cabecalho_tabela(pdf: _PDF, colunas: list[str], larguras: list[int]):
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(240, 240, 240)
    for texto, w in zip(colunas, larguras):
        pdf.cell(w, 6, _s(texto), border=1, fill=True)
    pdf.ln()


def _linha_tabela(pdf: _PDF, valores: list, larguras: list[int]):
    pdf.set_font("Helvetica", "", 8)
    pdf.set_fill_color(255, 255, 255)
    for texto, w in zip(valores, larguras):
        pdf.cell(w, 6, _s(texto), border=1)
    pdf.ln()


def _kpi(pdf: _PDF, rotulos: list[str], valores: list[str]):
    w = 190 // len(rotulos)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(255, 245, 200)
    for r, v in zip(rotulos, valores):
        pdf.cell(w, 10, _s(f"{r}: {v}"), border=1, fill=True, align="C")
    pdf.ln(14)


# ── PROPOSTA COMERCIAL ─────────────────────────────────────────────────────────
def gerar_proposta(
    venda: dict,
    cliente: dict,
    itens: list,
    map_produtos: dict,
    colaborador: dict | None = None,
) -> bytes:
    pdf = _PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(10, 20, 10)
    pdf.add_page()

    _titulo_secao(pdf, f"Proposta Comercial  -  Venda #{venda['id']}")
    pdf.ln(2)

    # Dados do cliente
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "Cliente", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, _s(f"Nome: {cliente['nome']}"), ln=True)
    if cliente.get("cpf_cnpj"):
        pdf.cell(0, 5, _s(f"CPF/CNPJ: {cliente['cpf_cnpj']}"), ln=True)
    linha_loc = " | ".join(filter(None, [
        cliente.get("telefone"), cliente.get("email"),
        f"{cliente.get('cidade','')}/{cliente.get('uf','')}" if cliente.get("cidade") else None,
    ]))
    if linha_loc:
        pdf.cell(0, 5, _s(linha_loc), ln=True)
    pdf.ln(3)

    # Dados da proposta
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "Dados da Proposta", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(95, 5, _s(f"Data: {venda['data_orcamento']}"), ln=False)
    pdf.cell(95, 5, _s(f"Forma de Pagamento: {venda['forma_pagamento']}"), ln=True)
    if int(venda.get("parcelas") or 1) > 1:
        pdf.cell(95, 5, _s(f"Parcelas: {venda['parcelas']}x"), ln=False)
    if colaborador:
        pdf.cell(95, 5, _s(f"Responsavel: {colaborador['nome']}"), ln=True)
    pdf.ln(4)

    # Tabela de itens
    _titulo_secao(pdf, "Itens")
    cols = ["Produto", "Qtd", "Preco Unitario", "Subtotal"]
    wids = [105, 15, 37, 33]
    _cabecalho_tabela(pdf, cols, wids)

    total_equip = 0.0
    for item in itens:
        prod_nome = map_produtos.get(item["produto_id"], f"Produto #{item['produto_id']}")
        qty       = float(item["quantidade"])
        preco     = float(item["preco_unitario"])
        sub       = qty * preco
        total_equip += sub
        _linha_tabela(pdf, [
            prod_nome[:45],
            f"{qty:.0f}",
            f"R$ {preco:,.2f}",
            f"R$ {sub:,.2f}",
        ], wids)
    pdf.ln(4)

    # Totais
    inst  = float(venda.get("valor_instalacao") or 0)
    desc  = float(venda.get("desconto") or 0)
    total = total_equip + inst - desc

    def _tot_linha(label, valor, negrito=False):
        pdf.set_font("Helvetica", "B" if negrito else "", 9)
        pdf.cell(157, 6, _s(label), align="R")
        pdf.cell(33, 6, f"R$ {valor:,.2f}", border="B" if negrito else 0,
                 ln=True, align="R")

    _tot_linha("Equipamentos:", total_equip)
    if inst > 0:
        _tot_linha("Instalacao:", inst)
    if desc > 0:
        _tot_linha("Desconto:", -desc)
    pdf.set_line_width(0.3)
    _tot_linha("TOTAL:", total, negrito=True)

    if venda.get("observacoes"):
        pdf.ln(5)
        _titulo_secao(pdf, "Observacoes")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, _s(venda["observacoes"]))

    # Assinatura
    pdf.ln(15)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.3)
    pdf.cell(85, 0, "", border="T")
    pdf.cell(20)
    pdf.cell(85, 0, "", border="T", ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(85, 5, EMPRESA, align="C")
    pdf.cell(20)
    pdf.cell(85, 5, _s(cliente["nome"]), align="C", ln=True)

    return bytes(pdf.output())


# ── EXTRATO FINANCEIRO ─────────────────────────────────────────────────────────
def gerar_extrato_financeiro(
    lancamentos: list,
    data_ini: str,
    data_fim: str,
) -> bytes:
    pdf = _PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(10, 20, 10)
    pdf.add_page()

    _titulo_secao(pdf, f"Extrato Financeiro  -  {data_ini} a {data_fim}")
    pdf.ln(2)

    receitas  = [l for l in lancamentos if l["tipo"] == "Receita"]
    despesas  = [l for l in lancamentos if l["tipo"] == "Despesa"]
    tot_rec   = sum(float(l["valor"]) for l in receitas)
    tot_desp  = sum(float(l["valor"]) for l in despesas)
    saldo     = tot_rec - tot_desp

    _kpi(pdf,
         ["Receitas", "Despesas", "Saldo"],
         [f"R$ {tot_rec:,.2f}", f"R$ {tot_desp:,.2f}", f"R$ {saldo:,.2f}"])

    cols = ["Data Venc.", "Descricao", "Categoria", "Status", "Valor"]
    wids = [23, 75, 38, 23, 31]

    def _secao_financeira(titulo, lista):
        if not lista:
            return
        _titulo_secao(pdf, titulo)
        _cabecalho_tabela(pdf, cols, wids)
        for l in lista:
            _linha_tabela(pdf, [
                l["data_vencimento"],
                l["descricao"][:42],
                l["categoria"],
                l["status_pagamento"],
                f"R$ {float(l['valor']):,.2f}",
            ], wids)
        pdf.ln(4)

    _secao_financeira("Receitas", receitas)
    _secao_financeira("Despesas", despesas)

    return bytes(pdf.output())


# ── RELATÓRIO DE ORDENS DE SERVIÇO ────────────────────────────────────────────
def gerar_relatorio_os(
    ordens: list,
    map_clientes: dict,
    data_ini: str,
    data_fim: str,
) -> bytes:
    pdf = _PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(10, 20, 10)
    pdf.add_page()

    _titulo_secao(pdf, f"Ordens de Servico  -  {data_ini} a {data_fim}")
    pdf.ln(2)

    total_custo = sum(float(o.get("custo_total") or 0) for o in ordens)
    concluidas  = sum(1 for o in ordens if o["status_os"] == "Concluida")

    _kpi(pdf,
         ["Total de OS", "Concluidas", "Total Faturado"],
         [str(len(ordens)), str(concluidas), f"R$ {total_custo:,.2f}"])

    cols = ["OS", "Cliente", "Tipo", "Status", "Abertura", "Custo"]
    wids = [18, 62, 30, 28, 22, 30]
    _cabecalho_tabela(pdf, cols, wids)

    for o in ordens:
        _linha_tabela(pdf, [
            o["id_os"],
            map_clientes.get(o["cliente_id"], f"#{o['cliente_id']}")[:28],
            o["tipo_servico"],
            o["status_os"],
            o["data_abertura"],
            f"R$ {float(o['custo_total']):,.2f}" if o.get("custo_total") else "-",
        ], wids)

    return bytes(pdf.output())
