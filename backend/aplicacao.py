from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timezone
import sqlite3
import json
import os

from rotinas.genericas import DB_PATH, db_selecionar, db_inserir, db_atualizar, db_excluir
from rotinas.sincronizacao import sincronizar
from rotinas.autenticacao import (
    hash_senha, verificar_senha, criar_token, validar_token, revogar_token
)

RAIZ              = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PASTA_FRONTEND    = os.path.join(RAIZ, "frontend")
PASTA_INTEGRACAO  = os.path.join(RAIZ, "integracao")
SAR_HTML          = os.path.join(PASTA_FRONTEND, "telas", "SAR.html")
TELA_ACESSO_HTML  = os.path.join(PASTA_FRONTEND, "telas", "login.html")
TELA_CADASTRO_HTML = os.path.join(PASTA_FRONTEND, "telas", "cadastro.html")

app = FastAPI(title="SAR - Sistema de Automação de Recolocação")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend",   StaticFiles(directory=PASTA_FRONTEND),   name="frontend")
app.mount("/integracao", StaticFiles(directory=PASTA_INTEGRACAO), name="integracao")

# ------------------------------------------------------------
# BANCO DE DADOS — inicialização e migrações
# ------------------------------------------------------------
@app.on_event("startup")
def inicializar_banco():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave     TEXT PRIMARY KEY,
                valor     TEXT,
                tipo      TEXT DEFAULT 'string',
                descricao TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vagas (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo               TEXT NOT NULL,
                empresa              TEXT,
                link                 TEXT UNIQUE,
                localizacao          TEXT,
                modalidade           TEXT,
                tipo_contrato        TEXT,
                salario_inicial      INTEGER,
                descricao            TEXT,
                id_externo           TEXT UNIQUE,
                fonte                TEXT DEFAULT 'peixe30',
                data_extracao        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultima_sincronizacao TIMESTAMP,
                score                REAL DEFAULT 0.0,
                status               TEXT DEFAULT 'PENDENTE'
            )
        """)

        cursor.execute("PRAGMA table_info(vagas)")
        colunas = {row[1] for row in cursor.fetchall()}
        for coluna, tipo in [
            ("localizacao",            "TEXT"),
            ("modalidade",             "TEXT"),
            ("tipo_contrato",          "TEXT"),
            ("salario_inicial",        "INTEGER"),
            ("descricao",              "TEXT"),
            ("id_externo",             "TEXT"),
            ("fonte",                  "TEXT DEFAULT 'peixe30'"),
            ("ultima_sincronizacao",   "TIMESTAMP"),
            ("disponivel_plataforma",  "INTEGER DEFAULT 1"),
        ]:
            if coluna not in colunas:
                cursor.execute(f"ALTER TABLE vagas ADD COLUMN {coluna} {tipo}")

        try:
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_vagas_id_externo
                ON vagas(id_externo) WHERE id_externo IS NOT NULL
            """)
        except Exception:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs_sistema (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                momento  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acao     TEXT NOT NULL,
                detalhes TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidatos (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                nome          TEXT NOT NULL,
                email         TEXT UNIQUE NOT NULL,
                senha_hash    TEXT NOT NULL,
                status        TEXT DEFAULT 'ATIVO',
                criado_em     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultimo_acesso TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessoes (
                token        TEXT PRIMARY KEY,
                id_candidato INTEGER NOT NULL,
                criado_em    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expira_em    TIMESTAMP NOT NULL,
                FOREIGN KEY (id_candidato) REFERENCES candidatos(id) ON DELETE CASCADE
            )
        """)

        # Normaliza valores legados da API Peixe 30 já gravados no banco
        cursor.execute("UPDATE vagas SET modalidade    = 'remoto'  WHERE modalidade    = 'remota'")
        cursor.execute("UPDATE vagas SET modalidade    = 'hibrido' WHERE modalidade    = 'ambos'")
        cursor.execute("UPDATE vagas SET tipo_contrato = 'pj'      WHERE tipo_contrato = 'pessoajuridica'")

        conn.commit()

# ------------------------------------------------------------
# AUTENTICAÇÃO — dependency injetada nas rotas protegidas
# ------------------------------------------------------------
async def autenticar(authorization: str = Header(None)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autorizado.")
    id_candidato = validar_token(authorization[7:])
    if not id_candidato:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")
    return id_candidato


# ------------------------------------------------------------
# ÍCONE E RAIZ
# ------------------------------------------------------------
_ICONE_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
    "<rect width='32' height='32' rx='8' fill='#2d65e0'/>"
    "<text x='50%' y='54%' dominant-baseline='middle' text-anchor='middle' "
    "font-family='system-ui,sans-serif' font-weight='700' font-size='14' fill='#e8f0ff'>SAR</text>"
    "</svg>"
)

@app.get("/favicon.ico", include_in_schema=False)
async def icone_sistema():
    return Response(content=_ICONE_SVG, media_type="image/svg+xml")

@app.get("/")
async def raiz():
    return {"projeto": "SAR", "status": "operacional"}

# ------------------------------------------------------------
# TELAS — rotas públicas de navegação
# ------------------------------------------------------------
@app.get("/login", include_in_schema=False)
async def tela_acesso():
    return FileResponse(TELA_ACESSO_HTML)

@app.get("/cadastrar", include_in_schema=False)
async def tela_cadastrar():
    return FileResponse(TELA_CADASTRO_HTML)

@app.get("/sar", include_in_schema=False)
async def tela_principal():
    return FileResponse(SAR_HTML)

# ------------------------------------------------------------
# AUTENTICAÇÃO — endpoints públicos
# ------------------------------------------------------------
@app.post("/auth/cadastrar")
async def cadastrar(dados: dict):
    nome  = (dados.get("nome")  or "").strip()
    email = (dados.get("email") or "").strip().lower()
    senha = (dados.get("senha") or "")
    if not nome or not email or not senha:
        raise HTTPException(400, "Nome, e-mail e senha são obrigatórios.")
    if db_selecionar("candidatos", condicao={"email": email}, unico=True):
        raise HTTPException(409, "E-mail já cadastrado.")
    resultado = db_inserir("candidatos", {
        "nome": nome, "email": email, "senha_hash": hash_senha(senha),
    })
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    token = criar_token(resultado["id"])
    return {"token": token, "nome": nome}

@app.post("/auth/login")
async def entrar(dados: dict):
    email = (dados.get("email") or "").strip().lower()
    senha = (dados.get("senha") or "")
    candidato = db_selecionar("candidatos", condicao={"email": email}, unico=True)
    if not candidato or not verificar_senha(senha, candidato["senha_hash"]):
        raise HTTPException(401, "E-mail ou senha incorretos.")
    if candidato["status"] != "ATIVO":
        raise HTTPException(403, "Conta inativa.")
    db_atualizar("candidatos",
                 {"ultimo_acesso": datetime.now(timezone.utc).isoformat()},
                 {"id": candidato["id"]})
    token = criar_token(candidato["id"])
    return {"token": token, "nome": candidato["nome"]}

@app.post("/auth/logout")
async def encerrar_sessao(
    id_candidato: int = Depends(autenticar),
    authorization: str = Header(None),
):
    revogar_token(authorization[7:])
    return {"mensagem": "Sessão encerrada."}

# ------------------------------------------------------------
# PERFIL DO CANDIDATO AUTENTICADO
# ------------------------------------------------------------
@app.get("/candidatos/meu-perfil")
async def meu_perfil(id_candidato: int = Depends(autenticar)):
    candidato = db_selecionar("candidatos", condicao={"id": id_candidato}, unico=True)
    if not candidato:
        raise HTTPException(404, "Candidato não encontrado.")
    return {"nome": candidato["nome"], "email": candidato["email"]}

# ------------------------------------------------------------
# VAGAS — protegidas
# ------------------------------------------------------------
@app.get("/vagas")
async def listar_vagas(id_candidato: int = Depends(autenticar)):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM vagas
            WHERE disponivel_plataforma = 1
               OR (status IS NOT NULL AND status != 'PENDENTE')
            ORDER BY ultima_sincronizacao DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

@app.post("/vagas/sincronizar")
async def sincronizar_vagas(id_candidato: int = Depends(autenticar)):
    resultado = sincronizar()
    if not resultado["ok"]:
        raise HTTPException(500, resultado["erro"])
    print(f"[SAR] Sync concluído — {resultado['processadas']} vagas, "
          f"{resultado['indisponiveis']} indisponíveis.")
    return resultado

@app.get("/vagas/{id}")
async def buscar_vaga(id: int, id_candidato: int = Depends(autenticar)):
    vaga = db_selecionar("vagas", condicao={"id": id}, unico=True)
    if not vaga:
        raise HTTPException(404, "Vaga não encontrada.")
    return vaga

@app.post("/vagas")
async def criar_vaga(dados: dict, id_candidato: int = Depends(autenticar)):
    resultado = db_inserir("vagas", dados)
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

@app.put("/vagas/{id}")
async def atualizar_vaga(id: int, dados: dict, id_candidato: int = Depends(autenticar)):
    resultado = db_atualizar("vagas", dados, {"id": id})
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

@app.delete("/vagas/{id}")
async def remover_vaga(id: int, id_candidato: int = Depends(autenticar)):
    resultado = db_excluir("vagas", {"id": id})
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

# ------------------------------------------------------------
# CONFIGURAÇÕES — protegidas
# ------------------------------------------------------------
@app.get("/configuracoes")
async def listar_configuracoes(id_candidato: int = Depends(autenticar)):
    return db_selecionar("configuracoes")

@app.get("/configuracoes/{chave}")
async def buscar_configuracao(chave: str, id_candidato: int = Depends(autenticar)):
    cfg = db_selecionar("configuracoes", condicao={"chave": chave}, unico=True)
    if not cfg:
        raise HTTPException(404, "Configuração não encontrada.")
    return cfg

@app.post("/configuracoes")
async def salvar_configuracao(dados: dict, id_candidato: int = Depends(autenticar)):
    chave = dados.get("chave")
    valor = dados.get("valor")
    if not chave:
        raise HTTPException(400, "Campo 'chave' obrigatório.")
    if db_selecionar("configuracoes", condicao={"chave": chave}, unico=True):
        return db_atualizar("configuracoes", {"valor": valor}, {"chave": chave})
    return db_inserir("configuracoes", {"chave": chave, "valor": valor})

# ------------------------------------------------------------
# REGISTROS DO SISTEMA — protegidos
# ------------------------------------------------------------
@app.get("/logs")
async def listar_registros(limite: int = 50, id_candidato: int = Depends(autenticar)):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM logs_sistema ORDER BY momento DESC LIMIT ?", (limite,)
        )
        return [dict(row) for row in cursor.fetchall()]
