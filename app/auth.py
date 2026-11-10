from datetime import datetime, timedelta, timezone

import jwt

SECRET_KEY = "civiclens-lite-chave-jwt-2026"
ALGORITMO = "HS256"


def gerar_token(usuario: str, minutos: int = 30) -> str:
    agora = datetime.now(timezone.utc)
    payload = {"sub": usuario, "iat": agora, "exp": agora + timedelta(minutes=minutos)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITMO)


def validar_token(token: str) -> str:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO])["sub"]


def extrair_usuario(token: str) -> str:
    return jwt.decode(token, options={"verify_signature": False})["sub"]
