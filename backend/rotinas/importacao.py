import io
import os
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

_PROMPT = """Você é um assistente especializado em análise de currículos jurídicos brasileiros.
Extraia as informações do currículo abaixo e retorne APENAS um JSON válido, sem markdown, sem explicações.

Estrutura esperada:
{
  "resumo_profissional": "string ou null",
  "localizacao": "Cidade, UF ou null",
  "pretensao_salarial": 0,
  "contatos": {
    "telefone": "string ou null",
    "linkedin": "URL ou null",
    "github": "URL ou null",
    "website": "URL ou null"
  },
  "experiencias": [
    {
      "cargo": "string",
      "empresa": "string",
      "data_inicio": "YYYY-MM-DD ou null",
      "data_fim": "YYYY-MM-DD ou null",
      "em_atual": 0,
      "descricao": "string ou null"
    }
  ],
  "formacoes": [
    {
      "instituicao": "string",
      "curso": "string",
      "nivel": "graduacao|pos_graduacao|mestrado|doutorado|tecnico|curso",
      "data_inicio": "YYYY-MM-DD ou null",
      "data_conclusao": "YYYY-MM-DD ou null",
      "em_progresso": 0
    }
  ],
  "habilidades": [
    {
      "nome": "string",
      "proficiencia": "basico|intermediario|avancado|especialista",
      "categoria": "juridica|tecnica|comportamental ou null"
    }
  ],
  "idiomas": [
    {
      "nome": "string",
      "proficiencia": "basico|intermediario|avancado|fluente|nativo"
    }
  ],
  "certificacoes": [
    {
      "nome": "string",
      "emissor": "string",
      "data_emissao": "YYYY-MM-DD ou null",
      "data_expiracao": "YYYY-MM-DD ou null",
      "url": "string ou null"
    }
  ]
}

Currículo:
"""


def extrair_texto_pdf(conteudo: bytes) -> str:
    import pdfplumber
    texto = []
    with pdfplumber.open(io.BytesIO(conteudo)) as pdf:
        for pagina in pdf.pages:
            t = pagina.extract_text()
            if t:
                texto.append(t)
    return "\n".join(texto)


def extrair_texto_docx(conteudo: bytes) -> str:
    import docx
    doc = docx.Document(io.BytesIO(conteudo))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def processar_curriculo_com_ia(texto: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY não configurada. Adicione a chave ao arquivo .env.")

    import google.generativeai as genai
    genai.configure(api_key=api_key)
    modelo = genai.GenerativeModel("gemini-2.5-flash")

    resposta = modelo.generate_content(_PROMPT + texto)
    texto_resposta = resposta.text.strip()

    if texto_resposta.startswith("```"):
        linhas = texto_resposta.split("\n")
        texto_resposta = "\n".join(linhas[1:-1])

    return json.loads(texto_resposta)
