# backend/servidor.py
# Orquestrador central do SAR.
# Ponto de entrada único — nunca iniciar pelo Uvicorn diretamente.
# Fluxo: expiração → instalacao.dat → Drive → .env → api.js → SSL → servidor

import os
import re
import sys
import signal
import socket
import tempfile
import threading
import time
import webbrowser
import urllib.request
import uvicorn
from datetime import date
from dotenv import load_dotenv, set_key
from aplicacao import app

# ------------------------------------------------------------
# 0. TRAVA DE EXPIRAÇÃO
# ------------------------------------------------------------
if date.today() > date(2026, 6, 30):
    print("[SAR] Esta versão expirou em 30/06/2026. Contate o desenvolvedor.")
    sys.exit(1)

# ------------------------------------------------------------
# 1. LEITURA DO INSTALACAO.DAT — URLs do Drive compartilhado
# ------------------------------------------------------------
_APPDATA  = os.environ.get("APPDATA", "")
_DAT_PATH = os.path.join(_APPDATA, "SAR", "instalacao.dat")

_URL_ENV = ""
_URL_KEY = ""

if os.path.isfile(_DAT_PATH):
    with open(_DAT_PATH, "r", encoding="utf-8") as _f:
        _linhas = [l.strip() for l in _f.readlines() if l.strip()]
    if len(_linhas) >= 2:
        _URL_ENV = _linhas[0]
        _URL_KEY = _linhas[1]

# ------------------------------------------------------------
# 2. DOWNLOAD EM MEMÓRIA — .env e sar.key do Drive
# ------------------------------------------------------------
_ENV_TEMP  = None
_KEY_TEMP  = None

def _baixar(url: str, sufixo: str) -> str:
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            conteudo = r.read()
        fd, caminho = tempfile.mkstemp(suffix=sufixo)
        with os.fdopen(fd, "wb") as f:
            f.write(conteudo)
        return caminho
    except Exception as e:
        print(f"[ERRO] Falha ao baixar {sufixo}: {e}")
        return ""

if _URL_ENV and _URL_KEY:
    print("[SAR] Carregando configuração remota...")
    _ENV_TEMP = _baixar(_URL_ENV, ".env")
    _KEY_TEMP = _baixar(_URL_KEY, ".key")
    if not _ENV_TEMP or not _KEY_TEMP:
        print("[BLOQUEIO] Não foi possível acessar a configuração remota.")
        print("[AÇÃO] Verifique sua conexão com a internet e tente novamente.")
        sys.exit(1)
    print("[SAR] Configuração remota carregada.")

# ------------------------------------------------------------
# CAMINHOS
# ------------------------------------------------------------
_FROZEN = getattr(sys, "frozen", False)

def _raiz():
    if _FROZEN:
        return sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

RAIZ        = _raiz()
ENV_PATH    = _ENV_TEMP if _ENV_TEMP else os.path.join(RAIZ, ".env")
API_JS_PATH = os.path.join(RAIZ, "integracao", "rotas", "api.js")
PID_PATH    = os.path.join(os.environ.get("APPDATA", ""), "SAR", "sar.pid") if _FROZEN else os.path.join(RAIZ, "sar.pid")

load_dotenv(ENV_PATH)

HOST          = os.getenv("HOST", "127.0.0.1")
PORTA_DEFAULT = int(os.getenv("PORTA_DEFAULT", "8000"))
SSL_CERTFILE  = os.path.join(RAIZ, "certificado", "publico", "sar.crt") if _FROZEN else os.path.join(RAIZ, os.getenv("SSL_CERTFILE", ""))
SSL_KEYFILE   = _KEY_TEMP if _KEY_TEMP else os.path.join(RAIZ, os.getenv("SSL_KEYFILE", ""))

# ------------------------------------------------------------
# 1. CAPTURA DE PORTA INTELIGENTE
# ------------------------------------------------------------
def _porta_livre(porta: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, porta))
            return True
        except OSError:
            return False

def encontrar_porta() -> int:
    porta = PORTA_DEFAULT
    while not _porta_livre(porta):
        print(f"[SAR] Porta {porta} ocupada — tentando {porta + 1}...")
        porta += 1
    return porta

# ------------------------------------------------------------
# 2. GRAVAÇÃO DA PORTA ATUAL NO .ENV
# ------------------------------------------------------------
def gravar_porta_atual(porta: int):
    set_key(ENV_PATH, "PORTA_ATUAL", str(porta))
    print(f"[SAR] PORTA_ATUAL={porta} gravada no .env")

# ------------------------------------------------------------
# 3. ATUALIZAÇÃO DA BASE_URL NO API.JS
# ------------------------------------------------------------
def atualizar_api_js(porta: int):
    with open(API_JS_PATH, "r", encoding="utf-8") as f:
        conteudo = f.read()

    novo_conteudo = re.sub(
        r'const BASE_URL\s*=\s*["\']https?://[^"\']+["\'];',
        f'const BASE_URL = "https://{HOST}:{porta}";',
        conteudo
    )

    with open(API_JS_PATH, "w", encoding="utf-8") as f:
        f.write(novo_conteudo)

    print(f"[SAR] BASE_URL atualizada em api.js → https://{HOST}:{porta}")

# ------------------------------------------------------------
# 4. GERENCIAMENTO DE PID — previne instâncias fantasmas
# ------------------------------------------------------------
def encerrar_instancia_anterior():
    if not os.path.isfile(PID_PATH):
        return
    try:
        with open(PID_PATH, "r") as f:
            pid_anterior = int(f.read().strip())
        os.kill(pid_anterior, signal.SIGTERM)
        print(f"[SAR] Instância anterior (PID {pid_anterior}) encerrada.")
    except (ProcessLookupError, PermissionError, ValueError, OSError):
        pass
    finally:
        os.remove(PID_PATH)

def gravar_pid():
    with open(PID_PATH, "w") as f:
        f.write(str(os.getpid()))
    print(f"[SAR] PID {os.getpid()} gravado.")

def remover_pid():
    if os.path.isfile(PID_PATH):
        os.remove(PID_PATH)
        print("[SAR] PID removido.")

# ------------------------------------------------------------
# 5. VALIDAÇÃO DE CERTIFICADOS SSL
# ------------------------------------------------------------
def validar_certificados():
    erros = []
    if not os.path.isfile(SSL_CERTFILE):
        erros.append(f"Certificado público não encontrado: {SSL_CERTFILE}")
    if not os.path.isfile(SSL_KEYFILE):
        erros.append(f"Chave privada não encontrada: {SSL_KEYFILE}")
    if erros:
        for erro in erros:
            print(f"[ERRO] {erro}")
        print("[BLOQUEIO] Servidor não pode ser iniciado sem certificado SSL válido.")
        print("[AÇÃO] mkcert -cert-file certificado/publico/sar.crt "
              "-key-file certificado/privado/sar.key localhost 127.0.0.1")
        sys.exit(1)

# ------------------------------------------------------------
# 6. INICIALIZAÇÃO
# ------------------------------------------------------------
if __name__ == "__main__":

    encerrar_instancia_anterior()
    porta_atual = encontrar_porta()
    if not _FROZEN:
        gravar_porta_atual(porta_atual)
        atualizar_api_js(porta_atual)
    validar_certificados()
    gravar_pid()

    print(f"[SAR] Servidor seguro em https://{HOST}:{porta_atual}")
    print(f"[SAR] Certificado: {SSL_CERTFILE}")
    print(f"[SAR] Pressione Ctrl+C para encerrar.\n")

    if _FROZEN:
        def _abrir_browser():
            time.sleep(2)
            webbrowser.open(f"https://{HOST}:{porta_atual}/login")
        threading.Thread(target=_abrir_browser, daemon=True).start()

    try:
        uvicorn.run(
            app,
            host=HOST,
            port=porta_atual,
            ssl_certfile=SSL_CERTFILE,
            ssl_keyfile=SSL_KEYFILE,
        )
    finally:
        remover_pid()
        for _tmp in [_ENV_TEMP, _KEY_TEMP]:
            if _tmp and os.path.isfile(_tmp):
                os.remove(_tmp)
