# backend/rotinas/genericas.py
# Rotinas genéricas (CRUD Agnóstico + utilitários agnósticos) para o Sistema SAR.
# Funções síncronas puras — sqlite3 é bloqueante por natureza.

import json
import re
import sqlite3
import os
from typing import List, Dict, Any, Optional

from rotinas.ia import gerar_conteudo

# Caminho do banco — Windows usa APPDATA, Linux usa ~/.local/share/SAR
if os.name == "nt":
    DB_PATH = os.path.join(os.environ["APPDATA"], "SAR", "sar_repositorio.db")
else:
    DB_PATH = os.path.join(os.path.expanduser("~"), ".local", "share", "SAR", "sar_repositorio.db")

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

def extrair_json(texto: str) -> dict:
    """Extrai o primeiro objeto JSON válido de uma resposta de LLM (pode vir
    com cercas de código ```json ... ``` ou texto antes/depois)."""
    texto = re.sub(r'^```[^\n]*\n', '', texto.strip())
    texto = re.sub(r'\n```$', '', texto.strip())

    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass

    inicio = texto.find('{')
    if inicio == -1:
        raise ValueError(f"Nenhum objeto JSON encontrado na resposta: {texto[:200]!r}")

    depth = 0
    in_string = False
    escape = False
    for i, ch in enumerate(texto[inicio:], start=inicio):
        if escape:
            escape = False
            continue
        if ch == '\\' and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return json.loads(texto[inicio:i + 1])

    raise ValueError(f"JSON mal-formado na resposta: {texto[:200]!r}")


_PROMPT_ADERENCIA = """Você é um especialista sênior em recrutamento brasileiro, com domínio em todas as áreas de atuação profissional.

INSTRUÇÕES OBRIGATÓRIAS — siga na ordem exata:
1. Leia integralmente TODO o conteúdo do candidato abaixo — perfil estruturado, currículo premium se presente, e histórico de entrevista se houver. Não ignore nenhuma seção.
2. Identifique TODAS as habilidades técnicas declaradas individualmente, independentemente da trajetória de carreira ou das certificações listadas. Habilidades declaradas são evidência real de capacidade.
3. Considere habilidades transferíveis (ex.: HTML, CSS e JavaScript são relevantes para vagas Front-End mesmo com experiência em outra área).
4. Lacunas aparentes podem ser ausência de informação no texto, não ausência de capacidade real.
5. Se houver histórico de entrevista, credite qualquer informação pertinente ao TEMA da vaga que o candidato tenha fornecido — mesmo que a resposta não tenha atacado exatamente a pergunta feita. Avalie o CONTEÚDO entregue, não a aderência estrita ao formato da pergunta.
6. NUNCA atribua score zero se houver habilidade técnica relevante à vaga declarada em qualquer parte do conteúdo.
7. NUNCA atribua um score menor que o "SCORE ANTERIOR" informado abaixo — a aderência é cumulativa: só sobe ou se mantém, nunca cai.
8. Somente após percorrer todo o conteúdo, calcule o score de 0 a 100.

Retorne APENAS um JSON válido, sem markdown, sem explicações:
{
  "score": <inteiro 0 a 100>,
  "resumo": "<1 frase explicando o nível de compatibilidade>",
  "pontos_fortes": ["<item>", "<item>"],
  "lacunas": ["<item>", "<item>"]
}

VAGA:
Título: {titulo}
Descrição: {descricao}

CANDIDATO:
{perfil}

SCORE ANTERIOR: {score_anterior}

HISTÓRICO DA ENTREVISTA (se houver):
{historico}
"""


def calcular_aderencia(titulo: str, descricao: str, perfil: str, historico: str = "", score_anterior: int = 0) -> dict:
    """
    Função pública e agnóstica de cálculo de aderência candidato↔vaga.
    Única régua usada em todo o sistema — na pré-triagem ("Ver aderência" na
    lista de vagas) e a cada resposta durante a entrevista. Garante que o
    score nunca regride abaixo de `score_anterior`. Chamável de qualquer
    parte do sistema que precise desse cálculo, bastando passar os parâmetros.
    """
    prompt = (
        _PROMPT_ADERENCIA
        .replace("{titulo}", titulo)
        .replace("{descricao}", descricao or "Não informada")
        .replace("{perfil}", perfil)
        .replace("{score_anterior}", str(int(score_anterior)))
        .replace("{historico}", historico or "(sem entrevista ainda)")
    )
    resultado = extrair_json(gerar_conteudo(prompt))
    resultado["score"] = max(int(resultado.get("score", 0)), int(score_anterior))
    return resultado

# Fim do arquivo genericas.py
