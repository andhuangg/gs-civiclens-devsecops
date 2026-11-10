#!/bin/sh
set -eu

BASE_URL="${1:-http://localhost:8000}"
EXPECTED_VERSION="${2:-}"

echo "Validando aplicação em $BASE_URL"

tentativas=0
until curl -fsS "$BASE_URL/health" >/tmp/health.json 2>/dev/null; do
    tentativas=$((tentativas + 1))
    if [ "$tentativas" -ge 30 ]; then
        echo "FALHA: /health não respondeu após 60s"
        exit 1
    fi
    sleep 2
done

echo "GET /health -> $(cat /tmp/health.json)"
if [ -n "$EXPECTED_VERSION" ]; then
    versao=$(jq -r '.version' /tmp/health.json)
    if [ "$versao" != "$EXPECTED_VERSION" ]; then
        echo "FALHA: versão em execução ($versao) diferente da esperada ($EXPECTED_VERSION)"
        exit 1
    fi
    echo "OK: versão em execução confere ($versao)"
fi

total=$(curl -fsS "$BASE_URL/api/v1/ocorrencias" | jq 'length')
echo "GET /api/v1/ocorrencias -> $total ocorrências"
[ "$total" -ge 1 ] || { echo "FALHA: listagem vazia"; exit 1; }

codigo=$(curl -sS -o /tmp/criada.json -w '%{http_code}' -X POST "$BASE_URL/api/v1/ocorrencias" \
    -H 'Content-Type: application/json' \
    -d '{"titulo":"Validação pós-deploy","descricao":"Ocorrência criada pelo smoke test da pipeline.","categoria":"outros","severidade":"baixa","latitude":-23.55,"longitude":-46.63}')
echo "POST /api/v1/ocorrencias -> HTTP $codigo, protocolo $(jq -r '.protocolo' /tmp/criada.json)"
[ "$codigo" = "201" ] || { echo "FALHA: esperado HTTP 201"; exit 1; }

echo "GET /api/v1/estatisticas -> $(curl -fsS "$BASE_URL/api/v1/estatisticas")"
echo "Validação funcional concluída com sucesso"
