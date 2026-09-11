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
Seu julgamento é PRAGMÁTICO, não literário: avalie evidências concretas — o que foi dito, o que consta em
documentos — nunca a qualidade da narrativa ou o quão bem contada está a história do candidato. Um
candidato que descreve pouco mas com fatos concretos e verificáveis vale mais, para efeito de score, do
que um que descreve muito com linguagem elogiosa, vaga ou aspiracional. Não pontue "romance" — pontue fato.

REGRA DE REALISMO — acima de qualquer outra instrução abaixo:
- O score deve refletir a aderência REAL entre o que o candidato demonstrou (habilidade declarada,
  experiência descrita, ou resposta efetivamente dada na entrevista) e os requisitos da vaga — nem
  punitivo, nem otimista. PROIBIDO presumir que o candidato provavelmente tem uma capacidade que ele
  nunca demonstrou, só porque "seria razoável supor". Se não há evidência de um requisito, ele conta
  como lacuna real — não como "provável presença não declarada".
- A instrução 4 abaixo ("lacuna pode ser ausência de informação") significa: LISTE a lacuna e deixe a
  entrevista esclarecer — NÃO significa presumir a resposta e já pontuar como se estivesse confirmada.
- "resumo", "pontos_fortes" e "lacunas" devem ser honestos: não omita uma lacuna real para o candidato
  parecer mais aderente, e não invente um ponto forte que não está no conteúdo fornecido.
- LACUNA CONFESSADA NUNCA VIRA PONTO FORTE — se o candidato declarou EXPLICITAMENTE que NÃO tem
  experiência ou conhecimento em algo — mesmo que, no mesmo momento, descreva um PLANO para compensar
  essa lacuna (ex.: "vou consultar normas técnicas", "pretendo estudar isso") — isso continua sendo uma
  LACUNA em "lacunas", nunca um item em "pontos_fortes", e NÃO justifica subir o score como se o requisito
  já estivesse atendido. Mencionar os termos técnicos da vaga ao explicar como pretende suprir uma lacuna
  não é o mesmo que já possuir a competência — credite a iniciativa/postura se relevante, mas não a
  competência em si.

INSTRUÇÕES OBRIGATÓRIAS — siga na ordem exata:
1. Leia integralmente TODO o conteúdo do candidato abaixo — perfil estruturado, currículo premium se presente, DOCUMENTOS COMPLEMENTARES anexados (histórico acadêmico, certificados, portfólio) se presentes, e histórico de entrevista se houver. Não ignore nenhuma seção — documento anexado e ignorado é informação relevante desperdiçada.
2. Identifique TODAS as habilidades técnicas e conhecimentos declarados individualmente, independentemente de onde apareçam (perfil, currículo ou documento complementar) ou da trajetória de carreira. Garimpe especialmente os documentos complementares: disciplinas de um histórico acadêmico, competências de um certificado, projetos de um portfólio — tudo isso é evidência real de capacidade, mesmo que o candidato não tenha repetido isso na entrevista.
3. Considere habilidades transferíveis (ex.: HTML, CSS e JavaScript são relevantes para vagas Front-End mesmo com experiência em outra área) — desde que a habilidade-base tenha sido de fato declarada.
4. Lacunas aparentes podem ser ausência de informação no texto, não ausência de capacidade real — mas isso é motivo para LISTAR a lacuna e perguntar na entrevista, nunca para presumir a resposta e pontuar como se já estivesse resolvida.
5. Se houver histórico de entrevista, credite qualquer informação pertinente ao TEMA da vaga que o candidato tenha fornecido — mesmo que a resposta não tenha atacado exatamente a pergunta feita. Avalie o CONTEÚDO efetivamente entregue, não a aderência estrita ao formato da pergunta, e não o que ele poderia ter dito.
6. NUNCA atribua score zero se houver habilidade técnica relevante à vaga declarada em qualquer parte do conteúdo — mas isso não autoriza inflar o score além do que os requisitos efetivamente atendidos justificam.
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


_HISTORICO_MAX_MENSAGENS = 16
_HISTORICO_MAX_CHARS = 12000
_DOCUMENTO_COMPLEMENTAR_MAX_CHARS = 8000


def montar_historico_texto(historico: list) -> str:
    """Constrói o texto do histórico de conversa para enviar à IA, com limites de
    tamanho — usada por toda rotina que precisa desse texto (entrevista, aderência).
    Sem isso, uma conversa longa (ou um documento grande citado numa mensagem) faz o
    prompt crescer sem controle a cada turno até estourar o limite do provedor
    (erro real observado em produção: 'Request too large' / 'context_length_exceeded',
    crescendo ~33K tokens por turno até travar a entrevista em loop de erro)."""
    if not historico:
        return ""
    recentes = historico[-_HISTORICO_MAX_MENSAGENS:]
    texto = "\n".join(f"{h['role'].upper()}: {h['conteudo']}" for h in recentes)
    if len(texto) > _HISTORICO_MAX_CHARS:
        texto = "[...histórico truncado, mensagens mais antigas omitidas...]\n" + texto[-_HISTORICO_MAX_CHARS:]
    return texto


def limitar_texto_documento(texto: str) -> str:
    """Corta o conteúdo extraído de um documento complementar a um teto de tamanho
    antes de persistir/injetar em qualquer prompt — mesma motivação de
    montar_historico_texto(): documento grande sem corte estoura o limite do
    provedor de IA."""
    if texto and len(texto) > _DOCUMENTO_COMPLEMENTAR_MAX_CHARS:
        return texto[:_DOCUMENTO_COMPLEMENTAR_MAX_CHARS] + "\n[...documento truncado — conteúdo muito extenso para análise integral...]"
    return texto


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
