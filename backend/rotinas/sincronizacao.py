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

_MAPA_MODALIDADE = {
    "remota":   "remoto",
    "ambos":    "hibrido",
}

_MAPA_CONTRATO = {
    "pessoajuridica": "pj",
}

def _normalizar(valor: str, mapa: dict) -> str:
    v = (valor or "").strip().lower()
    return mapa.get(v, v)

def _mapear(item: dict, sync_time: str) -> dict:
    salario = item.get("startingSalaryInCents")
    return {
        "titulo":                item.get("name", ""),
        "empresa":               item.get("companyName", ""),
        "link":                  item.get("publicUrl", ""),
        "localizacao":           item.get("location", ""),
        "modalidade":            _normalizar(item.get("modality",       ""), _MAPA_MODALIDADE),
        "tipo_contrato":         _normalizar(item.get("contractType",   ""), _MAPA_CONTRATO),
        "salario_inicial":       salario if isinstance(salario, int) else None,
        "descricao":             item.get("requisites", ""),
        "id_externo":            item.get("_id", ""),
        "fonte":                 _FONTE,
        "data_extracao":         item.get("createdAt", sync_time),
        "ultima_sincronizacao":  sync_time,
        "disponivel_plataforma": 1,
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
            except Exception as e:
                print(f"[SYNC] Erro na página {num}: {e}")
                continue

            for item in pagina.get("data", []):
                vaga = _mapear(item, sync_time)
                if not vaga["id_externo"]:
                    continue
                try:
                    cursor.execute("""
                        UPDATE vagas SET
                            titulo               = :titulo,
                            empresa              = :empresa,
                            link                 = :link,
                            localizacao          = :localizacao,
                            modalidade           = :modalidade,
                            tipo_contrato        = :tipo_contrato,
                            salario_inicial      = :salario_inicial,
                            descricao            = :descricao,
                            ultima_sincronizacao = :ultima_sincronizacao,
                            disponivel_plataforma = 1
                        WHERE id_externo = :id_externo
                    """, vaga)
                    if cursor.rowcount == 0:
                        cursor.execute("""
                            INSERT INTO vagas
                                (titulo, empresa, link, localizacao, modalidade,
                                 tipo_contrato, salario_inicial, descricao,
                                 id_externo, fonte, data_extracao,
                                 ultima_sincronizacao, disponivel_plataforma)
                            VALUES
                                (:titulo, :empresa, :link, :localizacao, :modalidade,
                                 :tipo_contrato, :salario_inicial, :descricao,
                                 :id_externo, :fonte, :data_extracao,
                                 :ultima_sincronizacao, :disponivel_plataforma)
                        """, vaga)
                    processadas += 1
                except Exception as e:
                    print(f"[SYNC] Erro ao salvar vaga {vaga['id_externo']}: {e}")

        # Marca como indisponível vagas que sumiram do Peixe 30.
        # Nunca deleta — candidato pode ter progresso vinculado.
        # Vagas com status != PENDENTE continuam visíveis mesmo indisponíveis.
        cursor.execute("""
            UPDATE vagas
            SET disponivel_plataforma = 0
            WHERE fonte = ?
              AND ultima_sincronizacao < ?
              AND (status IS NULL OR status = 'PENDENTE')
        """, (_FONTE, sync_time))
        indisponiveis = cursor.rowcount
        conn.commit()

    return {
        "ok":           True,
        "total_api":    total_api,
        "processadas":  processadas,
        "indisponiveis": indisponiveis,
        "sync_time":    sync_time,
    }
