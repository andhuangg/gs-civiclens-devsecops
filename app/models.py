from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Status(str, Enum):
    RECEBIDA = "recebida"
    EM_ANDAMENTO = "em_andamento"
    RESOLVIDA = "resolvida"
    REJEITADA = "rejeitada"


class Severidade(str, Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class Categoria(str, Enum):
    VIAS = "vias"
    AGUA = "agua"
    SANEAMENTO = "saneamento"
    ENERGIA = "energia"
    ILUMINACAO = "iluminacao"
    DRENAGEM = "drenagem"
    PATRIMONIO_PUBLICO = "patrimonio_publico"
    SEGURANCA = "seguranca"
    MEIO_AMBIENTE = "meio_ambiente"
    OUTROS = "outros"


TRANSICOES_VALIDAS: dict[Status, set[Status]] = {
    Status.RECEBIDA: {Status.EM_ANDAMENTO, Status.REJEITADA},
    Status.EM_ANDAMENTO: {Status.RESOLVIDA, Status.REJEITADA},
    Status.RESOLVIDA: set(),
    Status.REJEITADA: set(),
}


class OcorrenciaCriar(BaseModel):
    titulo: str = Field(min_length=5, max_length=120)
    descricao: str = Field(min_length=10, max_length=2000)
    categoria: Categoria
    severidade: Severidade = Severidade.MEDIA
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    endereco: str | None = Field(default=None, max_length=300)


class Ocorrencia(OcorrenciaCriar):
    id: int
    protocolo: str
    status: Status = Status.RECEBIDA
    criada_em: datetime
    atualizada_em: datetime


class AtualizarStatus(BaseModel):
    status: Status
