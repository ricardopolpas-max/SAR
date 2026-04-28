# backend/servidor.py
# Orquestrador central do SAR.
# Ponto de entrada único do sistema — nunca iniciar pelo Uvicorn diretamente.
# Carrega variáveis de ambiente, valida certificados SSL e sobe o servidor.

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Resolve o .env a partir da raiz do projeto (um nível acima de /backend)
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(RAIZ, ".env"))

SSL_CERTFILE = os.path.join(RAIZ, os.getenv("SSL_CERTFILE", ""))
SSL_KEYFILE  = os.path.join(RAIZ, os.getenv("SSL_KEYFILE", ""))
HOST         = os.getenv("HOST", "127.0.0.1")
PORT         = int(os.getenv("PORT", "8000"))

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
        print("[AÇÃO] Execute: mkcert -cert-file certificado/publico/sar.crt -key-file certificado/privado/sar.key localhost 127.0.0.1")
        sys.exit(1)

if __name__ == "__main__":
    validar_certificados()

    print(f"[SAR] Iniciando servidor seguro em https://{HOST}:{PORT}")
    print(f"[SAR] Certificado: {SSL_CERTFILE}")

    uvicorn.run(
        "interface_backend:app",
        host=HOST,
        port=PORT,
        ssl_certfile=SSL_CERTFILE,
        ssl_keyfile=SSL_KEYFILE,
        reload=True,
    )
