import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# Erros que indicam cota/rate-limit esgotados — tenta próximo provedor
_ERROS_COTA = ("429", "quota", "limit", "rate", "insufficient", "exhausted")


def _cota_esgotada(msg: str) -> bool:
    return any(p in msg.lower() for p in _ERROS_COTA)


def _gerar_gemini(api_key: str, prompt: str) -> str:
    from google import genai
    client = genai.Client(api_key=api_key)
    modelo = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    response = client.models.generate_content(model=modelo, contents=prompt)
    return response.text.strip()


def _gerar_groq(api_key: str, prompt: str) -> str:
    import openai
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    resp = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()


# Mapa de tipo → função geradora (recebe api_key, prompt)
_TIPO_FN = {
    "gemini": _gerar_gemini,
    "groq":   _gerar_groq,
}


def _resolver_provedores() -> list[tuple[str, str]]:
    """
    Lê IA_PROVIDERS do .env e resolve cada entrada para (tipo, api_key).

    Formato do .env:
        IA_PROVIDERS=gemini,groq_1,groq_2,groq_3

    Chaves esperadas:
        GEMINI_API_KEY        → para entradas do tipo "gemini"
        GROQ_API_KEY_1        → para "groq_1"
        GROQ_API_KEY_2        → para "groq_2"
        GROQ_API_KEY          → para "groq" (compatibilidade legada)

    Para adicionar mais um Groq: inclua "groq_4" em IA_PROVIDERS
    e adicione GROQ_API_KEY_4 no .env — sem alterar o código.
    """
    lista_raw = os.getenv("IA_PROVIDERS", "gemini,groq").strip()
    provedores = []

    for entrada in lista_raw.split(","):
        entrada = entrada.strip().lower()
        if not entrada:
            continue

        if entrada == "gemini":
            api_key = os.getenv("GEMINI_API_KEY", "").strip()
            tipo = "gemini"
        elif entrada.startswith("groq"):
            # groq → GROQ_API_KEY | groq_1 → GROQ_API_KEY_1
            sufixo = entrada[4:]                          # "" | "_1" | "_2" …
            var    = "GROQ_API_KEY" + sufixo.upper()
            api_key = os.getenv(var, "").strip()
            tipo = "groq"
        else:
            print(f"[IA] Tipo desconhecido ignorado: '{entrada}'")
            continue

        if not api_key:
            print(f"[IA] Chave não configurada para '{entrada}' — ignorado.")
            continue

        provedores.append((entrada, tipo, api_key))

    return provedores


def gerar_conteudo(prompt: str) -> str:
    provedores = _resolver_provedores()

    if not provedores:
        raise RuntimeError("Nenhum provedor de IA configurado. Verifique IA_PROVIDERS e as chaves no .env.")

    ultimo_erro = None
    for nome, tipo, api_key in provedores:
        fn = _TIPO_FN.get(tipo)
        if not fn:
            continue
        try:
            return fn(api_key, prompt)
        except Exception as e:
            ultimo_erro = e
            if _cota_esgotada(str(e)):
                print(f"[IA] {nome} — cota esgotada, tentando próximo...")
                continue
            # Erro não relacionado a cota — propaga imediatamente
            raise

    raise RuntimeError(
        f"Todos os provedores esgotaram a cota. Último erro: {ultimo_erro}"
    )
