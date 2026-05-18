from fastapi import FastAPI, Depends, Header, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timezone
import asyncio
import sqlite3
import json
import os
import shutil

import sys
from rotinas.genericas import DB_PATH, _obter_conexao, db_selecionar, db_inserir, db_atualizar, db_excluir
from rotinas.sincronizacao import sincronizar
from rotinas.autenticacao import (
    hash_senha, verificar_senha, criar_token, validar_token, revogar_token
)

def _raiz():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

RAIZ              = _raiz()
PASTA_FRONTEND    = os.path.join(RAIZ, "frontend")
PASTA_INTEGRACAO  = os.path.join(RAIZ, "integracao")
PASTA_UPLOADS     = os.path.join(RAIZ, "apoio", "uploads")
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

class _SemCache(StaticFiles):
    async def get_response(self, path, scope):
        resposta = await super().get_response(path, scope)
        resposta.headers["Cache-Control"] = "no-store"
        return resposta

app.mount("/frontend",   _SemCache(directory=PASTA_FRONTEND),   name="frontend")
app.mount("/integracao", _SemCache(directory=PASTA_INTEGRACAO), name="integracao")

# ------------------------------------------------------------
# LOOP — suprime ConnectionResetError (ruído Windows/ProactorEventLoop)
# ------------------------------------------------------------
@app.on_event("startup")
async def _suprimir_ruido_windows():
    def _handler(loop, context):
        if isinstance(context.get("exception"), ConnectionResetError):
            return
        loop.default_exception_handler(context)
    asyncio.get_running_loop().set_exception_handler(_handler)

# ------------------------------------------------------------
# BANCO DE DADOS — inicialização e migrações
# ------------------------------------------------------------
@app.on_event("startup")
def inicializar_banco():
    with _obter_conexao() as conn:
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

        # ─────────────────────────────────────────────────────────
        # MOTOR 3 — Perfil do Candidato (8 tabelas filhas)
        # ─────────────────────────────────────────────────────────

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS perfil_candidato (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                id_candidato         INTEGER NOT NULL UNIQUE,
                tipo_importacao      TEXT,
                arquivo_nome         TEXT,
                resumo_profissional  TEXT,
                localizacao          TEXT,
                disponibilidade      TEXT,
                pretensao_salarial   INTEGER DEFAULT 0,
                data_atualizacao     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_candidato) REFERENCES candidatos(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiencias (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                id_candidato     INTEGER NOT NULL,
                cargo            TEXT NOT NULL,
                empresa          TEXT NOT NULL,
                data_inicio      DATE,
                data_fim         DATE,
                em_atual         INTEGER DEFAULT 0,
                descricao        TEXT,
                responsabilidades TEXT,
                FOREIGN KEY (id_candidato) REFERENCES candidatos(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS formacoes (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                id_candidato     INTEGER NOT NULL,
                instituicao      TEXT NOT NULL,
                curso            TEXT NOT NULL,
                nivel            TEXT NOT NULL,
                data_inicio      DATE,
                data_conclusao   DATE,
                em_progresso     INTEGER DEFAULT 0,
                FOREIGN KEY (id_candidato) REFERENCES candidatos(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habilidades (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                id_candidato     INTEGER NOT NULL,
                nome             TEXT NOT NULL,
                proficiencia     TEXT NOT NULL,
                categoria        TEXT,
                FOREIGN KEY (id_candidato) REFERENCES candidatos(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS idiomas (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                id_candidato     INTEGER NOT NULL,
                nome             TEXT NOT NULL,
                proficiencia     TEXT NOT NULL,
                FOREIGN KEY (id_candidato) REFERENCES candidatos(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certificacoes (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                id_candidato     INTEGER NOT NULL,
                nome             TEXT NOT NULL,
                emissor          TEXT NOT NULL,
                data_emissao     DATE,
                data_expiracao   DATE,
                url              TEXT,
                FOREIGN KEY (id_candidato) REFERENCES candidatos(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documentos (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                id_candidato     INTEGER NOT NULL,
                tipo             TEXT NOT NULL,
                nome_arquivo     TEXT NOT NULL,
                caminho_disco    TEXT NOT NULL,
                data_upload      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_candidato) REFERENCES candidatos(id) ON DELETE CASCADE
            )
        """)

        try:
            cursor.execute("ALTER TABLE documentos ADD COLUMN descricao TEXT")
        except Exception:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contatos (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                id_candidato     INTEGER NOT NULL UNIQUE,
                telefone         TEXT,
                linkedin         TEXT,
                github           TEXT,
                website          TEXT,
                FOREIGN KEY (id_candidato) REFERENCES candidatos(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversas (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                id_candidato   INTEGER NOT NULL,
                id_vaga        INTEGER NOT NULL,
                historico      TEXT NOT NULL DEFAULT '[]',
                score_estimado REAL DEFAULT 0,
                status         TEXT DEFAULT 'em_andamento',
                criado_em      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(id_candidato, id_vaga),
                FOREIGN KEY (id_candidato) REFERENCES candidatos(id) ON DELETE CASCADE,
                FOREIGN KEY (id_vaga)      REFERENCES vagas(id)      ON DELETE CASCADE
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
# PERFIL DO CANDIDATO — Motor 3
# ------------------------------------------------------------
@app.get("/perfil-candidato")
async def carregar_perfil(id_candidato: int = Depends(autenticar)):
    perfil = db_selecionar("perfil_candidato", condicao={"id_candidato": id_candidato}, unico=True)
    if not perfil:
        return {"ok": True, "dados": None}
    return {"ok": True, "dados": perfil}

@app.get("/perfil-candidato/completo")
async def carregar_perfil_completo(id_candidato: int = Depends(autenticar)):
    perfil = db_selecionar("perfil_candidato", condicao={"id_candidato": id_candidato}, unico=True)

    experiencias = db_selecionar("experiencias", condicao={"id_candidato": id_candidato}) or []
    formacoes = db_selecionar("formacoes", condicao={"id_candidato": id_candidato}) or []
    habilidades = db_selecionar("habilidades", condicao={"id_candidato": id_candidato}) or []
    idiomas = db_selecionar("idiomas", condicao={"id_candidato": id_candidato}) or []
    certificacoes = db_selecionar("certificacoes", condicao={"id_candidato": id_candidato}) or []
    documentos = db_selecionar("documentos", condicao={"id_candidato": id_candidato}) or []
    contatos = db_selecionar("contatos", condicao={"id_candidato": id_candidato}, unico=True)

    return {
        "perfil": perfil,
        "experiencias": experiencias,
        "formacoes": formacoes,
        "habilidades": habilidades,
        "idiomas": idiomas,
        "certificacoes": certificacoes,
        "documentos": documentos,
        "contatos": contatos,
    }

# ─────────────────────────────────────────────────────────
# EXPERIÊNCIAS
# ─────────────────────────────────────────────────────────
@app.post("/perfil-candidato/experiencias")
async def criar_experiencia(dados: dict, id_candidato: int = Depends(autenticar)):
    cargo = (dados.get("cargo") or "").strip()
    empresa = (dados.get("empresa") or "").strip()
    if not cargo or not empresa:
        raise HTTPException(400, "Cargo e empresa são obrigatórios.")
    dados["id_candidato"] = id_candidato
    resultado = db_inserir("experiencias", dados)
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

@app.put("/perfil-candidato/experiencias/{id}")
async def atualizar_experiencia(id: int, dados: dict, id_candidato: int = Depends(autenticar)):
    exp = db_selecionar("experiencias", condicao={"id": id, "id_candidato": id_candidato}, unico=True)
    if not exp:
        raise HTTPException(404, "Experiência não encontrada.")
    resultado = db_atualizar("experiencias", dados, {"id": id})
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

@app.delete("/perfil-candidato/experiencias/{id}")
async def remover_experiencia(id: int, id_candidato: int = Depends(autenticar)):
    exp = db_selecionar("experiencias", condicao={"id": id, "id_candidato": id_candidato}, unico=True)
    if not exp:
        raise HTTPException(404, "Experiência não encontrada.")
    resultado = db_excluir("experiencias", {"id": id})
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

# ─────────────────────────────────────────────────────────
# FORMAÇÕES
# ─────────────────────────────────────────────────────────
@app.post("/perfil-candidato/formacoes")
async def criar_formacao(dados: dict, id_candidato: int = Depends(autenticar)):
    instituicao = (dados.get("instituicao") or "").strip()
    curso = (dados.get("curso") or "").strip()
    nivel = (dados.get("nivel") or "").strip()
    if not instituicao or not curso or not nivel:
        raise HTTPException(400, "Instituição, curso e nível são obrigatórios.")
    dados["id_candidato"] = id_candidato
    resultado = db_inserir("formacoes", dados)
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

@app.put("/perfil-candidato/formacoes/{id}")
async def atualizar_formacao(id: int, dados: dict, id_candidato: int = Depends(autenticar)):
    form = db_selecionar("formacoes", condicao={"id": id, "id_candidato": id_candidato}, unico=True)
    if not form:
        raise HTTPException(404, "Formação não encontrada.")
    resultado = db_atualizar("formacoes", dados, {"id": id})
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

@app.delete("/perfil-candidato/formacoes/{id}")
async def remover_formacao(id: int, id_candidato: int = Depends(autenticar)):
    form = db_selecionar("formacoes", condicao={"id": id, "id_candidato": id_candidato}, unico=True)
    if not form:
        raise HTTPException(404, "Formação não encontrada.")
    resultado = db_excluir("formacoes", {"id": id})
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

# ─────────────────────────────────────────────────────────
# HABILIDADES
# ─────────────────────────────────────────────────────────
@app.post("/perfil-candidato/habilidades")
async def criar_habilidade(dados: dict, id_candidato: int = Depends(autenticar)):
    nome = (dados.get("nome") or "").strip()
    proficiencia = (dados.get("proficiencia") or "").strip()
    if not nome or not proficiencia:
        raise HTTPException(400, "Nome e proficiência são obrigatórios.")
    dados["id_candidato"] = id_candidato
    resultado = db_inserir("habilidades", dados)
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

@app.put("/perfil-candidato/habilidades/{id}")
async def atualizar_habilidade(id: int, dados: dict, id_candidato: int = Depends(autenticar)):
    hab = db_selecionar("habilidades", condicao={"id": id, "id_candidato": id_candidato}, unico=True)
    if not hab:
        raise HTTPException(404, "Habilidade não encontrada.")
    resultado = db_atualizar("habilidades", dados, {"id": id})
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

@app.delete("/perfil-candidato/habilidades/{id}")
async def remover_habilidade(id: int, id_candidato: int = Depends(autenticar)):
    hab = db_selecionar("habilidades", condicao={"id": id, "id_candidato": id_candidato}, unico=True)
    if not hab:
        raise HTTPException(404, "Habilidade não encontrada.")
    resultado = db_excluir("habilidades", {"id": id})
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

# ─────────────────────────────────────────────────────────
# IDIOMAS
# ─────────────────────────────────────────────────────────
@app.post("/perfil-candidato/idiomas")
async def criar_idioma(dados: dict, id_candidato: int = Depends(autenticar)):
    nome = (dados.get("nome") or "").strip()
    proficiencia = (dados.get("proficiencia") or "").strip()
    if not nome or not proficiencia:
        raise HTTPException(400, "Nome e proficiência são obrigatórios.")
    dados["id_candidato"] = id_candidato
    resultado = db_inserir("idiomas", dados)
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

@app.put("/perfil-candidato/idiomas/{id}")
async def atualizar_idioma(id: int, dados: dict, id_candidato: int = Depends(autenticar)):
    idm = db_selecionar("idiomas", condicao={"id": id, "id_candidato": id_candidato}, unico=True)
    if not idm:
        raise HTTPException(404, "Idioma não encontrado.")
    resultado = db_atualizar("idiomas", dados, {"id": id})
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

@app.delete("/perfil-candidato/idiomas/{id}")
async def remover_idioma(id: int, id_candidato: int = Depends(autenticar)):
    idm = db_selecionar("idiomas", condicao={"id": id, "id_candidato": id_candidato}, unico=True)
    if not idm:
        raise HTTPException(404, "Idioma não encontrado.")
    resultado = db_excluir("idiomas", {"id": id})
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

# ─────────────────────────────────────────────────────────
# CERTIFICAÇÕES
# ─────────────────────────────────────────────────────────
@app.post("/perfil-candidato/certificacoes")
async def criar_certificacao(dados: dict, id_candidato: int = Depends(autenticar)):
    nome = (dados.get("nome") or "").strip()
    emissor = (dados.get("emissor") or "").strip()
    if not nome or not emissor:
        raise HTTPException(400, "Nome e emissor são obrigatórios.")
    dados["id_candidato"] = id_candidato
    resultado = db_inserir("certificacoes", dados)
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

@app.put("/perfil-candidato/certificacoes/{id}")
async def atualizar_certificacao(id: int, dados: dict, id_candidato: int = Depends(autenticar)):
    cert = db_selecionar("certificacoes", condicao={"id": id, "id_candidato": id_candidato}, unico=True)
    if not cert:
        raise HTTPException(404, "Certificação não encontrada.")
    resultado = db_atualizar("certificacoes", dados, {"id": id})
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

@app.delete("/perfil-candidato/certificacoes/{id}")
async def remover_certificacao(id: int, id_candidato: int = Depends(autenticar)):
    cert = db_selecionar("certificacoes", condicao={"id": id, "id_candidato": id_candidato}, unico=True)
    if not cert:
        raise HTTPException(404, "Certificação não encontrada.")
    resultado = db_excluir("certificacoes", {"id": id})
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

# ─────────────────────────────────────────────────────────
# DOCUMENTOS
# ─────────────────────────────────────────────────────────
@app.post("/perfil-candidato/documentos")
async def criar_documento(dados: dict, id_candidato: int = Depends(autenticar)):
    tipo = (dados.get("tipo") or "").strip()
    nome_arquivo = (dados.get("nome_arquivo") or "").strip()
    caminho_disco = (dados.get("caminho_disco") or "").strip()
    if not tipo or not nome_arquivo or not caminho_disco:
        raise HTTPException(400, "Tipo, nome_arquivo e caminho_disco são obrigatórios.")
    dados["id_candidato"] = id_candidato
    resultado = db_inserir("documentos", dados)
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

@app.put("/perfil-candidato/documentos/{id}")
async def atualizar_documento(id: int, dados: dict, id_candidato: int = Depends(autenticar)):
    doc = db_selecionar("documentos", condicao={"id": id, "id_candidato": id_candidato}, unico=True)
    if not doc:
        raise HTTPException(404, "Documento não encontrado.")
    resultado = db_atualizar("documentos", dados, {"id": id})
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

@app.delete("/perfil-candidato/documentos/{id}")
async def remover_documento(id: int, id_candidato: int = Depends(autenticar)):
    doc = db_selecionar("documentos", condicao={"id": id, "id_candidato": id_candidato}, unico=True)
    if not doc:
        raise HTTPException(404, "Documento não encontrado.")
    resultado = db_excluir("documentos", {"id": id})
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

# ─────────────────────────────────────────────────────────
# CONTATOS
# ─────────────────────────────────────────────────────────
@app.put("/perfil-candidato/contatos")
async def atualizar_contatos(dados: dict, id_candidato: int = Depends(autenticar)):
    contato = db_selecionar("contatos", condicao={"id_candidato": id_candidato}, unico=True)
    if contato:
        resultado = db_atualizar("contatos", dados, {"id_candidato": id_candidato})
    else:
        dados["id_candidato"] = id_candidato
        resultado = db_inserir("contatos", dados)
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

# ─────────────────────────────────────────────────────────
# PERFIL — atualizar e validar
# ─────────────────────────────────────────────────────────
@app.put("/perfil-candidato")
async def atualizar_perfil(dados: dict, id_candidato: int = Depends(autenticar)):
    perfil = db_selecionar("perfil_candidato", condicao={"id_candidato": id_candidato}, unico=True)
    if perfil:
        resultado = db_atualizar("perfil_candidato", dados, {"id_candidato": id_candidato})
    else:
        dados["id_candidato"] = id_candidato
        resultado = db_inserir("perfil_candidato", dados)
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

@app.post("/perfil-candidato/novo-manual")
async def criar_perfil_manual(dados: dict, id_candidato: int = Depends(autenticar)):
    perfil_existente = db_selecionar("perfil_candidato", condicao={"id_candidato": id_candidato}, unico=True)
    if perfil_existente:
        raise HTTPException(409, "Perfil já existe. Use PUT para atualizar.")
    dados["id_candidato"] = id_candidato
    dados["tipo_importacao"] = "formulario"
    resultado = db_inserir("perfil_candidato", dados)
    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])
    return resultado

@app.post("/perfil-candidato/validar")
async def validar_perfil(id_candidato: int = Depends(autenticar)):
    perfil = db_selecionar("perfil_candidato", condicao={"id_candidato": id_candidato}, unico=True)
    if not perfil:
        return {
            "ok": True,
            "valido": False,
            "erros": ["Perfil não encontrado. Crie um novo perfil para continuar."]
        }

    erros = []

    # Validação 1: nome do candidato (já vem da tabela candidatos)
    candidato = db_selecionar("candidatos", condicao={"id": id_candidato}, unico=True)
    if not candidato or not candidato.get("nome"):
        erros.append("Nome do candidato não encontrado.")

    # Validação 2: contato (telefone, linkedin, github ou website)
    contato = db_selecionar("contatos", condicao={"id_candidato": id_candidato}, unico=True)
    if not contato or not (contato.get("telefone") or contato.get("linkedin") or contato.get("github") or contato.get("website")):
        erros.append("Falta informação de contato (telefone, LinkedIn, GitHub ou website).")

    # Validação 3: pelo menos 1 habilidade
    habilidades = db_selecionar("habilidades", condicao={"id_candidato": id_candidato}) or []
    if len(habilidades) == 0:
        erros.append("Falta adicionar pelo menos 1 habilidade.")

    # Validação 4: pelo menos 1 de (experiência, formação ou certificação)
    experiencias = db_selecionar("experiencias", condicao={"id_candidato": id_candidato}) or []
    formacoes = db_selecionar("formacoes", condicao={"id_candidato": id_candidato}) or []
    certificacoes = db_selecionar("certificacoes", condicao={"id_candidato": id_candidato}) or []

    if len(experiencias) == 0 and len(formacoes) == 0 and len(certificacoes) == 0:
        erros.append("Falta adicionar pelo menos 1 de: experiência, formação ou certificação.")

    valido = len(erros) == 0
    return {
        "ok": True,
        "valido": valido,
        "erros": erros if not valido else []
    }

# ─────────────────────────────────────────────────────────
# UPLOAD DE ARQUIVO — preparação para Motor 4
# ─────────────────────────────────────────────────────────
@app.post("/perfil-candidato/documentos/upload-complementar")
async def upload_documento_complementar(
    arquivo: UploadFile = File(...),
    descricao: str = Form(""),
    id_candidato: int = Depends(autenticar)
):
    conteudo = await arquivo.read()
    if len(conteudo) > 10 * 1024 * 1024:
        raise HTTPException(400, "Arquivo muito grande. Máximo 10MB.")

    pasta_candidato = os.path.join(PASTA_UPLOADS, str(id_candidato))
    os.makedirs(pasta_candidato, exist_ok=True)

    nome_arquivo = arquivo.filename.replace("/", "_").replace("\\", "_")
    caminho_destino = os.path.join(pasta_candidato, nome_arquivo)

    with open(caminho_destino, "wb") as f:
        f.write(conteudo)

    resultado = db_inserir("documentos", {
        "id_candidato": id_candidato,
        "tipo": "complementar",
        "nome_arquivo": nome_arquivo,
        "caminho_disco": caminho_destino,
        "descricao": descricao.strip() or nome_arquivo,
    })

    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])

    texto_extraido = None
    try:
        from rotinas.importacao import extrair_texto_pdf, extrair_texto_docx
        ext = nome_arquivo.lower().rsplit(".", 1)[-1]
        if ext == "pdf":
            texto_extraido = extrair_texto_pdf(conteudo)
        elif ext in ("docx", "doc"):
            texto_extraido = extrair_texto_docx(conteudo)
    except Exception:
        pass

    return {"ok": True, "dados": resultado, "texto_extraido": texto_extraido}

@app.post("/perfil-candidato/upload-arquivo")
async def upload_arquivo(
    arquivo: UploadFile = File(...),
    id_candidato: int = Depends(autenticar)
):
    """
    Upload de arquivo de currículo ou documento.
    Motor 4 usará esse endpoint para processar com IA.
    Salva em apoio/uploads/{id_candidato}/{nome_arquivo}
    """
    # Valida tipo de arquivo
    tipos_permitidos = {"application/pdf", "application/msword",
                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                       "text/plain"}
    if arquivo.content_type not in tipos_permitidos:
        raise HTTPException(400, "Tipo de arquivo não permitido. Use PDF, DOC, DOCX ou TXT.")

    # Valida tamanho (máx 10MB)
    conteudo = await arquivo.read()
    if len(conteudo) > 10 * 1024 * 1024:
        raise HTTPException(400, "Arquivo muito grande. Máximo 10MB.")

    # Cria pasta de destino
    pasta_candidato = os.path.join(PASTA_UPLOADS, str(id_candidato))
    os.makedirs(pasta_candidato, exist_ok=True)

    # Sanitiza nome do arquivo
    nome_arquivo = arquivo.filename.replace("/", "_").replace("\\", "_")
    caminho_destino = os.path.join(pasta_candidato, nome_arquivo)

    # Salva arquivo
    try:
        with open(caminho_destino, "wb") as f:
            f.write(conteudo)
    except Exception as e:
        raise HTTPException(500, f"Erro ao salvar arquivo: {str(e)}")

    # Registra no banco de dados
    resultado = db_inserir("documentos", {
        "id_candidato": id_candidato,
        "tipo": "arquivo_importacao",
        "nome_arquivo": nome_arquivo,
        "caminho_disco": caminho_destino,
    })

    if resultado["status"] == "erro":
        raise HTTPException(400, resultado["mensagem"])

    return {
        "ok": True,
        "dados": {
            "id": resultado.get("id"),
            "nome_arquivo": nome_arquivo,
            "caminho_disco": caminho_destino,
            "mensagem": "Arquivo salvo com sucesso. Motor 4 processará em breve."
        }
    }

# ─────────────────────────────────────────────────────────
# IMPORTAÇÃO DE CURRÍCULO — Motor 4
# ─────────────────────────────────────────────────────────
@app.post("/perfil-candidato/importar")
async def importar_curriculo(
    arquivo: UploadFile = File(...),
    id_candidato: int = Depends(autenticar)
):
    from rotinas.importacao import extrair_texto_pdf, extrair_texto_docx, processar_curriculo_com_ia

    tipos_permitidos = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }
    if arquivo.content_type not in tipos_permitidos:
        raise HTTPException(400, "Apenas PDF e DOCX são suportados para importação.")

    conteudo = await arquivo.read()
    if len(conteudo) > 10 * 1024 * 1024:
        raise HTTPException(400, "Arquivo muito grande. Máximo 10MB.")

    if "pdf" in arquivo.content_type:
        texto = extrair_texto_pdf(conteudo)
    else:
        texto = extrair_texto_docx(conteudo)

    if not texto.strip():
        raise HTTPException(422, "Não foi possível extrair texto do arquivo.")

    try:
        dados = processar_curriculo_com_ia(texto)
    except ValueError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        msg = str(e).lower()
        if "quota" in msg or "insufficient" in msg or "429" in msg or "rate" in msg:
            raise HTTPException(503, "Cota de IA esgotada em todos os provedores. Tente novamente mais tarde ou adicione créditos em platform.openai.com.")
        raise HTTPException(500, f"Erro ao processar com IA: {str(e)}")

    # Salva arquivo físico
    pasta_candidato = os.path.join(PASTA_UPLOADS, str(id_candidato))
    os.makedirs(pasta_candidato, exist_ok=True)
    nome_arquivo = arquivo.filename.replace("/", "_").replace("\\", "_")
    caminho_destino = os.path.join(pasta_candidato, nome_arquivo)
    with open(caminho_destino, "wb") as f:
        f.write(conteudo)

    db_inserir("documentos", {
        "id_candidato": id_candidato,
        "tipo": "curriculo_importado",
        "nome_arquivo": nome_arquivo,
        "caminho_disco": caminho_destino,
    })

    # Upsert perfil_candidato
    perfil_dados = {
        "tipo_importacao": "arquivo",
        "arquivo_nome": nome_arquivo,
        "resumo_profissional": dados.get("resumo_profissional"),
        "localizacao": dados.get("localizacao"),
        "pretensao_salarial": dados.get("pretensao_salarial") or 0,
        "data_atualizacao": datetime.now(timezone.utc).isoformat(),
    }
    perfil_existente = db_selecionar("perfil_candidato", condicao={"id_candidato": id_candidato}, unico=True)
    if perfil_existente:
        db_atualizar("perfil_candidato", perfil_dados, {"id_candidato": id_candidato})
    else:
        perfil_dados["id_candidato"] = id_candidato
        db_inserir("perfil_candidato", perfil_dados)

    # Merge incremental — insere apenas registros novos, preserva os existentes
    existentes_exp  = {(r["cargo"], r["empresa"]) for r in db_selecionar("experiencias",  condicao={"id_candidato": id_candidato}) or []}
    existentes_form = {(r["curso"], r["instituicao"]) for r in db_selecionar("formacoes",  condicao={"id_candidato": id_candidato}) or []}
    existentes_hab  = {r["nome"] for r in db_selecionar("habilidades",   condicao={"id_candidato": id_candidato}) or []}
    existentes_idm  = {r["nome"] for r in db_selecionar("idiomas",       condicao={"id_candidato": id_candidato}) or []}
    existentes_cert = {r["nome"] for r in db_selecionar("certificacoes", condicao={"id_candidato": id_candidato}) or []}

    for exp in dados.get("experiencias") or []:
        if (exp.get("cargo"), exp.get("empresa")) not in existentes_exp:
            exp["id_candidato"] = id_candidato
            db_inserir("experiencias", exp)

    for form in dados.get("formacoes") or []:
        if (form.get("curso"), form.get("instituicao")) not in existentes_form:
            form["id_candidato"] = id_candidato
            db_inserir("formacoes", form)

    for hab in dados.get("habilidades") or []:
        if hab.get("nome") not in existentes_hab:
            hab["id_candidato"] = id_candidato
            db_inserir("habilidades", hab)

    for idm in dados.get("idiomas") or []:
        if idm.get("nome") not in existentes_idm:
            idm["id_candidato"] = id_candidato
            db_inserir("idiomas", idm)

    for cert in dados.get("certificacoes") or []:
        if cert.get("nome") not in existentes_cert:
            cert["id_candidato"] = id_candidato
            db_inserir("certificacoes", cert)

    # Upsert contatos
    contatos = dados.get("contatos") or {}
    if any(v for v in contatos.values() if v):
        contato_existente = db_selecionar("contatos", condicao={"id_candidato": id_candidato}, unico=True)
        if contato_existente:
            db_atualizar("contatos", contatos, {"id_candidato": id_candidato})
        else:
            contatos["id_candidato"] = id_candidato
            db_inserir("contatos", contatos)

    return {"ok": True, "mensagem": "Currículo importado com sucesso.", "dados": dados}

# ─────────────────────────────────────────────────────────
# VAGAS — protegidas
# ─────────────────────────────────────────────────────────
@app.get("/vagas")
async def listar_vagas(id_candidato: int = Depends(autenticar)):
    with _obter_conexao() as conn:
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

@app.get("/vagas/verificar-disponibilidade")
async def verificar_disponibilidade_vagas(id_candidato: int = Depends(autenticar)):
    from rotinas.sincronizacao import _get_json, _API_URL
    try:
        meta = _get_json(f"{_API_URL}?page=1&perPage=1")["meta"]
        total_api = meta.get("total", 0)
    except Exception as e:
        return {"ok": False, "erro": str(e)}

    with _obter_conexao() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM vagas WHERE disponivel_plataforma = 1"
        ).fetchone()
        total_db = row[0] if row else 0

    return {
        "ok": True,
        "total_api": total_api,
        "total_db": total_db,
        "desatualizado": total_api != total_db,
    }

@app.get("/vagas/{id}")
async def buscar_vaga(id: int, id_candidato: int = Depends(autenticar)):
    vaga = db_selecionar("vagas", condicao={"id": id}, unico=True)
    if not vaga:
        raise HTTPException(404, "Vaga não encontrada.")
    return vaga

def _montar_perfil_texto(id_candidato: int) -> str:
    candidato    = db_selecionar("candidatos",       condicao={"id": id_candidato},           unico=True) or {}
    perfil       = db_selecionar("perfil_candidato", condicao={"id_candidato": id_candidato}, unico=True) or {}
    contatos     = db_selecionar("contatos",         condicao={"id_candidato": id_candidato}, unico=True) or {}
    experiencias = db_selecionar("experiencias",     condicao={"id_candidato": id_candidato}) or []
    formacoes    = db_selecionar("formacoes",        condicao={"id_candidato": id_candidato}) or []
    habilidades  = db_selecionar("habilidades",      condicao={"id_candidato": id_candidato}) or []
    idiomas      = db_selecionar("idiomas",          condicao={"id_candidato": id_candidato}) or []
    certificacoes= db_selecionar("certificacoes",    condicao={"id_candidato": id_candidato}) or []
    docs         = db_selecionar("documentos",       condicao={"id_candidato": id_candidato}) or []

    linhas = [f"Nome: {candidato.get('nome', '')}"]

    itens_contato = [
        f"Telefone: {contatos['telefone']}" if contatos.get("telefone") else None,
        f"LinkedIn: {contatos['linkedin']}"  if contatos.get("linkedin")  else None,
        f"GitHub: {contatos['github']}"      if contatos.get("github")    else None,
        f"Website: {contatos['website']}"    if contatos.get("website")   else None,
    ]
    itens_contato = [i for i in itens_contato if i]
    if itens_contato:
        linhas.append("Contatos: " + " | ".join(itens_contato))

    if perfil.get("localizacao"):
        linhas.append(f"Localização: {perfil['localizacao']}")
    if perfil.get("resumo_profissional"):
        linhas.append(f"\nResumo: {perfil['resumo_profissional']}")

    if experiencias:
        linhas.append("\nExperiências:")
        for e in experiencias:
            periodo = " (atual)" if e.get("em_atual") else (f" até {e['data_fim']}" if e.get("data_fim") else "")
            linhas.append(f"  - {e.get('cargo')} em {e.get('empresa')}{periodo}")
            if e.get("descricao"):
                linhas.append(f"    {e['descricao']}")

    if formacoes:
        linhas.append("\nFormação:")
        for f in formacoes:
            prog = " (em progresso)" if f.get("em_progresso") else ""
            linhas.append(f"  - {f.get('curso')} — {f.get('instituicao')} ({f.get('nivel')}){prog}")

    if habilidades:
        linhas.append(f"\nHabilidades: {', '.join(h.get('nome', '') for h in habilidades)}")

    if idiomas:
        linhas.append("\nIdiomas: " + ", ".join(
            f"{i.get('nome')} ({i.get('proficiencia')})" for i in idiomas
        ))

    if certificacoes:
        linhas.append("\nCertificações: " + ", ".join(
            f"{c.get('nome')} ({c.get('emissor')})" for c in certificacoes
        ))

    complementares = [d for d in docs if d.get("tipo") == "complementar"]
    if complementares:
        linhas.append("\nDocumentos complementares (portfólio):")
        for d in complementares:
            linhas.append(f"  - {d.get('descricao') or d.get('nome_arquivo', '')}")

    return "\n".join(linhas) if linhas else "Perfil sem dados suficientes."


def _obter_base_perfil(id_candidato: int) -> str:
    """Base de análise é sempre o perfil estruturado do banco (fonte de verdade).
    Currículos premium gerados são produto final — nunca fonte de análise."""
    return _montar_perfil_texto(id_candidato)


@app.get("/vagas/{id}/conversa")
async def carregar_conversa(id: int, id_candidato: int = Depends(autenticar)):
    with _obter_conexao() as conn:
        row = conn.execute(
            "SELECT id, historico, score_estimado, status FROM conversas WHERE id_candidato = ? AND id_vaga = ?",
            (id_candidato, id)
        ).fetchone()
    if not row:
        return {"ok": True, "dados": None}
    return {
        "ok": True,
        "dados": {
            "id": row[0],
            "historico": json.loads(row[1]),
            "score_estimado": row[2],
            "status": row[3],
        },
    }


@app.post("/vagas/{id}/conversar")
async def conversar(id: int, corpo: dict, id_candidato: int = Depends(autenticar)):
    mensagem = (corpo.get("mensagem") or "").strip()

    vaga = db_selecionar("vagas", condicao={"id": id}, unico=True)
    if not vaga:
        raise HTTPException(404, "Vaga não encontrada.")

    perfil = db_selecionar("perfil_candidato", condicao={"id_candidato": id_candidato}, unico=True)
    if not perfil:
        raise HTTPException(422, "Importe seu currículo antes de iniciar a entrevista.")

    perfil_texto = _obter_base_perfil(id_candidato)

    with _obter_conexao() as conn:
        row = conn.execute(
            "SELECT id, historico, score_estimado FROM conversas WHERE id_candidato = ? AND id_vaga = ?",
            (id_candidato, id)
        ).fetchone()

    if row:
        conv_id  = row[0]
        historico = json.loads(row[1])
    else:
        conv_id  = None
        historico = []

    if mensagem:
        historico.append({"role": "candidato", "conteudo": mensagem})

    from rotinas.importacao import conduzir_entrevista
    try:
        resultado = conduzir_entrevista(
            titulo=vaga.get("titulo", ""),
            descricao=vaga.get("descricao", ""),
            perfil=perfil_texto,
            historico=historico,
        )
    except Exception as e:
        msg = str(e).lower()
        if "quota" in msg or "insufficient" in msg or "429" in msg or "rate" in msg:
            raise HTTPException(503, "Cota de IA esgotada. Tente novamente em instantes.")
        raise HTTPException(500, f"Erro ao processar: {str(e)}")

    historico.append({"role": "recrutador", "conteudo": resultado["mensagem"]})

    pronto = bool(resultado.get("pronto", False))
    score  = float(resultado.get("score_estimado", 0))
    status = "pronto" if pronto else "em_andamento"
    hist_json = json.dumps(historico, ensure_ascii=False)

    with _obter_conexao() as conn:
        if conv_id:
            conn.execute(
                "UPDATE conversas SET historico=?, score_estimado=?, status=?, atualizado_em=CURRENT_TIMESTAMP WHERE id=?",
                (hist_json, score, status, conv_id)
            )
        else:
            conn.execute(
                "INSERT INTO conversas (id_candidato, id_vaga, historico, score_estimado, status) VALUES (?,?,?,?,?)",
                (id_candidato, id, hist_json, score, status)
            )
        conn.commit()

    return {
        "ok": True,
        "resposta": resultado["mensagem"],
        "pronto": pronto,
        "score_estimado": score,
    }


@app.delete("/vagas/{id}/conversa")
async def resetar_conversa(id: int, id_candidato: int = Depends(autenticar)):
    with _obter_conexao() as conn:
        conn.execute(
            "DELETE FROM conversas WHERE id_candidato = ? AND id_vaga = ?",
            (id_candidato, id)
        )
        conn.commit()
    return {"ok": True, "mensagem": "Conversa reiniciada."}


@app.post("/vagas/{id}/score")
async def calcular_score_vaga(id: int, id_candidato: int = Depends(autenticar)):
    vaga = db_selecionar("vagas", condicao={"id": id}, unico=True)
    if not vaga:
        raise HTTPException(404, "Vaga não encontrada.")

    perfil = db_selecionar("perfil_candidato", condicao={"id_candidato": id_candidato}, unico=True)
    if not perfil:
        raise HTTPException(422, "Importe seu currículo antes de calcular compatibilidade.")

    perfil_texto = _obter_base_perfil(id_candidato)

    from rotinas.importacao import processar_score_com_ia
    try:
        resultado = processar_score_com_ia(
            titulo=vaga.get("titulo", ""),
            descricao=vaga.get("descricao", ""),
            perfil=perfil_texto,
        )
    except Exception as e:
        msg = str(e).lower()
        if "quota" in msg or "insufficient" in msg or "429" in msg or "rate" in msg:
            raise HTTPException(503, "Cota de IA esgotada em todos os provedores. Tente novamente mais tarde ou adicione créditos em platform.openai.com.")
        raise HTTPException(500, f"Erro ao processar com IA: {str(e)}")

    return resultado

@app.post("/vagas/{id}/gerar-curriculo")
async def gerar_curriculo_vaga(id: int, id_candidato: int = Depends(autenticar)):
    vaga = db_selecionar("vagas", condicao={"id": id}, unico=True)
    if not vaga:
        raise HTTPException(404, "Vaga não encontrada.")

    perfil = db_selecionar("perfil_candidato", condicao={"id_candidato": id_candidato}, unico=True)
    if not perfil:
        raise HTTPException(422, "Importe seu currículo antes de gerar.")

    candidato = db_selecionar("candidatos", condicao={"id": id_candidato}, unico=True)
    contatos  = db_selecionar("contatos",   condicao={"id_candidato": id_candidato}, unico=True)

    linhas = [f"Nome: {candidato.get('nome', '')}"]

    if contatos:
        itens = [
            f"Telefone: {contatos['telefone']}" if contatos.get("telefone") else None,
            f"LinkedIn: {contatos['linkedin']}"  if contatos.get("linkedin")  else None,
            f"GitHub: {contatos['github']}"      if contatos.get("github")    else None,
            f"Website: {contatos['website']}"    if contatos.get("website")   else None,
        ]
        itens = [i for i in itens if i]
        if itens:
            linhas.append("Contatos: " + " | ".join(itens))

    if perfil.get("localizacao"):
        linhas.append(f"Localização: {perfil['localizacao']}")
    if perfil.get("resumo_profissional"):
        linhas.append(f"\nResumo: {perfil['resumo_profissional']}")

    experiencias = db_selecionar("experiencias", condicao={"id_candidato": id_candidato}) or []
    if experiencias:
        linhas.append("\nExperiências:")
        for e in experiencias:
            periodo = " (atual)" if e.get("em_atual") else (f" até {e['data_fim']}" if e.get("data_fim") else "")
            linhas.append(f"  - {e.get('cargo')} em {e.get('empresa')}{periodo}")
            if e.get("descricao"):
                linhas.append(f"    {e['descricao']}")

    formacoes = db_selecionar("formacoes", condicao={"id_candidato": id_candidato}) or []
    if formacoes:
        linhas.append("\nFormação:")
        for f in formacoes:
            prog = " (em progresso)" if f.get("em_progresso") else ""
            linhas.append(f"  - {f.get('curso')} — {f.get('instituicao')} ({f.get('nivel')}){prog}")

    habilidades = db_selecionar("habilidades", condicao={"id_candidato": id_candidato}) or []
    if habilidades:
        linhas.append(f"\nHabilidades: {', '.join(h.get('nome', '') for h in habilidades)}")

    idiomas = db_selecionar("idiomas", condicao={"id_candidato": id_candidato}) or []
    if idiomas:
        linhas.append("\nIdiomas: " + ", ".join(
            f"{i.get('nome')} ({i.get('proficiencia')})" for i in idiomas
        ))

    certificacoes = db_selecionar("certificacoes", condicao={"id_candidato": id_candidato}) or []
    if certificacoes:
        linhas.append("\nCertificações: " + ", ".join(
            f"{c.get('nome')} ({c.get('emissor')})" for c in certificacoes
        ))

    docs = db_selecionar("documentos", condicao={"id_candidato": id_candidato}) or []
    complementares = [d for d in docs if d.get("tipo") == "complementar"]
    if complementares:
        linhas.append("\nDocumentos complementares (portfólio):")
        for d in complementares:
            linhas.append(f"  - {d.get('descricao') or d.get('nome_arquivo', '')}")

    perfil_texto = "\n".join(linhas)

    with _obter_conexao() as conn:
        row_conv = conn.execute(
            "SELECT historico FROM conversas WHERE id_candidato = ? AND id_vaga = ?",
            (id_candidato, id)
        ).fetchone()
    historico_entrevista = ""
    if row_conv:
        try:
            msgs = json.loads(row_conv["historico"])
            historico_entrevista = "\n".join(
                f"{m['role'].upper()}: {m['conteudo']}"
                for m in msgs if m.get("conteudo", "").strip()
            )
        except Exception:
            pass

    from rotinas.importacao import gerar_curriculo_com_ia
    try:
        texto = gerar_curriculo_com_ia(
            titulo=vaga.get("titulo", ""),
            descricao=vaga.get("descricao", ""),
            perfil=perfil_texto,
            historico=historico_entrevista,
        )
    except Exception as e:
        msg = str(e).lower()
        if "quota" in msg or "insufficient" in msg or "429" in msg or "rate" in msg:
            raise HTTPException(503, "Cota de IA esgotada em todos os provedores. Tente novamente mais tarde ou adicione créditos em platform.openai.com.")
        raise HTTPException(500, f"Erro ao processar com IA: {str(e)}")

    # DA-02: preservar cada geração como ativo independente (nunca sobrescrever)
    import time as _time
    pasta_candidato = os.path.join(PASTA_UPLOADS, str(id_candidato))
    os.makedirs(pasta_candidato, exist_ok=True)
    nome_arquivo    = f"curriculo_vaga_{id}_{int(_time.time())}.txt"
    caminho_destino = os.path.join(pasta_candidato, nome_arquivo)
    with open(caminho_destino, "w", encoding="utf-8") as f:
        f.write(texto)

    with _obter_conexao() as conn:
        conn.execute(
            "INSERT INTO documentos (id_candidato, tipo, nome_arquivo, caminho_disco, descricao) VALUES (?,?,?,?,?)",
            (
                id_candidato, "curriculo_gerado", nome_arquivo, caminho_destino,
                f"Currículo — {vaga.get('titulo', 'Vaga')} ({vaga.get('empresa', '')})",
            )
        )
        conn.commit()

    return {
        "ok": True,
        "curriculo": texto,
        "vaga": {"id": id, "titulo": vaga.get("titulo", ""), "empresa": vaga.get("empresa", "")},
    }


@app.get("/perfil-candidato/curriculos-gerados")
async def listar_curriculos_gerados(id_candidato: int = Depends(autenticar)):
    """Retorna todos os currículos premium gerados, com conteúdo, ordenados do mais recente."""
    import re as _re
    docs = db_selecionar("documentos", condicao={"id_candidato": id_candidato}) or []
    gerados = sorted(
        [d for d in docs if d.get("tipo") == "curriculo_gerado"],
        key=lambda d: d.get("id", 0),
        reverse=True,
    )
    resultado = []
    for doc in gerados:
        conteudo = ""
        try:
            with open(doc.get("caminho_disco", ""), "r", encoding="utf-8") as f:
                conteudo = f.read()
        except Exception:
            pass
        # extrai vagaId do nome_arquivo: curriculo_vaga_{id}_{ts}.txt
        m = _re.match(r"curriculo_vaga_(\d+)_", doc.get("nome_arquivo", ""))
        vaga_id = int(m.group(1)) if m else None
        vaga_info = {}
        if vaga_id:
            vaga_row = db_selecionar("vagas", condicao={"id": vaga_id}, unico=True)
            vaga_info = {
                "id": vaga_id,
                "titulo": vaga_row.get("titulo", "") if vaga_row else "",
                "empresa": vaga_row.get("empresa", "") if vaga_row else "",
            }
        resultado.append({
            "id_documento": doc.get("id"),
            "descricao": doc.get("descricao", ""),
            "vaga": vaga_info,
            "conteudo": conteudo,
        })
    return {"ok": True, "dados": resultado}


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
    with _obter_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM logs_sistema ORDER BY momento DESC LIMIT ?", (limite,)
        )
        return [dict(row) for row in cursor.fetchall()]
