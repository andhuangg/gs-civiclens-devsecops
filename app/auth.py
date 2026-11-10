import os
from datetime import datetime, timedelta, timezone

import jwt

ALGORITMO = "HS256"
TAMANHO_MINIMO_CHAVE = 32


def _chave() -> str:
    chave = os.getenv("JWT_SECRET_KEY", "")
    if len(chave) < TAMANHO_MINIMO_CHAVE:
        raise RuntimeError("JWT_SECRET_KEY ausente ou com menos de 32 caracteres")
    return chave


def gerar_token(usuario: str, minutos: int = 30) -> str:
    agora = datetime.now(timezone.utc)
    payload = {"sub": usuario, "iat": agora, "exp": agora + timedelta(minutes=minutos)}
    return jwt.encode(payload, _chave(), algorithm=ALGORITMO)


def validar_token(token: str) -> str:
    return jwt.decode(token, _chave(), algorithms=[ALGORITMO])["sub"]


def extrair_usuario(token: str) -> str:
    return validar_token(token)
