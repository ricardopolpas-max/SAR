import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


def _gerar_gemini(prompt: str) -> str:
    from google import genai
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY não configurada.")
    client = genai.Client(api_key=api_key)
    modelo = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    response = client.models.generate_content(model=modelo, contents=prompt)
    return response.text.strip()


def _gerar_groq(prompt: str) -> str:
    import openai
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY não configurada.")
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    resp = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()


_PROVEDORES = {
    "gemini": _gerar_gemini,
    "groq":   _gerar_groq,
}


def gerar_conteudo(prompt: str) -> str:
    provedor = os.getenv("IA_PROVIDER", "gemini").strip().lower()
    fallback  = os.getenv("IA_FALLBACK", "").strip().lower()

    fn = _PROVEDORES.get(provedor)
    if not fn:
        raise ValueError(f"Provedor desconhecido: '{provedor}'. Opções: {', '.join(_PROVEDORES)}")

    try:
        return fn(prompt)
    except Exception as e:
        msg = str(e).lower()
        if fallback and fallback in _PROVEDORES and fallback != provedor:
            if "429" in msg or "quota" in msg or "limit" in msg or "rate" in msg:
                print(f"[IA] {provedor} retornou cota esgotada — usando fallback: {fallback}")
                return _PROVEDORES[fallback](prompt)
        raise
