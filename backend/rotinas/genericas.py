# backend/rotinas/genericas.py
# Rotinas genéricas de persistência (CRUD Agnóstico) para o Sistema SAR.
# Funções síncronas puras — sqlite3 é bloqueante por natureza.

import sqlite3
import os
from typing import List, Dict, Any, Optional

# Caminho centralizado para o banco de dados conforme governança
DB_PATH = "armazenamento_dados/sar_repositorio.db"

def _obter_conexao():
    """Estabelece conexão com o SQLite e ativa suporte a chaves estrangeiras."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def db_selecionar(
    tabela: str,
    campos: Any = "*",
    condicao: Dict[str, Any] = None,
    ordem: str = None,
    unico: bool = False
) -> Any:
    """Executa leitura (SELECT) agnóstica."""
    campos_str = campos if isinstance(campos, str) else ", ".join(campos)
    sql = f"SELECT {campos_str} FROM {tabela}"
    params = []

    if condicao:
        filtros = [f"{k} = ?" for k in condicao.keys()]
        sql += " WHERE " + " AND ".join(filtros)
        params = list(condicao.values())

    if ordem:
        sql += f" ORDER BY {ordem}"
    if unico:
        sql += " LIMIT 1"

    try:
        with _obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            linhas = [dict(row) for row in cursor.fetchall()]
            if unico:
                return linhas[0] if linhas else None
            return linhas
    except Exception as e:
        print(f"[ERRO db_selecionar] Tabela {tabela}: {e}")
        return None if unico else []

def db_inserir(tabela: str, dados: Dict[str, Any]) -> Dict[str, Any]:
    """Executa inserção (INSERT) agnóstica."""
    colunas = ", ".join(dados.keys())
    placeholders = ", ".join(["?" for _ in dados])
    sql = f"INSERT INTO {tabela} ({colunas}) VALUES ({placeholders})"

    try:
        with _obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, list(dados.values()))
            conn.commit()
            return {"status": "sucesso", "id": cursor.lastrowid}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}

def db_atualizar(tabela: str, dados: Dict[str, Any], condicao: Dict[str, Any]) -> Dict[str, Any]:
    """Executa atualização (UPDATE) agnóstica."""
    set_str = ", ".join([f"{k} = ?" for k in dados.keys()])
    where_str = " AND ".join([f"{k} = ?" for k in condicao.keys()])
    sql = f"UPDATE {tabela} SET {set_str} WHERE {where_str}"
    params = list(dados.values()) + list(condicao.values())

    try:
        with _obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return {"status": "sucesso", "afetados": cursor.rowcount}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}

def db_excluir(tabela: str, condicao: Dict[str, Any]) -> Dict[str, Any]:
    """Executa exclusão (DELETE) agnóstica."""
    where_str = " AND ".join([f"{k} = ?" for k in condicao.keys()])
    sql = f"DELETE FROM {tabela} WHERE {where_str}"

    try:
        with _obter_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, list(condicao.values()))
            conn.commit()
            return {"status": "sucesso", "afetados": cursor.rowcount}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}

# Fim do arquivo genericas.py
