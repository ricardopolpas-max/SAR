import asyncio
import json
import os
import ssl
import time
import threading
from pathlib import Path
from dotenv import load_dotenv
import websockets
import uuid

# Carrega variáveis de ambiente
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path, verbose=False)

# Configurações do Servidor de Integração (Ukiceker Conecta)
WS_HOST = os.getenv("UKICEKER_HOST", "127.0.0.1")
# WS_PORT agora é dinâmico, mas mantemos a exportação para compatibilidade de importação
WS_PORT = os.getenv("UKICEKER_PORT", "8765")


def _float_env(nome, padrao):
    try:
        return float(os.getenv(nome, str(padrao)))
    except Exception:
        return float(padrao)


def _int_env(nome, padrao, minimo=1):
    try:
        valor = int(os.getenv(nome, str(padrao)))
        return max(minimo, valor)
    except Exception:
        return int(padrao)


WS_OPEN_TIMEOUT = _float_env("UKICEKER_OPEN_TIMEOUT", 2.0)
WS_RESPONSE_TIMEOUT = _float_env("UKICEKER_RESPONSE_TIMEOUT", 8.0)
WS_HANDSHAKE_DELAY = max(0.0, _float_env("UKICEKER_HANDSHAKE_DELAY", 0.0))
WS_MAX_RETRIES = _int_env("UKICEKER_MAX_RETRIES", 2, minimo=1)
WS_MAX_RETRIES_DML = _int_env("UKICEKER_MAX_RETRIES_DML", 1, minimo=1)
RUNTIME_URI_TTL = max(0.0, _float_env("UKICEKER_RUNTIME_URI_TTL", 2.0))

_RUNTIME_URI_LOCK = threading.Lock()
_RUNTIME_URI_CACHE = {
    "uri": None,
    "expira_em": 0.0,
}


def _paths_runtime_candidates():
    # Possiveis locais para o src/nucleo/runtime_connection.json
    return [
        Path("D:/Projetos_VS_Code/ukiceker-conecta/src/nucleo/runtime_connection.json"),
        Path(__file__).resolve().parents[3] / "ukiceker-conecta" / "src" / "nucleo" / "runtime_connection.json",
    ]


def _ler_uri_runtime():
    host = WS_HOST
    port = WS_PORT

    for path in _paths_runtime_candidates():
        if not path.exists():
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)

            if config.get("status") == "active":
                host = config.get("host", host)
                port = config.get("port", port)
                break
        except Exception:
            # Silencioso para nao poluir logs de producao
            continue

    return f"ws://{host}:{port}"


def _obter_uri_websocket(force_refresh=False):
    """
    Tenta localizar o arquivo de runtime do Ukiceker para obter a porta dinamica.
    Caso nao encontre, utiliza as configuracoes do .env.
    """
    agora = time.monotonic()

    if not force_refresh and RUNTIME_URI_TTL > 0:
        with _RUNTIME_URI_LOCK:
            uri_cache = _RUNTIME_URI_CACHE.get("uri")
            expira_em = float(_RUNTIME_URI_CACHE.get("expira_em") or 0.0)
        if uri_cache and agora < expira_em:
            return uri_cache

    uri = _ler_uri_runtime()

    with _RUNTIME_URI_LOCK:
        _RUNTIME_URI_CACHE["uri"] = uri
        _RUNTIME_URI_CACHE["expira_em"] = agora + RUNTIME_URI_TTL

    return uri


async def _receber_json(websocket):
    resposta_raw = await asyncio.wait_for(websocket.recv(), timeout=WS_RESPONSE_TIMEOUT)
    return json.loads(resposta_raw)


def _mensagem_erro_conexao(msg):
    texto = str(msg or "").strip().lower()
    return (
        "falha de conexao" in texto
        or "timed out" in texto
        or "timeout" in texto
        or "connection" in texto
    )


async def _enviar_payload_async(payload):
    """
    Corrotina interna: Gerencia o ciclo de vida da conexao WebSocket.
    """
    uri = _obter_uri_websocket()
    try:
        async with websockets.connect(uri, open_timeout=WS_OPEN_TIMEOUT, close_timeout=1) as websocket:
            await websocket.send(json.dumps(payload))
            resposta = await _receber_json(websocket)
            if "payload" in resposta:
                return resposta["payload"]
            return resposta

    except (ConnectionRefusedError, OSError, asyncio.TimeoutError) as e:
        return {"status": "erro", "mensagem": f"Falha de conexao com Integrador ({uri}): {str(e)}"}
    except Exception as e:
        return {"status": "erro", "mensagem": f"Falha na comunicacao WebSocket: {str(e)}"}


async def _executar_transacao_com_auth_async(acao, tabela, dados, condicao=None):
    """Handshake completo v1.0: Identify -> Import -> Transaction."""
    uri = _obter_uri_websocket()
    try:
        async with websockets.connect(uri, open_timeout=WS_OPEN_TIMEOUT, close_timeout=1) as websocket:
            # 1. Identificacao
            await websocket.send(json.dumps({
                "type": "identify",
                "version": "1.0",
                "payload": {
                    "client_id": f"backend_almox_transaction_{uuid.uuid4()}",
                    "origin": "backend",
                    "app_version": "1.0.0"
                }
            }))
            resp_id = await _receber_json(websocket)

            if resp_id.get("status") == "erro":
                return resp_id

            # 2. Autenticacao no Banco (Import Request)
            db_name = os.getenv("MYSQL_DATABASE", "almox")
            await websocket.send(json.dumps({
                "type": "import_request",
                "version": "1.0",
                "payload": {
                    "banco": db_name,
                    "autocommit": True
                }
            }))
            resp_auth = await _receber_json(websocket)

            if resp_auth.get("status") == "erro":
                return resp_auth

            if WS_HANDSHAKE_DELAY > 0:
                await asyncio.sleep(WS_HANDSHAKE_DELAY)

            # 3. Execucao da Transacao
            payload_transacao = {
                "acao": acao,
                "tabela": tabela,
                "dados": dados
            }
            if condicao:
                payload_transacao["condicao"] = condicao

            payload = {
                "type": "transaction_request",
                "version": "1.0",
                "payload": payload_transacao
            }
            await websocket.send(json.dumps(payload))

            resposta = await _receber_json(websocket)

            if resposta.get("type") != "error":
                # COMMIT explicito para compatibilidade com integradores sem autocommit efetivo.
                try:
                    p_commit = {
                        "type": "transaction_request",
                        "version": "1.0",
                        "payload": {"acao": "COMMIT", "tabela": "", "dados": {}}
                    }
                    await websocket.send(json.dumps(p_commit))
                    await _receber_json(websocket)  # Ignora ack/erro do commit.
                except Exception:
                    pass

            if resposta.get("type") == "error":
                p = resposta.get("payload", {})
                return {"status": "erro", "mensagem": p.get("message") or p.get("mensagem") or "Erro no servidor"}

            if "payload" in resposta:
                return resposta["payload"]
            return resposta

    except (ConnectionRefusedError, OSError, asyncio.TimeoutError) as e:
        return {"status": "erro", "mensagem": f"Falha de conexao com Integrador ({uri}): {str(e)}"}
    except Exception as e:
        return {"status": "erro", "mensagem": f"Falha na execucao da transacao: {str(e)}"}


def executar_transacao(acao, dados=None):
    """
    Executa uma transacao no padrao Ukiceker v1.0 com handshake completo.
    """
    payload_entrada = dict(dados or {})

    # O servidor protocol.py 1.0 suporta transaction_request mas EXIGE handshake
    acoes_dml = ["inserir", "atualizar", "excluir"]

    if acao in acoes_dml:
        tabela = payload_entrada.pop("tabela", "desconhecida")
        condicao = payload_entrada.pop("condicao", None)  # Extrai condicao se existir (para UPDATE/DELETE)

        mapa_acoes = {
            "inserir": "inserir",
            "atualizar": "atualizar",
            "excluir": "excluir"
        }
        acao_protocolo = mapa_acoes.get(acao, acao.lower())

        # DML usa 1 tentativa por padrao para reduzir risco de escrita duplicada.
        for tentativa in range(WS_MAX_RETRIES_DML):
            resultado = asyncio.run(
                _executar_transacao_com_auth_async(acao_protocolo, tabela, payload_entrada, condicao)
            )
            msg = resultado.get("mensagem") if isinstance(resultado, dict) else ""

            if tentativa < (WS_MAX_RETRIES_DML - 1) and _mensagem_erro_conexao(msg):
                _obter_uri_websocket(force_refresh=True)
                continue

            return _normalizar_chaves(resultado)

        return _normalizar_chaves({"status": "erro", "mensagem": "Falha na transacao apos retentativas."})

    # Acoes legadas (ping, etc) usam o metodo antigo
    payload = {
        "type": acao,
        "version": "1.0",
        "payload": payload_entrada
    }
    for tentativa in range(WS_MAX_RETRIES):
        resultado = asyncio.run(_enviar_payload_async(payload))
        msg = resultado.get("mensagem") if isinstance(resultado, dict) else ""

        if tentativa < (WS_MAX_RETRIES - 1) and _mensagem_erro_conexao(msg):
            _obter_uri_websocket(force_refresh=True)
            continue

        return _normalizar_chaves(resultado)

    return _normalizar_chaves({"status": "erro", "mensagem": "Falha na operacao apos retentativas."})


def _normalizar_chaves(obj):
    """Converte chaves para minusculo para compatibilidade com backend."""
    if isinstance(obj, dict):
        novo_obj = {}
        for k, v in obj.items():
            novo_k = k.lower()
            novo_v = _normalizar_chaves(v)
            novo_obj[novo_k] = novo_v

        # Mapeamento Servidor -> Backend (minusculo)
        if "rows" in novo_obj and "linhas" not in novo_obj:
            novo_obj["linhas"] = novo_obj["rows"]
        if "columns" in novo_obj and "colunas" not in novo_obj:
            novo_obj["colunas"] = novo_obj["columns"]
        if "row_count" in novo_obj and "linhas_afetadas" not in novo_obj:
            novo_obj["linhas_afetadas"] = novo_obj["row_count"]

        return novo_obj
    if isinstance(obj, list):
        return [_normalizar_chaves(item) for item in obj]
    return obj


async def _executar_query_com_auth_async(sql, params):
    """Handshake completo v1.0: Identify -> Import -> Query."""
    uri = _obter_uri_websocket()
    try:
        async with websockets.connect(uri, open_timeout=WS_OPEN_TIMEOUT, close_timeout=1) as websocket:
            # 1. Identificacao
            await websocket.send(json.dumps({
                "type": "identify",
                "version": "1.0",
                "payload": {
                    "client_id": f"backend_almox_query_{uuid.uuid4()}",
                    "origin": "backend",
                    "app_version": "1.0.0"
                }
            }))
            resp_id = await _receber_json(websocket)

            if resp_id.get("status") == "erro":
                return resp_id

            # 2. Autenticacao no Banco (Import Request)
            db_name = os.getenv("MYSQL_DATABASE", "almox")
            await websocket.send(json.dumps({
                "type": "import_request",
                "version": "1.0",
                "payload": {
                    "banco": db_name,
                    "autocommit": True
                }
            }))
            resp_auth = await _receber_json(websocket)

            if resp_auth.get("status") == "erro":
                return resp_auth

            if WS_HANDSHAKE_DELAY > 0:
                await asyncio.sleep(WS_HANDSHAKE_DELAY)

            # 3. Execucao da Query
            payload = {
                "type": "query_request",
                "version": "1.0",
                "payload": {
                    "sql": sql,
                    "params": params
                }
            }
            await websocket.send(json.dumps(payload))

            resposta = await _receber_json(websocket)

            if resposta.get("type") == "error":
                p = resposta.get("payload", {})
                return {"status": "erro", "mensagem": p.get("message") or p.get("mensagem") or "Erro no servidor"}

            if "payload" in resposta:
                return resposta["payload"]
            return resposta

    except (ConnectionRefusedError, OSError, asyncio.TimeoutError) as e:
        return {"status": "erro", "mensagem": f"Falha de conexao com Integrador ({uri}): {str(e)}"}
    except Exception as e:
        return {"status": "erro", "mensagem": f"Falha na execucao da query: {str(e)}"}


def executar_consulta(sql, params=None):
    """Executa consulta SQL via v1.1 com retry em caso de falha de auth/conexao."""
    if params is None:
        params = []

    for tentativa in range(WS_MAX_RETRIES):
        resultado = asyncio.run(_executar_query_com_auth_async(sql, params))

        if not isinstance(resultado, dict):
            return _normalizar_chaves(resultado)

        mensagem = str(resultado.get("mensagem") or "")
        if resultado.get("status") == "erro" and "import_request" in mensagem:
            _obter_uri_websocket(force_refresh=True)
            continue

        if resultado.get("status") == "erro" and _mensagem_erro_conexao(mensagem):
            if tentativa < (WS_MAX_RETRIES - 1):
                _obter_uri_websocket(force_refresh=True)
                continue

        return _normalizar_chaves(resultado)

    return _normalizar_chaves({"status": "erro", "mensagem": "Falha na consulta apos retentativas."})


def testar_conexao_integracao():
    """Verifica se o servidor esta online."""
    resp = executar_transacao("ping")
    if not isinstance(resp, dict):
        return False
    status = str(resp.get("status") or resp.get("STATUS") or "").strip().lower()
    return status != "erro"
