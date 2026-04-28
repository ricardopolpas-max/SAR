from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import threading
import os
from rotinas.genericas import DB_PATH, db_selecionar
from rotinas.sincronizacao import sincronizar

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR  = os.path.join(RAIZ, "frontend")
INTEGRACAO_DIR = os.path.join(RAIZ, "integracao")
SAR_HTML = os.path.join(FRONTEND_DIR, "telas", "SAR.html")

app = FastAPI(title="SAR - Sistema de Automação de Recolocação")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend",   StaticFiles(directory=FRONTEND_DIR),   name="frontend")
app.mount("/integracao", StaticFiles(directory=INTEGRACAO_DIR), name="integracao")

@app.on_event("startup")
def setup_db():
    """
    Inicializa o banco de dados e as tabelas core seguindo a governança de 'Verdade Absoluta'.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()
        
        # Tabela de Configurações: Parâmetros agnósticos do sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT,
                tipo TEXT DEFAULT 'string',
                descricao TEXT
            )
        """)
        
        # Tabela de Vagas: Repositório central de oportunidades (Core do SAR)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vagas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                empresa TEXT,
                link TEXT UNIQUE,
                localizacao TEXT,
                modalidade TEXT,
                tipo_contrato TEXT,
                salario_inicial INTEGER,
                descricao TEXT,
                id_externo TEXT UNIQUE,
                fonte TEXT DEFAULT 'peixe30',
                data_extracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultima_sincronizacao TIMESTAMP,
                score REAL DEFAULT 0.0,
                status TEXT DEFAULT 'PENDENTE'
            )
        """)

        # Migração: adiciona colunas ausentes em bancos já existentes
        cursor.execute("PRAGMA table_info(vagas)")
        colunas_existentes = {row[1] for row in cursor.fetchall()}
        novas_colunas = [
            ("localizacao",          "TEXT"),
            ("modalidade",           "TEXT"),
            ("tipo_contrato",        "TEXT"),
            ("salario_inicial",      "INTEGER"),
            ("descricao",            "TEXT"),
            ("id_externo",           "TEXT"),
            ("fonte",                "TEXT DEFAULT 'peixe30'"),
            ("ultima_sincronizacao", "TIMESTAMP"),
        ]
        for coluna, tipo in novas_colunas:
            if coluna not in colunas_existentes:
                cursor.execute(f"ALTER TABLE vagas ADD COLUMN {coluna} {tipo}")
        
        # Tabela de Logs: Rastreabilidade total
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                momento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acao TEXT NOT NULL,
                detalhes TEXT
            )
        """)
        conn.commit()

@app.on_event("startup")
def sync_inicial():
    """Dispara sincronização com o Peixe 30 em background para não bloquear o startup."""
    t = threading.Thread(target=_executar_sync, daemon=True)
    t.start()

def _executar_sync():
    resultado = sincronizar()
    if resultado["ok"]:
        print(f"[SAR] Sync Peixe 30 concluído — "
              f"{resultado['processadas']} vagas, "
              f"{resultado['removidas']} removidas.")
    else:
        print(f"[SAR] Sync Peixe 30 falhou — {resultado['erro']}")

_FAVICON_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
    "<rect width='32' height='32' rx='8' fill='#2d65e0'/>"
    "<text x='50%' y='54%' dominant-baseline='middle' text-anchor='middle' "
    "font-family='system-ui,sans-serif' font-weight='700' font-size='14' fill='#e8f0ff'>SAR</text>"
    "</svg>"
)

@app.get("/sar", include_in_schema=False)
async def interface_sar():
    return FileResponse(SAR_HTML)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content=_FAVICON_SVG, media_type="image/svg+xml")

@app.get("/")
async def root():
    return {"projeto": "SAR", "status": "operacional", "mensagem": "Interface Backend pronta para processamento"}

@app.get("/vagas")
async def listar_vagas():
    return db_selecionar("vagas", ordem="ultima_sincronizacao DESC")

@app.post("/vagas/sincronizar")
async def sincronizar_vagas(background: BackgroundTasks):
    """Dispara sincronização manual com o Peixe 30 em background."""
    background.add_task(_executar_sync)
    return {"mensagem": "Sincronização iniciada."}