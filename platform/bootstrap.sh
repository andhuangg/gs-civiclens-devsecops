#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
ENV_FILE=.env
SONAR_URL=http://localhost:9000

gerar_senha() {
    echo "$(openssl rand -base64 18 | tr -dc 'A-Za-z0-9' | head -c 16)Aa1!"
}

imds() {
    local token
    token=$(curl -fsS -X PUT http://169.254.169.254/latest/api/token -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
    curl -fsS -H "X-aws-ec2-metadata-token: $token" "http://169.254.169.254/latest/$1"
}

if [ ! -f "$ENV_FILE" ]; then
    account_id=$(imds dynamic/instance-identity/document | jq -r .accountId)
    region=$(imds dynamic/instance-identity/document | jq -r .region)
    public_ip=$(imds meta-data/public-ipv4)
    cat > "$ENV_FILE" <<ENV
JENKINS_ADMIN_PASSWORD=$(gerar_senha)
SONAR_ADMIN_PASSWORD=$(gerar_senha)
SONAR_DB_PASSWORD=$(gerar_senha)
SONAR_TOKEN=
ECR_REGISTRY=${account_id}.dkr.ecr.${region}.amazonaws.com
JENKINS_PUBLIC_URL=http://${public_ip}:8080/
DOCKER_GID=$(getent group docker | cut -d: -f3)
ENV
    chmod 600 "$ENV_FILE"
fi

grep -q '^SONAR_WEBHOOK_SECRET=' "$ENV_FILE" || echo "SONAR_WEBHOOK_SECRET=$(openssl rand -hex 24)" >> "$ENV_FILE"

set -a
. "./$ENV_FILE"
set +a

docker network inspect devsecops >/dev/null 2>&1 || docker network create devsecops
sudo mkdir -p /var/jenkins_home
sudo chown 1000:1000 /var/jenkins_home

docker compose up -d sonar-db sonarqube

echo "Aguardando SonarQube ficar disponível..."
until [ "$(curl -fsS "$SONAR_URL/api/system/status" 2>/dev/null | jq -r .status)" = "UP" ]; do
    sleep 5
done

if curl -fsS -u admin:admin "$SONAR_URL/api/authentication/validate" | jq -e '.valid' >/dev/null; then
    curl -fsS -u admin:admin -X POST "$SONAR_URL/api/users/change_password" \
        --data-urlencode "login=admin" \
        --data-urlencode "previousPassword=admin" \
        --data-urlencode "password=$SONAR_ADMIN_PASSWORD"
fi

SONAR_AUTH="admin:$SONAR_ADMIN_PASSWORD"

if [ -z "$SONAR_TOKEN" ]; then
    SONAR_TOKEN=$(curl -fsS -u "$SONAR_AUTH" -X POST "$SONAR_URL/api/user_tokens/generate" \
        --data-urlencode "name=jenkins-pipeline" \
        --data-urlencode "type=GLOBAL_ANALYSIS_TOKEN" | jq -r .token)
    sed -i "s|^SONAR_TOKEN=.*|SONAR_TOKEN=$SONAR_TOKEN|" "$ENV_FILE"
fi

WEBHOOK_URL="${JENKINS_PUBLIC_URL}sonarqube-webhook/"
WEBHOOK_KEY=$(curl -fsS -u "$SONAR_AUTH" "$SONAR_URL/api/webhooks/list" | jq -r '.webhooks[] | select(.name=="jenkins") | .key')
if [ -z "$WEBHOOK_KEY" ]; then
    curl -fsS -u "$SONAR_AUTH" -X POST "$SONAR_URL/api/webhooks/create" \
        --data-urlencode "name=jenkins" \
        --data-urlencode "url=$WEBHOOK_URL" \
        --data-urlencode "secret=$SONAR_WEBHOOK_SECRET" >/dev/null
else
    curl -fsS -u "$SONAR_AUTH" -X POST "$SONAR_URL/api/webhooks/update" \
        --data-urlencode "webhook=$WEBHOOK_KEY" \
        --data-urlencode "name=jenkins" \
        --data-urlencode "url=$WEBHOOK_URL" \
        --data-urlencode "secret=$SONAR_WEBHOOK_SECRET"
fi

GATE="CivicLens Gate"
if ! curl -fsS -u "$SONAR_AUTH" "$SONAR_URL/api/qualitygates/list" | jq -e --arg g "$GATE" '.qualitygates[] | select(.name==$g)' >/dev/null; then
    curl -fsS -u "$SONAR_AUTH" -X POST "$SONAR_URL/api/qualitygates/create" --data-urlencode "name=$GATE"
    while read -r metric op error; do
        curl -fsS -u "$SONAR_AUTH" -X POST "$SONAR_URL/api/qualitygates/create_condition" \
            --data-urlencode "gateName=$GATE" \
            --data-urlencode "metric=$metric" \
            --data-urlencode "op=$op" \
            --data-urlencode "error=$error" >/dev/null
    done <<CONDITIONS
coverage LT 80
reliability_rating GT 1
security_rating GT 1
sqale_rating GT 1
duplicated_lines_density GT 3
CONDITIONS
fi
curl -fsS -u "$SONAR_AUTH" -X POST "$SONAR_URL/api/qualitygates/set_as_default" --data-urlencode "name=$GATE"

docker compose up -d --build jenkins

echo "Plataforma pronta."
echo "Jenkins:   $JENKINS_PUBLIC_URL (usuário admin, senha em platform/.env)"
echo "SonarQube: ${JENKINS_PUBLIC_URL%:8080/}:9000 (usuário admin, senha em platform/.env)"
