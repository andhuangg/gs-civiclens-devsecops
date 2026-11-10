from fastapi import FastAPI, HTTPException, Query, status

from app import __version__
from app.models import AtualizarStatus, Categoria, Ocorrencia, OcorrenciaCriar, Status
from app.repository import (
    OcorrenciaNaoEncontrada,
    RepositorioOcorrencias,
    TransicaoInvalida,
    carregar_exemplos,
)

app = FastAPI(
    title="CivicLens Lite",
    version=__version__,
    description="API de registro e acompanhamento de ocorrências urbanas (CitizenTech).",
)

repositorio = RepositorioOcorrencias()
carregar_exemplos(repositorio)


@app.get("/health", tags=["infra"])
def health() -> dict:
    return {"status": "ok", "service": "civiclens-lite", "version": __version__}


@app.get("/api/v1/ocorrencias", response_model=list[Ocorrencia], tags=["ocorrencias"])
def listar_ocorrencias(
    status_filtro: Status | None = Query(default=None, alias="status"),
    categoria: Categoria | None = None,
) -> list[Ocorrencia]:
    return repositorio.listar(status=status_filtro, categoria=categoria)


@app.get("/api/v1/ocorrencias/{ocorrencia_id}", response_model=Ocorrencia, tags=["ocorrencias"])
def obter_ocorrencia(ocorrencia_id: int) -> Ocorrencia:
    try:
        return repositorio.obter(ocorrencia_id)
    except OcorrenciaNaoEncontrada:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")


@app.post(
    "/api/v1/ocorrencias",
    response_model=Ocorrencia,
    status_code=status.HTTP_201_CREATED,
    tags=["ocorrencias"],
)
def criar_ocorrencia(dados: OcorrenciaCriar) -> Ocorrencia:
    return repositorio.criar(dados)


@app.patch(
    "/api/v1/ocorrencias/{ocorrencia_id}/status",
    response_model=Ocorrencia,
    tags=["ocorrencias"],
)
def atualizar_status(ocorrencia_id: int, dados: AtualizarStatus) -> Ocorrencia:
    try:
        return repositorio.atualizar_status(ocorrencia_id, dados.status)
    except OcorrenciaNaoEncontrada:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    except TransicaoInvalida as erro:
        raise HTTPException(status_code=409, detail=f"Transição de status inválida: {erro}")


@app.get("/api/v1/estatisticas", tags=["ocorrencias"])
def estatisticas() -> dict:
    return repositorio.estatisticas()
