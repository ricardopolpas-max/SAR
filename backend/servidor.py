# backend/servidor.py
# Orquestrador central do SAR.
# Ponto de entrada único — nunca iniciar pelo Uvicorn diretamente.
# Fluxo: porta → .env → api.js → SSL → servidor → shutdown limpo

import os
import re
import sys
import socket
import atexit
import subprocess
import uvicorn
from dotenv import load_dotenv, set_key

# ------------------------------------------------------------
# CAMINHOS
# ------------------------------------------------------------
RAIZ        = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH    = os.path.join(RAIZ, ".env")
API_JS_PATH = os.path.join(RAIZ, "integracao", "rotas", "api.js")

load_dotenv(ENV_PATH)

HOST          = os.getenv("HOST", "127.0.0.1")
PORTA_DEFAULT = int(os.getenv("PORTA_DEFAULT", "8000"))
SSL_CERTFILE  = os.path.join(RAIZ, os.getenv("SSL_CERTFILE", ""))
SSL_KEYFILE   = os.path.join(RAIZ, os.getenv("SSL_KEYFILE", ""))

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
# 4. VALIDAÇÃO DE CERTIFICADOS SSL
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
# 5. SHUTDOWN LIMPO — LIBERA PORTA NO WINDOWS
# ------------------------------------------------------------
def liberar_porta(porta: int):
    try:
        resultado = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True
        )
        for linha in resultado.stdout.split("\n"):
            partes = linha.split()
            if len(partes) >= 5 and f":{porta}" in partes[1] and "LISTENING" in linha:
                pid = partes[-1]
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
        print(f"[SAR] Porta {porta} liberada.")
    except Exception as e:
        print(f"[AVISO] Liberação de porta: {e}")

# ------------------------------------------------------------
# INICIALIZAÇÃO
# ------------------------------------------------------------
if __name__ == "__main__":

    porta_atual = encontrar_porta()
    gravar_porta_atual(porta_atual)
    atualizar_api_js(porta_atual)
    validar_certificados()

    atexit.register(liberar_porta, porta_atual)

    print(f"[SAR] Servidor seguro em https://{HOST}:{porta_atual}")
    print(f"[SAR] Certificado: {SSL_CERTFILE}")
    print(f"[SAR] Pressione Ctrl+C para encerrar.\n")

    uvicorn.run(
        "interface_backend:app",
        host=HOST,
        port=porta_atual,
        ssl_certfile=SSL_CERTFILE,
        ssl_keyfile=SSL_KEYFILE,
    )
