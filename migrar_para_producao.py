"""
Migração completa para produção — execute UMA única vez:
  1. SQLite local → API  (clientes, produtos, colaboradores, projetos, OS, financeiro)
  2. Excel          → API  (projetos de homologação)

    python migrar_para_producao.py
"""
import re
import sqlite3
import sys
from datetime import datetime, timedelta, date

import openpyxl
import requests

EXCEL_PATH = r"C:\Users\Marcelo Vieira\Downloads\CONTROLE DE PROJETOS.xlsx"

API_URL = input("Cole a URL do Railway (ex: https://mvenergiasolar-production.up.railway.app): ").strip().rstrip("/")
if not API_URL.startswith("http"):
    print("URL inválida.")
    sys.exit(1)

print(f"\nConectando em {API_URL} ...")
try:
    requests.get(f"{API_URL}/clientes/", timeout=30).raise_for_status()
    print("API OK\n")
except Exception as e:
    print(f"Não consegui conectar: {e}")
    sys.exit(1)

ok_total  = 0
err_total = 0


def _post(endpoint, payload, label):
    global ok_total, err_total
    resp = requests.post(f"{API_URL}/{endpoint}/", json=payload, timeout=30)
    if resp.status_code in (200, 201):
        ok_total += 1
        return resp.json()
    err_total += 1
    detail = resp.json().get("detail", resp.text) if resp.content else resp.status_code
    print(f"  ERRO {label}: {detail}")
    return None


# ══════════════════════════════════════════════════════════════════════════════
# PARTE 1 — SQLite local
# ══════════════════════════════════════════════════════════════════════════════
conn = sqlite3.connect("solar.db")
conn.row_factory = sqlite3.Row

# ── Clientes ──────────────────────────────────────────────────────────────────
clientes_db = conn.execute("SELECT * FROM clientes").fetchall()
print(f"Migrando {len(clientes_db)} clientes do SQLite...")
id_map_clientes: dict[int, int] = {}

for c in clientes_db:
    payload = {k: c[k] for k in c.keys()
               if k not in ("id", "data_cadastro") and c[k] is not None}
    resp = requests.post(f"{API_URL}/clientes/", json=payload, timeout=30)
    if resp.status_code in (200, 201):
        id_map_clientes[c["id"]] = resp.json()["id"]
        ok_total += 1
    else:
        err_total += 1
        detail = resp.json().get("detail", resp.text) if resp.content else resp.status_code
        print(f"  ERRO cliente '{c['nome']}': {detail}")

# ── Produtos ──────────────────────────────────────────────────────────────────
produtos_db = conn.execute("SELECT * FROM produtos").fetchall()
print(f"Migrando {len(produtos_db)} produtos...")
id_map_produtos: dict[int, int] = {}
CAT = {"PAINEL": "Painel", "INVERSOR": "Inversor", "CABO": "Cabo",
       "ESTRUTURA": "Estrutura", "ACESSORIO": "Acessório", "SERVICO": "Serviço"}

for p in produtos_db:
    payload = {k: p[k] for k in p.keys() if k not in ("id",) and p[k] is not None}
    if "categoria" in payload:
        payload["categoria"] = CAT.get(payload["categoria"], payload["categoria"])
    resp = requests.post(f"{API_URL}/produtos/", json=payload, timeout=30)
    if resp.status_code in (200, 201):
        id_map_produtos[p["id"]] = resp.json()["id"]
        ok_total += 1
    else:
        err_total += 1
        detail = resp.json().get("detail", resp.text) if resp.content else resp.status_code
        print(f"  ERRO produto '{p['nome']}': {detail}")

# ── Colaboradores ─────────────────────────────────────────────────────────────
colab_db = conn.execute("SELECT * FROM colaboradores").fetchall()
print(f"Migrando {len(colab_db)} colaboradores...")
TC = {"CLT": "CLT", "AUTONOMO": "Autônomo", "PJ": "PJ"}

for c in colab_db:
    payload = {k: c[k] for k in c.keys()
               if k not in ("id_colaborador", "status") and c[k] is not None}
    if "tipo_contrato" in payload:
        payload["tipo_contrato"] = TC.get(payload["tipo_contrato"], payload["tipo_contrato"])
    _post("colaboradores", payload, f"colaborador '{c['nome']}'")

# ── Projetos do SQLite ────────────────────────────────────────────────────────
try:
    projetos_db = conn.execute("SELECT * FROM projetos").fetchall()
except Exception:
    projetos_db = []
print(f"Migrando {len(projetos_db)} projetos do SQLite...")
SP = {"EM_ANALISE": "Em Análise", "APROVADO": "Aprovado",
      "APROVADO_COM_OBRAS": "Aprovado c/ Obras", "FALTA_TRT": "Falta TRT", "CANCELADO": "Cancelado"}
SV = {"NAO_SOLICITADO": "Não Solicitado", "SOLICITADO": "Solicitado", "REALIZADO": "Realizado"}

for p in projetos_db:
    cliente_prod = id_map_clientes.get(p["cliente_id"])
    if not cliente_prod:
        print(f"  AVISO projeto #{p['id']}: cliente não migrado, pulando")
        continue
    payload = {k: p[k] for k in p.keys() if k not in ("id",) and p[k] is not None}
    payload["cliente_id"] = cliente_prod
    if "status_projeto"  in payload: payload["status_projeto"]  = SP.get(payload["status_projeto"],  payload["status_projeto"])
    if "status_vistoria" in payload: payload["status_vistoria"] = SV.get(payload["status_vistoria"], payload["status_vistoria"])
    _post("projetos", payload, f"projeto #{p['id']}")

# ── Ordens de Serviço ─────────────────────────────────────────────────────────
try:
    os_db = conn.execute("SELECT * FROM ordens_servico").fetchall()
except Exception:
    os_db = []
print(f"Migrando {len(os_db)} ordens de serviço...")
TS = {"PREVENTIVA": "Preventiva", "CORRETIVA": "Corretiva", "LIMPEZA": "Limpeza",
      "INSPECAO": "Inspeção", "GARANTIA": "Garantia", "OUTROS": "Outros"}
SS = {"ABERTA": "Aberta", "EM_ANDAMENTO": "Em Andamento", "CONCLUIDA": "Concluída", "CANCELADA": "Cancelada"}

for o in os_db:
    cliente_prod = id_map_clientes.get(o["cliente_id"])
    if not cliente_prod:
        continue
    payload = {k: o[k] for k in o.keys() if k not in ("id", "id_os") and o[k] is not None}
    payload["cliente_id"] = cliente_prod
    if "tipo_servico" in payload: payload["tipo_servico"] = TS.get(payload["tipo_servico"], payload["tipo_servico"])
    if "status_os"    in payload: payload["status_os"]    = SS.get(payload["status_os"],    payload["status_os"])
    _post("ordens-servico", payload, f"OS #{o['id_os']}")

# ── Financeiro ────────────────────────────────────────────────────────────────
try:
    lanc_db = conn.execute("SELECT * FROM lancamentos").fetchall()
except Exception:
    lanc_db = []
print(f"Migrando {len(lanc_db)} lançamentos financeiros...")
CT = {"RECEITA": "Receita", "DESPESA": "Despesa"}
SP2 = {"PENDENTE": "Pendente", "PAGO": "Pago", "ATRASADO": "Atrasado", "CANCELADO": "Cancelado"}

for l in lanc_db:
    payload = {k: l[k] for k in l.keys() if k not in ("id",) and l[k] is not None}
    if "tipo"             in payload: payload["tipo"]             = CT.get(payload["tipo"],             payload["tipo"])
    if "status_pagamento" in payload: payload["status_pagamento"] = SP2.get(payload["status_pagamento"], payload["status_pagamento"])
    _post("financeiro", payload, f"lançamento #{l['id']}")

conn.close()
print(f"\nSQLite concluído: {ok_total} OK, {err_total} erros até aqui.\n")

# ══════════════════════════════════════════════════════════════════════════════
# PARTE 2 — Excel (projetos de homologação)
# ══════════════════════════════════════════════════════════════════════════════

def _excel_para_date(valor) -> date | None:
    if isinstance(valor, datetime): return valor.date()
    if isinstance(valor, (int, float)) and valor > 0:
        return (datetime(1899, 12, 30) + timedelta(days=int(valor))).date()
    return None

def _parse_resultado(valor, base: date | None) -> date | None:
    if isinstance(valor, datetime): return valor.date()
    if isinstance(valor, str):
        m = re.search(r"\+(\d+)", valor)
        if m and base:
            return base + timedelta(days=int(m.group(1)))
    return None

def _normalizar(nome: str) -> str:
    return re.sub(r"\s*\([^)]*\)", "", nome).strip()

def _status_projeto(v: str) -> str:
    v = v.upper()
    if "OBRAS"    in v: return "Aprovado c/ Obras"
    if "TRT"      in v: return "Falta TRT"
    if "APROVADO" in v: return "Aprovado"
    return "Em Análise"

def _status_vistoria(v) -> str:
    v = str(v).upper()
    if "REALIZADO"  in v: return "Realizado"
    if "SOLICITADO" in v: return "Solicitado"
    return "Não Solicitado"

try:
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb["PROJETOS FINALIZADOS"]
    linhas = [
        row for row in ws.iter_rows(min_row=3, values_only=True)
        if row[0] and isinstance(row[0], str) and row[0] != "NOME:"
    ]
    print(f"Excel: {len(linhas)} projetos encontrados.\n")
except Exception as e:
    print(f"⚠ Não foi possível ler o Excel ({e}). Pulando importação do Excel.\n")
    linhas = []

if linhas:
    # Recarrega todos os clientes já na API (inclui os recém-migrados do SQLite)
    clientes_api = requests.get(f"{API_URL}/clientes/", timeout=30).json()
    nome_para_id: dict[str, int] = {c["nome"]: c["id"] for c in clientes_api}

    ok_excel_cli = 0
    ok_excel_proj = 0

    # Cria clientes do Excel que ainda não existem na API
    nomes_necessarios = {_normalizar(str(row[0]).strip()) for row in linhas}
    for nome in nomes_necessarios:
        if nome in nome_para_id:
            continue
        resp = requests.post(f"{API_URL}/clientes/", json={"nome": nome, "tipo_pessoa": "PF"}, timeout=30)
        if resp.status_code in (200, 201):
            nome_para_id[nome] = resp.json()["id"]
            ok_excel_cli += 1
            ok_total += 1
            print(f"  + Cliente criado (Excel): {nome}")
        else:
            err_total += 1
            detail = resp.json().get("detail", resp.text) if resp.content else resp.status_code
            print(f"  ERRO cliente Excel '{nome}': {detail}")

    print(f"Excel: {ok_excel_cli} clientes novos criados.\n")

    # Importa projetos do Excel
    for row in linhas:
        nome_base  = _normalizar(str(row[0]).strip())
        cliente_id = nome_para_id.get(nome_base)
        if not cliente_id:
            print(f"  ⚠ Cliente não mapeado: {nome_base}")
            err_total += 1
            continue

        kwp          = float(row[1]) if isinstance(row[1], (int, float)) else None
        inversor     = str(row[2]).strip() if row[2] and isinstance(row[2], str) else None
        status_raw   = str(row[5]).strip() if row[5] and isinstance(row[5], str) else ""
        data_entrada = _excel_para_date(row[6])
        data_result  = _parse_resultado(row[7], data_entrada)
        protocolo    = str(row[8]).strip() if row[8] else None
        uc           = str(row[9]).strip() if row[9] else None
        vistoria_raw = row[10]

        payload: dict = {
            "cliente_id"     : cliente_id,
            "status_projeto" : _status_projeto(status_raw),
            "status_vistoria": _status_vistoria(vistoria_raw),
        }
        if uc:           payload["uc"]             = uc
        if protocolo:    payload["protocolo"]      = protocolo
        if kwp:          payload["kwp"]            = kwp
        if inversor:     payload["inversor"]       = inversor
        if data_entrada: payload["data_entrada"]   = data_entrada.isoformat()
        if data_result:  payload["data_resultado"] = data_result.isoformat()

        result = _post("projetos", payload, f"projeto Excel '{nome_base}'")
        if result:
            ok_excel_proj += 1

    print(f"Excel: {ok_excel_proj} projetos importados.\n")

# ══════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print(f"  TOTAL: {ok_total} registros importados, {err_total} erros")
print("=" * 60)
