from datetime import datetime, timezone
from threading import Lock

from app.models import (
    TRANSICOES_VALIDAS,
    Categoria,
    Ocorrencia,
    OcorrenciaCriar,
    Severidade,
    Status,
)


class OcorrenciaNaoEncontrada(Exception):
    pass


class TransicaoInvalida(Exception):
    pass


class RepositorioOcorrencias:
    def __init__(self) -> None:
        self._dados: dict[int, Ocorrencia] = {}
        self._proximo_id = 1
        self._lock = Lock()

    def criar(self, dados: OcorrenciaCriar) -> Ocorrencia:
        with self._lock:
            agora = datetime.now(timezone.utc)
            ocorrencia = Ocorrencia(
                **dados.model_dump(),
                id=self._proximo_id,
                protocolo=f"CL-{agora:%Y}-{self._proximo_id:05d}",
                criada_em=agora,
                atualizada_em=agora,
            )
            self._dados[ocorrencia.id] = ocorrencia
            self._proximo_id += 1
            return ocorrencia

    def listar(
        self,
        status: Status | None = None,
        categoria: Categoria | None = None,
    ) -> list[Ocorrencia]:
        itens = list(self._dados.values())
        if status:
            itens = [o for o in itens if o.status == status]
        if categoria:
            itens = [o for o in itens if o.categoria == categoria]
        return itens

    def obter(self, ocorrencia_id: int) -> Ocorrencia:
        ocorrencia = self._dados.get(ocorrencia_id)
        if ocorrencia is None:
            raise OcorrenciaNaoEncontrada(ocorrencia_id)
        return ocorrencia

    def atualizar_status(self, ocorrencia_id: int, novo: Status) -> Ocorrencia:
        with self._lock:
            ocorrencia = self.obter(ocorrencia_id)
            if novo not in TRANSICOES_VALIDAS[ocorrencia.status]:
                raise TransicaoInvalida(f"{ocorrencia.status.value} -> {novo.value}")
            atualizada = ocorrencia.model_copy(
                update={"status": novo, "atualizada_em": datetime.now(timezone.utc)}
            )
            self._dados[ocorrencia_id] = atualizada
            return atualizada

    def estatisticas(self) -> dict:
        itens = list(self._dados.values())
        return {
            "total": len(itens),
            "por_status": {s.value: sum(o.status == s for o in itens) for s in Status},
            "por_severidade": {
                s.value: sum(o.severidade == s for o in itens) for s in Severidade
            },
        }


def carregar_exemplos(repo: RepositorioOcorrencias) -> None:
    exemplos = [
        OcorrenciaCriar(
            titulo="Buraco na Avenida Paulista",
            descricao="Buraco grande na faixa da direita próximo ao número 1500.",
            categoria=Categoria.VIAS,
            severidade=Severidade.ALTA,
            latitude=-23.5614,
            longitude=-46.6559,
            endereco="Av. Paulista, 1500, São Paulo/SP",
        ),
        OcorrenciaCriar(
            titulo="Poste apagado na praça",
            descricao="Iluminação pública apagada há uma semana na praça central.",
            categoria=Categoria.ILUMINACAO,
            severidade=Severidade.MEDIA,
            latitude=-23.5505,
            longitude=-46.6333,
            endereco="Praça da Sé, São Paulo/SP",
        ),
        OcorrenciaCriar(
            titulo="Vazamento de água na calçada",
            descricao="Vazamento contínuo de água limpa vindo da rede pública.",
            categoria=Categoria.AGUA,
            severidade=Severidade.CRITICA,
            latitude=-23.5880,
            longitude=-46.6320,
            endereco="Rua Vergueiro, 3000, São Paulo/SP",
        ),
    ]
    for exemplo in exemplos:
        repo.criar(exemplo)
