pipeline {
    agent any

    triggers {
        githubPush()
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '30'))
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        AWS_REGION      = 'us-east-1'
        IMAGE_NAME      = 'civiclens-lite'
        PYTHON_IMAGE    = 'python:3.14.10-alpine3.24'
        TRIVY_CACHE_DIR = '/var/jenkins_home/.cache/trivy'
        APP_URL         = 'http://civiclens-app:8000'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_SHORT = sh(script: 'git rev-parse --short=7 HEAD', returnStdout: true).trim()
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_SHORT}"
                    env.IMAGE_REPO = "${env.ECR_REGISTRY}/${env.IMAGE_NAME}"
                    env.IMAGE_URI = "${env.IMAGE_REPO}:${env.IMAGE_TAG}"
                    currentBuild.description = "imagem ${env.IMAGE_TAG}"
                }
                sh 'git log -1 --pretty="Commit: %h | Autor: %an | Mensagem: %s"'
                sh 'mkdir -p reports'
            }
        }

        stage('Testes automatizados') {
            steps {
                sh '''
                    docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp \
                        -v "$WORKSPACE":"$WORKSPACE" -w "$WORKSPACE" "$PYTHON_IMAGE" \
                        sh -c "python -m venv /tmp/venv && /tmp/venv/bin/pip install -q -r requirements-dev.txt && /tmp/venv/bin/pytest"
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                }
            }
        }

        stage('Análise SonarQube') {
            steps {
                script {
                    def scannerHome = tool 'sonar-scanner'
                    withSonarQubeEnv('sonarqube') {
                        sh "${scannerHome}/bin/sonar-scanner -Dsonar.projectVersion=${env.IMAGE_TAG}"
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker build --pull \
                        --build-arg APP_VERSION="$IMAGE_TAG" \
                        -t "$IMAGE_URI" -t "$IMAGE_REPO:latest" .
                    docker image ls "$IMAGE_REPO"
                '''
            }
        }

        stage('Trivy Scan') {
            steps {
                sh '''
                    trivy image --cache-dir "$TRIVY_CACHE_DIR" --scanners vuln --download-db-only

                    trivy image --cache-dir "$TRIVY_CACHE_DIR" --scanners vuln --skip-db-update \
                        --severity HIGH,CRITICAL --format table "$IMAGE_URI" | tee reports/trivy-report.txt

                    trivy image --cache-dir "$TRIVY_CACHE_DIR" --scanners vuln --skip-db-update \
                        --format json --output reports/trivy-report.json "$IMAGE_URI"

                    trivy image --cache-dir "$TRIVY_CACHE_DIR" --scanners vuln --skip-db-update \
                        --format template --template "@/opt/trivy/html.tpl" \
                        --output reports/trivy-report.html "$IMAGE_URI"

                    echo "Resumo de vulnerabilidades por severidade:"
                    jq '[.Results[]?.Vulnerabilities[]?.Severity] | group_by(.) | map({(.[0]): length}) | add // {}' reports/trivy-report.json

                    trivy image --cache-dir "$TRIVY_CACHE_DIR" --scanners vuln --skip-db-update \
                        --severity CRITICAL --exit-code 1 --format table "$IMAGE_URI"
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/trivy-report.*', allowEmptyArchive: true
                    publishHTML(target: [
                        reportName: 'Relatorio Trivy',
                        reportDir: 'reports',
                        reportFiles: 'trivy-report.html',
                        keepAll: true,
                        alwaysLinkToLastBuild: true,
                        allowMissing: true
                    ])
                }
            }
        }

        stage('Publicação no ECR') {
            steps {
                sh '''
                    aws ecr get-login-password --region "$AWS_REGION" \
                        | docker login --username AWS --password-stdin "$ECR_REGISTRY"
                    docker push "$IMAGE_URI"
                    docker push "$IMAGE_REPO:latest"
                    aws ecr describe-images --region "$AWS_REGION" --repository-name "$IMAGE_NAME" \
                        --image-ids imageTag="$IMAGE_TAG" \
                        --query 'imageDetails[0].{tags:imageTags,digest:imageDigest,pushedAt:imagePushedAt}'
                '''
            }
        }

        stage('Deploy (Docker Compose)') {
            steps {
                sh '''
                    docker network inspect devsecops >/dev/null 2>&1 || docker network create devsecops
                    IMAGE="$IMAGE_URI" docker compose -p civiclens up -d --remove-orphans
                    docker compose -p civiclens ps
                '''
            }
        }

        stage('Validação funcional') {
            steps {
                sh './scripts/smoke-test.sh "$APP_URL" "$IMAGE_TAG" | tee reports/smoke-test.txt'
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**, coverage.xml, test-results.xml', allowEmptyArchive: true
            sh 'docker image prune -f >/dev/null 2>&1 || true'
        }
        success {
            echo "Pipeline concluída: ${env.IMAGE_URI} publicada e em execução."
        }
        failure {
            echo 'Pipeline bloqueada. Verifique o estágio que falhou nos logs acima.'
        }
    }
}
