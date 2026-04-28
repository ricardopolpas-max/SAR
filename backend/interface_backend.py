from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import os
from rotinas.genericas import DB_PATH, db_selecionar

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
                data_extracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                score REAL DEFAULT 0.0,
                status TEXT DEFAULT 'PENDENTE'
            )
        """)
        
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
    """
    Rota para retornar todas as vagas cadastradas.
    Consome a rotina genérica de banco de dados.
    """
    return db_selecionar("vagas", ordem="data_extracao DESC")