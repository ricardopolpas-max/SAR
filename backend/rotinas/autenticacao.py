# backend/rotinas/autenticacao.py
# Utilitários de autenticação: hash de senha, geração e validação de token de sessão.

import uuid
import bcrypt
from datetime import datetime, timezone, timedelta

from rotinas.genericas import db_selecionar, db_inserir, db_excluir

_TOKEN_VALIDADE_HORAS = 24


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, hash_salvo: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), hash_salvo.encode("utf-8"))


def criar_token(id_candidato: int) -> str:
    token = str(uuid.uuid4())
    expira_em = (
        datetime.now(timezone.utc) + timedelta(hours=_TOKEN_VALIDADE_HORAS)
    ).isoformat()
    db_inserir("sessoes", {
        "token":        token,
        "id_candidato": id_candidato,
        "expira_em":    expira_em,
    })
    return token


def validar_token(token: str) -> int | None:
    """Retorna id_candidato se o token for válido e não expirado, senão None."""
    sessao = db_selecionar("sessoes", condicao={"token": token}, unico=True)
    if not sessao:
        return None
    if sessao["expira_em"] < datetime.now(timezone.utc).isoformat():
        db_excluir("sessoes", {"token": token})
        return None
    return sessao["id_candidato"]


def revogar_token(token: str) -> None:
    db_excluir("sessoes", {"token": token})
