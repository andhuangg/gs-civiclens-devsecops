from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

NOVA_OCORRENCIA = {
    "titulo": "Lixo acumulado na esquina",
    "descricao": "Descarte irregular de entulho e lixo doméstico há vários dias.",
    "categoria": "saneamento",
    "severidade": "alta",
    "latitude": -23.55,
    "longitude": -46.63,
    "endereco": "Rua Augusta, 900, São Paulo/SP",
}


def test_health():
    resposta = client.get("/health")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "ok"
    assert corpo["service"] == "civiclens-lite"


def test_listar_ocorrencias_retorna_exemplos():
    resposta = client.get("/api/v1/ocorrencias")
    assert resposta.status_code == 200
    assert len(resposta.json()) >= 3


def test_filtrar_por_categoria():
    resposta = client.get("/api/v1/ocorrencias", params={"categoria": "iluminacao"})
    assert resposta.status_code == 200
    assert all(o["categoria"] == "iluminacao" for o in resposta.json())


def test_criar_e_obter_ocorrencia():
    criada = client.post("/api/v1/ocorrencias", json=NOVA_OCORRENCIA)
    assert criada.status_code == 201
    corpo = criada.json()
    assert corpo["status"] == "recebida"
    assert corpo["protocolo"].startswith("CL-")

    obtida = client.get(f"/api/v1/ocorrencias/{corpo['id']}")
    assert obtida.status_code == 200
    assert obtida.json()["titulo"] == NOVA_OCORRENCIA["titulo"]


def test_criar_ocorrencia_invalida():
    invalida = {**NOVA_OCORRENCIA, "latitude": 200, "categoria": "inexistente"}
    resposta = client.post("/api/v1/ocorrencias", json=invalida)
    assert resposta.status_code == 422


def test_ocorrencia_inexistente():
    assert client.get("/api/v1/ocorrencias/99999").status_code == 404
    resposta = client.patch("/api/v1/ocorrencias/99999/status", json={"status": "em_andamento"})
    assert resposta.status_code == 404


def test_fluxo_de_status():
    criada = client.post("/api/v1/ocorrencias", json=NOVA_OCORRENCIA).json()
    url = f"/api/v1/ocorrencias/{criada['id']}/status"

    andamento = client.patch(url, json={"status": "em_andamento"})
    assert andamento.status_code == 200
    assert andamento.json()["status"] == "em_andamento"

    resolvida = client.patch(url, json={"status": "resolvida"})
    assert resolvida.status_code == 200

    filtradas = client.get("/api/v1/ocorrencias", params={"status": "resolvida"}).json()
    assert any(o["id"] == criada["id"] for o in filtradas)


def test_transicao_invalida():
    criada = client.post("/api/v1/ocorrencias", json=NOVA_OCORRENCIA).json()
    resposta = client.patch(
        f"/api/v1/ocorrencias/{criada['id']}/status", json={"status": "resolvida"}
    )
    assert resposta.status_code == 409


def test_estatisticas():
    resposta = client.get("/api/v1/estatisticas")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] >= 3
    assert set(corpo["por_status"]) == {"recebida", "em_andamento", "resolvida", "rejeitada"}
