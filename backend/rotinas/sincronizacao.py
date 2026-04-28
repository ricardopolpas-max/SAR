# backend/rotinas/sincronizacao.py
# Motor de sincronização bidirecional com a API pública do Peixe 30.
# Chamado no startup do servidor e via endpoint POST /vagas/sincronizar.

import json
import sqlite3
import urllib.request
from datetime import datetime, timezone

from rotinas.genericas import DB_PATH

_API_URL  = "https://api.jobs.peixe30.com/v1/jobs/search/eligible-to-apply-for"
_PER_PAGE = 50
_FONTE    = "peixe30"

# ------------------------------------------------------------
# UTILITÁRIOS
# ------------------------------------------------------------
def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

def _mapear(item: dict, sync_time: str) -> dict:
    salario = item.get("startingSalaryInCents")
    return {
        "titulo":               item.get("name", ""),
        "empresa":              item.get("companyName", ""),
        "link":                 item.get("publicUrl", ""),
        "localizacao":          item.get("location", ""),
        "modalidade":           item.get("modality", ""),
        "tipo_contrato":        item.get("contractType", ""),
        "salario_inicial":      salario if isinstance(salario, int) else None,
        "descricao":            item.get("requisites", ""),
        "id_externo":           item.get("_id", ""),
        "fonte":                _FONTE,
        "ultima_sincronizacao": sync_time,
    }

# ------------------------------------------------------------
# SYNC PRINCIPAL
# ------------------------------------------------------------
def sincronizar() -> dict:
    """
    Sync bidirecional com o Peixe 30:
    - INSERT novas vagas
    - UPDATE existentes  (chave: id_externo)
    - DELETE removidas da plataforma
    Retorna resumo com contadores.
    """
    sync_time = datetime.now(timezone.utc).isoformat()

    try:
        primeira   = _get_json(f"{_API_URL}?page=1&perPage={_PER_PAGE}")
        ultima_pag = primeira["meta"]["lastPage"]
        total_api  = primeira["meta"]["total"]
    except Exception as e:
        return {"ok": False, "erro": f"Falha ao contatar Peixe 30: {e}"}

    processadas = 0

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()

        for num in range(1, ultima_pag + 1):
            try:
                pagina = primeira if num == 1 else _get_json(
                    f"{_API_URL}?page={num}&perPage={_PER_PAGE}"
                )
                for item in pagina.get("data", []):
                    cursor.execute("""
                        INSERT INTO vagas
                            (titulo, empresa, link, localizacao, modalidade,
                             tipo_contrato, salario_inicial, descricao,
                             id_externo, fonte, ultima_sincronizacao)
                        VALUES
                            (:titulo, :empresa, :link, :localizacao, :modalidade,
                             :tipo_contrato, :salario_inicial, :descricao,
                             :id_externo, :fonte, :ultima_sincronizacao)
                        ON CONFLICT(id_externo) DO UPDATE SET
                            titulo               = excluded.titulo,
                            empresa              = excluded.empresa,
                            link                 = excluded.link,
                            localizacao          = excluded.localizacao,
                            modalidade           = excluded.modalidade,
                            tipo_contrato        = excluded.tipo_contrato,
                            salario_inicial      = excluded.salario_inicial,
                            descricao            = excluded.descricao,
                            ultima_sincronizacao = excluded.ultima_sincronizacao
                    """, _mapear(item, sync_time))
                    processadas += 1
            except Exception:
                continue

        cursor.execute(
            "DELETE FROM vagas WHERE fonte = ? AND ultima_sincronizacao < ?",
            (_FONTE, sync_time)
        )
        removidas = cursor.rowcount
        conn.commit()

    return {
        "ok":          True,
        "total_api":   total_api,
        "processadas": processadas,
        "removidas":   removidas,
        "sync_time":   sync_time,
    }
