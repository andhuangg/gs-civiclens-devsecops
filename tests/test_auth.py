import jwt
import pytest

from app.auth import gerar_token, validar_token


def test_gerar_e_validar_token():
    token = gerar_token("cidadao@civiclens.local")
    assert validar_token(token) == "cidadao@civiclens.local"


def test_token_expirado():
    token = gerar_token("cidadao@civiclens.local", minutos=-1)
    with pytest.raises(jwt.ExpiredSignatureError):
        validar_token(token)
