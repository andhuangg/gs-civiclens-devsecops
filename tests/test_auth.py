import jwt
import pytest

from app.auth import extrair_usuario, gerar_token, validar_token


@pytest.fixture(autouse=True)
def chave_jwt(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "chave-de-teste-com-mais-de-32-caracteres")


def test_gerar_e_validar_token():
    token = gerar_token("cidadao@civiclens.local")
    assert validar_token(token) == "cidadao@civiclens.local"


def test_token_expirado():
    token = gerar_token("cidadao@civiclens.local", minutos=-1)
    with pytest.raises(jwt.ExpiredSignatureError):
        validar_token(token)


def test_extrair_usuario():
    token = gerar_token("fiscal@civiclens.local")
    assert extrair_usuario(token) == "fiscal@civiclens.local"


def test_extrair_usuario_rejeita_token_adulterado():
    token = gerar_token("fiscal@civiclens.local")
    cabecalho, payload, _ = token.split(".")
    with pytest.raises(jwt.InvalidSignatureError):
        extrair_usuario(f"{cabecalho}.{payload}.assinatura-falsa")


def test_chave_ausente_ou_curta(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "curta")
    with pytest.raises(RuntimeError):
        gerar_token("cidadao@civiclens.local")
