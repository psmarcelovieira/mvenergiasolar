"""
Script de importação dos projetos de homologação do Excel.
Execute UMA única vez com o servidor uvicorn rodando:

    python importar_projetos.py
"""
import re
import sys
from datetime import datetime, timedelta, date

import openpyxl

sys.path.insert(0, ".")
from app.database import SessionLocal
from app.models.cliente import Cliente
from app.models.projeto import HomologacaoProjeto
from app.enums import StatusProjeto, StatusVistoria, StatusCliente, TipoPessoa

EXCEL_PATH = r"C:\Users\Marcelo Vieira\Downloads\CONTROLE DE PROJETOS.xlsx"


def excel_serial_para_date(valor) -> date | None:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, (int, float)) and valor > 0:
        return (datetime(1899, 12, 30) + timedelta(days=int(valor))).date()
    return None


def parse_resultado(valor, data_entrada: date | None) -> date | None:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, str):
        match = re.search(r"\+(\d+)", valor)
        if match and data_entrada:
            return data_entrada + timedelta(days=int(match.group(1)))
    return None


def normalizar_nome(nome: str) -> str:
    """Remove anotações entre parênteses para agrupar variações do mesmo cliente."""
    return re.sub(r"\s*\([^)]*\)", "", nome).strip()


def mapear_status(valor: str) -> StatusProjeto:
    if not valor:
        return StatusProjeto.EM_ANALISE
    v = valor.upper()
    if "OBRAS" in v:
        return StatusProjeto.APROVADO_COM_OBRAS
    if "ANALISE" in v or "ANÁLISE" in v:
        return StatusProjeto.EM_ANALISE
    if "TRT" in v:
        return StatusProjeto.FALTA_TRT
    if "APROVADO" in v:
        return StatusProjeto.APROVADO
    return StatusProjeto.EM_ANALISE


def mapear_vistoria(valor) -> StatusVistoria:
    if not valor:
        return StatusVistoria.NAO_SOLICITADO
    v = str(valor).upper()
    if "REALIZADO" in v:
        return StatusVistoria.REALIZADO
    if "SOLICITADO" in v:
        return StatusVistoria.SOLICITADO
    return StatusVistoria.NAO_SOLICITADO


# ── Leitura do Excel ──────────────────────────────────────────────────────────
wb = openpyxl.load_workbook(EXCEL_PATH)
ws = wb["PROJETOS FINALIZADOS"]

linhas = []
for row in ws.iter_rows(min_row=3, values_only=True):
    if row[0] and isinstance(row[0], str) and row[0] != "NOME:":
        linhas.append(row)

print(f"✅ {len(linhas)} projetos encontrados no Excel.")

# ── Banco de dados ────────────────────────────────────────────────────────────
db = SessionLocal()

try:
    # 1. Cria clientes (nomes normalizados, sem duplicatas)
    nome_para_id: dict[str, int] = {}

    for row in linhas:
        nome_raw   = row[0].strip()
        nome_base  = normalizar_nome(nome_raw)

        if nome_base in nome_para_id:
            continue

        existente = db.query(Cliente).filter(Cliente.nome == nome_base).first()
        if existente:
            nome_para_id[nome_base] = existente.id
            print(f"  → Cliente já existe: {nome_base}")
            continue

        from datetime import date as _date
        cliente = Cliente(
            nome          = nome_base,
            tipo_pessoa   = TipoPessoa.PF,
            status        = StatusCliente.ATIVO,
            data_cadastro = _date.today(),
        )
        db.add(cliente)
        db.flush()
        nome_para_id[nome_base] = cliente.id
        print(f"  + Cliente criado: {nome_base}")

    db.commit()
    print(f"\n✅ {len(nome_para_id)} clientes no banco.")

    # 2. Importa projetos
    importados = 0
    for row in linhas:
        nome_raw    = row[0].strip()
        nome_base   = normalizar_nome(nome_raw)
        cliente_id  = nome_para_id.get(nome_base)

        if not cliente_id:
            print(f"  ⚠ Cliente não encontrado para: {nome_raw}")
            continue

        kwp         = float(row[1]) if row[1] else None
        inversor    = str(row[2]).strip() if row[2] else None
        status_raw  = str(row[5]).strip() if row[5] else None
        entrada_raw = row[6]
        result_raw  = row[7]
        protocolo   = str(row[8]).strip() if row[8] else None
        uc          = str(row[9]).strip() if row[9] else None
        vistoria_raw = row[10]

        data_entrada   = excel_serial_para_date(entrada_raw)
        data_resultado = parse_resultado(result_raw, data_entrada)

        projeto = HomologacaoProjeto(
            cliente_id      = cliente_id,
            uc              = uc,
            data_entrada    = data_entrada,
            data_resultado  = data_resultado,
            protocolo       = protocolo,
            status_projeto  = mapear_status(status_raw),
            status_vistoria = mapear_vistoria(vistoria_raw),
            kwp             = kwp,
            inversor        = inversor,
        )
        db.add(projeto)
        importados += 1

    db.commit()
    print(f"✅ {importados} projetos importados com sucesso!")

except Exception as e:
    db.rollback()
    print(f"❌ Erro durante importação: {e}")
    raise
finally:
    db.close()
