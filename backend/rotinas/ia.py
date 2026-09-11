import os
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# Erros que indicam cota/rate-limit esgotados — tenta próximo provedor
_ERROS_COTA = ("429", "503", "quota", "limit", "rate", "insufficient", "exhausted", "unavailable", "overloaded")


def _cota_esgotada(msg: str) -> bool:
    return any(p in msg.lower() for p in _ERROS_COTA)


# ------------------------------------------------------------
# RESOLUÇÃO INTELIGENTE DE MODELO
# ------------------------------------------------------------
# O provedor pode descontinuar um modelo a qualquer momento (foi o que a Groq
# fez com os Llama). Em vez de confiar cegamente no nome fixo do .env, a rotina
# consulta a lista de modelos que a chave realmente enxerga e escolhe um válido.
# O valor do .env vira PREFERÊNCIA, não obrigação.

# Ordem de preferência quando o modelo do .env não está disponível
_PREF_MODELO = {
    "gemini": ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite",
               "gemini-2.0-flash", "gemini-pro-latest"],
    "groq":   ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b",
               "qwen/qwen3.6-27b", "groq/compound"],
}

# Palavras que denunciam modelos não-conversacionais (áudio, imagem, guarda…)
_MODELO_NAO_CHAT = ("whisper", "orpheus", "-tts", "guard", "embed", "lyria",
                    "image", "transcribe", "computer-use", "robotics", "deep-research")

_MODELO_TTL = 3600  # 1h
_modelo_cache: dict[str, tuple[str, float]] = {}  # tipo -> (modelo, timestamp)


def _modelos_disponiveis(tipo: str, api_key: str) -> set[str]:
    if tipo == "gemini":
        from google import genai
        client = genai.Client(api_key=api_key)   # manter referência: o GC fecha o HTTP client se for temporário
        disp = set()
        for m in client.models.list():
            acoes = getattr(m, "supported_actions", None) or \
                    getattr(m, "supported_generation_methods", []) or []
            if "generateContent" in acoes:
                disp.add(m.name.replace("models/", ""))
        return disp
    else:  # groq — via SDK openai (passa pela Cloudflare)
        import openai
        client = openai.OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        return {m.id for m in client.models.list().data}


def _resolver_modelo(tipo: str, api_key: str) -> str:
    pref_env = os.getenv("GEMINI_MODEL" if tipo == "gemini" else "GROQ_MODEL", "").strip()

    cached = _modelo_cache.get(tipo)
    if cached and time.time() - cached[1] < _MODELO_TTL:
        return cached[0]

    try:
        disp = _modelos_disponiveis(tipo, api_key)
    except Exception as e:
        # Sem lista → tenta o do .env; se vazio, o 1º da preferência
        print(f"[IA] {tipo}: não consegui listar modelos ({type(e).__name__}) — usando '{pref_env or _PREF_MODELO[tipo][0]}'")
        return pref_env or _PREF_MODELO[tipo][0]

    if pref_env and pref_env in disp:
        escolhido = pref_env
    else:
        escolhido = next((m for m in _PREF_MODELO[tipo] if m in disp), None)
        if not escolhido:
            chat = sorted(m for m in disp if not any(p in m.lower() for p in _MODELO_NAO_CHAT))
            escolhido = chat[0] if chat else (pref_env or _PREF_MODELO[tipo][0])
        if pref_env:
            print(f"[IA] {tipo}: modelo '{pref_env}' indisponível → usando '{escolhido}'")

    _modelo_cache[tipo] = (escolhido, time.time())
    return escolhido


def _gerar_gemini(api_key: str, prompt: str) -> str:
    from google import genai
    client = genai.Client(api_key=api_key)
    modelo = _resolver_modelo("gemini", api_key)
    response = client.models.generate_content(model=modelo, contents=prompt)
    return response.text.strip()


def _gerar_groq(api_key: str, prompt: str) -> str:
    import openai
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    resp = client.chat.completions.create(
        model=_resolver_modelo("groq", api_key),
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
            print(f"[IA] {nome} — falhou ({type(e).__name__}: {e}), tentando próximo...")
            continue

    raise RuntimeError(
        f"Todos os provedores esgotaram a cota. Último erro: {ultimo_erro}"
    )
