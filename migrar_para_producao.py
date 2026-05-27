"""
Migra dados do banco SQLite local para a API de produção no Railway.
Execute com o venv ativado:
    python migrar_para_producao.py
"""
import sqlite3
import requests
import sys

API_URL = input("Cole a URL do Railway (ex: https://mvenergiasolar-production.up.railway.app): ").strip().rstrip("/")

if not API_URL.startswith("http"):
    print("URL inválida.")
    sys.exit(1)

print(f"\nConectando em {API_URL} ...")
try:
    r = requests.get(f"{API_URL}/clientes/", timeout=30)
    r.raise_for_status()
    print("API OK\n")
except Exception as e:
    print(f"Não consegui conectar: {e}")
    sys.exit(1)

conn = sqlite3.connect("solar.db")
conn.row_factory = sqlite3.Row

ok_total = 0
err_total = 0


def _post(endpoint, payload, label):
    global ok_total, err_total
    resp = requests.post(f"{API_URL}/{endpoint}/", json=payload, timeout=30)
    if resp.status_code in (200, 201):
        ok_total += 1
    else:
        err_total += 1
        detail = resp.json().get("detail", resp.text) if resp.content else resp.status_code
        print(f"  ERRO {label}: {detail}")


# ── CLIENTES ──────────────────────────────────────────────────────────────────
clientes_db = conn.execute("SELECT * FROM clientes").fetchall()
print(f"Migrando {len(clientes_db)} clientes...")
id_map_clientes = {}   # id_local -> id_producao

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

# ── PRODUTOS ──────────────────────────────────────────────────────────────────
produtos_db = conn.execute("SELECT * FROM produtos").fetchall()
print(f"Migrando {len(produtos_db)} produtos...")
id_map_produtos = {}

CAT = {"PAINEL": "Painel", "INVERSOR": "Inversor", "CABO": "Cabo",
       "ESTRUTURA": "Estrutura", "ACESSORIO": "Acessório", "SERVICO": "Serviço"}

for p in produtos_db:
    payload = {k: p[k] for k in p.keys()
               if k not in ("id",) and p[k] is not None}
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

# ── COLABORADORES ─────────────────────────────────────────────────────────────
colab_db = conn.execute("SELECT * FROM colaboradores").fetchall()
print(f"Migrando {len(colab_db)} colaboradores...")
id_map_colab = {}

for c in colab_db:
    payload = {k: c[k] for k in c.keys()
               if k not in ("id_colaborador", "status") and c[k] is not None}
    # tipo_contrato está salvo como nome do enum no SQLite (ex: AUTONOMO)
    # a API espera o valor (ex: Autônomo) — converte
    TC = {"CLT": "CLT", "AUTONOMO": "Autônomo", "PJ": "PJ"}
    if "tipo_contrato" in payload:
        payload["tipo_contrato"] = TC.get(payload["tipo_contrato"], payload["tipo_contrato"])
    resp = requests.post(f"{API_URL}/colaboradores/", json=payload, timeout=30)
    if resp.status_code in (200, 201):
        id_map_colab[c["id_colaborador"]] = resp.json()["id_colaborador"]
        ok_total += 1
    else:
        err_total += 1
        detail = resp.json().get("detail", resp.text) if resp.content else resp.status_code
        print(f"  ERRO colaborador '{c['nome']}': {detail}")

# ── PROJETOS ──────────────────────────────────────────────────────────────────
try:
    projetos_db = conn.execute("SELECT * FROM projetos").fetchall()
except Exception:
    projetos_db = []
print(f"Migrando {len(projetos_db)} projetos...")

for p in projetos_db:
    cliente_prod = id_map_clientes.get(p["cliente_id"])
    if not cliente_prod:
        print(f"  AVISO projeto #{p['id']}: cliente_id {p['cliente_id']} não migrado, pulando")
        continue
    payload = {k: p[k] for k in p.keys()
               if k not in ("id",) and p[k] is not None}
    payload["cliente_id"] = cliente_prod
    SP = {"EM_ANALISE": "Em Análise", "APROVADO": "Aprovado",
          "APROVADO_COM_OBRAS": "Aprovado c/ Obras",
          "FALTA_TRT": "Falta TRT", "CANCELADO": "Cancelado"}
    SV = {"NAO_SOLICITADO": "Não Solicitado", "SOLICITADO": "Solicitado", "REALIZADO": "Realizado"}
    if "status_projeto"  in payload: payload["status_projeto"]  = SP.get(payload["status_projeto"],  payload["status_projeto"])
    if "status_vistoria" in payload: payload["status_vistoria"] = SV.get(payload["status_vistoria"], payload["status_vistoria"])
    _post("projetos", payload, f"projeto #{p['id']}")

# ── ORDENS DE SERVIÇO ─────────────────────────────────────────────────────────
try:
    os_db = conn.execute("SELECT * FROM ordens_servico").fetchall()
except Exception:
    os_db = []
print(f"Migrando {len(os_db)} ordens de serviço...")

for o in os_db:
    cliente_prod = id_map_clientes.get(o["cliente_id"])
    if not cliente_prod:
        continue
    payload = {k: o[k] for k in o.keys()
               if k not in ("id", "id_os") and o[k] is not None}
    payload["cliente_id"] = cliente_prod
    TS = {"PREVENTIVA": "Preventiva", "CORRETIVA": "Corretiva", "LIMPEZA": "Limpeza",
          "INSPECAO": "Inspeção", "GARANTIA": "Garantia", "OUTROS": "Outros"}
    SS = {"ABERTA": "Aberta", "EM_ANDAMENTO": "Em Andamento",
          "CONCLUIDA": "Concluída", "CANCELADA": "Cancelada"}
    if "tipo_servico" in payload: payload["tipo_servico"] = TS.get(payload["tipo_servico"], payload["tipo_servico"])
    if "status_os"    in payload: payload["status_os"]    = SS.get(payload["status_os"],    payload["status_os"])
    _post("ordens-servico", payload, f"OS #{o['id_os']}")

# ── FINANCEIRO ────────────────────────────────────────────────────────────────
try:
    lanc_db = conn.execute("SELECT * FROM lancamentos").fetchall()
except Exception:
    lanc_db = []
print(f"Migrando {len(lanc_db)} lançamentos financeiros...")

for l in lanc_db:
    payload = {k: l[k] for k in l.keys()
               if k not in ("id",) and l[k] is not None}
    CT = {"RECEITA": "Receita", "DESPESA": "Despesa"}
    SP = {"PENDENTE": "Pendente", "PAGO": "Pago", "ATRASADO": "Atrasado", "CANCELADO": "Cancelado"}
    if "tipo"             in payload: payload["tipo"]             = CT.get(payload["tipo"],             payload["tipo"])
    if "status_pagamento" in payload: payload["status_pagamento"] = SP.get(payload["status_pagamento"], payload["status_pagamento"])
    _post("financeiro", payload, f"lançamento #{l['id']}")

conn.close()

print(f"\n{'='*50}")
print(f"Migração concluída: {ok_total} registros OK, {err_total} erros")
print(f"{'='*50}")
