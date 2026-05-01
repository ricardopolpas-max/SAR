from fastapi import FastAPI, Depends, Header, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timezone
import sqlite3
import json
import os
import shutil

from rotinas.genericas import DB_PATH, db_selecionar, db_inserir, db_atualizar, db_excluir
from rotinas.sincronizacao import sincronizar
from rotinas.autenticacao import (
    hash_senha, verificar_senha, criar_token, validar_token, revogar_token
)

RAIZ              = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
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
        "ok": True,
        "dados": {
            "perfil": perfil,
            "experiencias": experiencias,
            "formacoes": formacoes,
            "habilidades": habilidades,
            "idiomas": idiomas,
            "certificacoes": certificacoes,
            "documentos": documentos,
            "contatos": contatos,
        }
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
# VAGAS — protegidas
# ─────────────────────────────────────────────────────────
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
