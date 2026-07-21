pipeline {
    // Pipeline-ul poate rula pe orice agent Jenkins disponibil.
    agent any

    options {
        // Împiedică două build-uri ale aceluiași job să ruleze simultan.
        // Este important pentru a evita două deployment-uri Blue/Green în același timp.
        disableConcurrentBuilds()
    }

    environment {
        /*
         * Imagine temporară folosită doar în Pipeline 1
         * pentru linting și teste pe Pull Request.
         */
        CI_IMAGE = "study4u-ci:${BUILD_NUMBER}"

        /*
         * Configurația GitHub Container Registry.
         */
        REGISTRY = "ghcr.io"
        REGISTRY_NAMESPACE = "paul1919ucj"

        /*
         * Imaginile folosite de Pipeline 2 pentru mediul Staging.
         * BUILD_NUMBER oferă un tag unic fiecărui build Jenkins.
         */
        BACKEND_IMAGE = "${REGISTRY}/${REGISTRY_NAMESPACE}/study4u-backend:${BUILD_NUMBER}"
        FRONTEND_IMAGE = "${REGISTRY}/${REGISTRY_NAMESPACE}/study4u-frontend:${BUILD_NUMBER}"

        /*
         * Imaginea folosită de Pipeline 3 în Production.
         * Exemplu:
         * ghcr.io/paul1919ucj/study4u-backend:production-5
         */
        PRODUCTION_TAG = "production-${BUILD_NUMBER}"
        PRODUCTION_IMAGE = "${REGISTRY}/${REGISTRY_NAMESPACE}/study4u-backend:${PRODUCTION_TAG}"

        /*
         * Datele serverului AWS EC2.
         */
        EC2_HOST = "35.159.70.167"
        EC2_PRODUCTION_DIR = "/home/ubuntu/study4u/production"
    }

    stages {
        stage('Checkout') {
            steps {
                /*
                 * Descarcă branch-ul sau Pull Request-ul
                 * care a declanșat build-ul.
                 */
                checkout scm
            }
        }

        stage('Verify Docker') {
            steps {
                /*
                 * Verifică dacă Docker și Docker Compose
                 * sunt disponibile pe serverul Jenkins.
                 */
                sh 'docker --version'
                sh 'docker compose version'
            }
        }

        /*
         * ==========================================================
         * PIPELINE 1
         * Validare CI pentru Pull Request către branch-ul main
         * ==========================================================
         */

        stage('PR - Docker Build') {
            when {
                // Etapa rulează numai pentru un PR care are target branch main.
                changeRequest target: 'main'
            }

            steps {
                /*
                 * Construiește o imagine temporară cu aplicația.
                 * Această imagine va fi folosită la linting și teste.
                 */
                sh '''
                    docker build \
                        -t "${CI_IMAGE}" \
                        -f docker/Dockerfile \
                        .
                '''
            }
        }

        stage('PR - Backend Lint') {
            when {
                changeRequest target: 'main'
            }

            steps {
                /*
                 * Rulează Ruff pentru verificarea codului Python.
                 */
                sh '''
                    docker run --rm \
                        "${CI_IMAGE}" \
                        ruff check .
                '''
            }
        }

        stage('PR - Frontend Lint') {
            when {
                changeRequest target: 'main'
            }

            steps {
                /*
                 * Pornește temporar un container Node.js.
                 * Montează proiectul în /workspace,
                 * instalează dependențele și rulează linting-ul frontend.
                 */
                sh '''
                    docker run --rm \
                        -v "$PWD:/workspace" \
                        -w /workspace \
                        node:22-alpine \
                        sh -c "npm ci && npm run lint:frontend"
                '''
            }
        }

        stage('PR - Unit Tests') {
            when {
                changeRequest target: 'main'
            }

            steps {
                /*
                 * Rulează testele unitare Pytest în imaginea CI.
                 */
                sh '''
                    docker run --rm \
                        "${CI_IMAGE}" \
                        python -m pytest -q
                '''
            }
        }

        /*
         * ==========================================================
         * PIPELINE 2
         * Build, Push GHCR și Deployment Staging pentru branch-ul main
         * ==========================================================
         */

        stage('Staging - Build Backend Image') {
            when {
                // Etapa rulează numai pe branch-ul main.
                branch 'main'
            }

            steps {
                /*
                 * Construiește imaginea backend cu un tag unic.
                 */
                sh '''
                    docker build \
                        -f docker/Dockerfile \
                        -t "${BACKEND_IMAGE}" \
                        .
                '''
            }
        }

        stage('Staging - Build Frontend Image') {
            when {
                branch 'main'
            }

            steps {
                /*
                 * Construiește imaginea frontend/Nginx cu un tag unic.
                 */
                sh '''
                    docker build \
                        -f nginx/Dockerfile \
                        -t "${FRONTEND_IMAGE}" \
                        .
                '''
            }
        }

        stage('Staging - Push Images to GHCR') {
            when {
                branch 'main'
            }

            steps {
                /*
                 * Preia credentialele GitHub Packages din Jenkins.
                 *
                 * GH_USER = utilizatorul GitHub
                 * GH_TOKEN = tokenul cu write:packages
                 */
                withCredentials([
                    usernamePassword(
                        credentialsId: 'github-packages',
                        usernameVariable: 'GH_USER',
                        passwordVariable: 'GH_TOKEN'
                    )
                ]) {
                    sh '''
                        set +x

                        # Autentificare securizată la GHCR.
                        echo "$GH_TOKEN" | docker login ghcr.io \
                            -u "$GH_USER" \
                            --password-stdin

                        # Publică imaginea backend.
                        docker push "${BACKEND_IMAGE}"

                        # Publică imaginea frontend.
                        docker push "${FRONTEND_IMAGE}"

                        # Închide sesiunea Docker din GHCR.
                        docker logout ghcr.io
                    '''
                }
            }
        }

        stage('Staging - Deploy') {
            when {
                branch 'main'
            }

            steps {
                /*
                 * Pornește sau actualizează mediul Staging.
                 *
                 * BACKEND_IMAGE și FRONTEND_IMAGE sunt trimise
                 * ca variabile către docker-compose.staging.yml.
                 */
                sh '''
                    BACKEND_IMAGE="${BACKEND_IMAGE}" \
                    FRONTEND_IMAGE="${FRONTEND_IMAGE}" \
                    docker compose \
                        -f docker-compose.staging.yml \
                        up -d \
                        --remove-orphans
                '''
            }
        }

        stage('Staging - API Test') {
            when {
                branch 'production'
            }

            steps {
                /*
                 * Așteaptă maximum 30 de încercări.
                 * La fiecare încercare verifică endpointul /health.
                 */
                sh '''
                    sleep 20
                        for i in $(seq 1 30); do
                            if curl -fsS http://localhost:8081/health; then
                                echo "API-ul Production functioneaza."
                                exit 0
                            fi

                            echo "Astept pornirea API-ului Production: $i/30"
                            sleep 5
                        done

                        echo "API-ul Production nu a pornit."
                        exit 1
                    '''
            }
        }

        stage('Staging - UI Test') {
            when {
                branch 'main'
            }

            steps {
                /*
                 * Verifică dacă interfața Staging răspunde prin HTTP.
                 */
                sh '''
                    curl -fsS http://localhost:8081/ > /dev/null
                '''
            }
        }

        /*
         * ==========================================================
         * PIPELINE 3
         * Blue/Green Deployment pe AWS pentru branch-ul production
         * ==========================================================
         */

        stage('Production - Build Image') {
            when {
                // Pipeline 3 rulează numai pe branch-ul production.
                branch 'production'
            }

            steps {
                /*
                 * Construiește imaginea backend pentru Production.
                 * Exemplu tag: production-7
                 */
                sh '''
                    docker build \
                        -f docker/Dockerfile \
                        -t "${PRODUCTION_IMAGE}" \
                        .
                '''
            }
        }

        stage('Production - Push Image to GHCR') {
            when {
                branch 'production'
            }

            steps {
                /*
                 * Publică imaginea Production în GHCR.
                 */
                withCredentials([
                    usernamePassword(
                        credentialsId: 'github-packages',
                        usernameVariable: 'GH_USER',
                        passwordVariable: 'GH_TOKEN'
                    )
                ]) {
                    sh '''
                        set +x

                        echo "$GH_TOKEN" | docker login ghcr.io \
                            -u "$GH_USER" \
                            --password-stdin

                        docker push "${PRODUCTION_IMAGE}"

                        docker logout ghcr.io
                    '''
                }
            }
        }

         stage('Production - Blue Green Deploy') {
            when {
                branch 'production'
            }

            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'github-packages',
                        usernameVariable: 'GH_USER',
                        passwordVariable: 'GH_TOKEN'
                    ),

                    sshUserPrivateKey(
                        credentialsId: 'aws-ec2-study4u',
                        keyFileVariable: 'EC2_SSH_KEY',
                        usernameVariable: 'EC2_SSH_USER'
                    )
                ]) {
                    sh '''
                        set +x

                        # Tokenul GHCR este transmis prin standard input
                        # către comanda docker login executată pe EC2.
                        #
                        # După autentificare:
                        # - Jenkins intră în directorul Production;
                        # - rulează scriptul Blue/Green;
                        # - pornește mediul inactiv;
                        # - face health check;
                        # - comută traficul Nginx;
                        # - oprește mediul vechi.

                        echo "$GH_TOKEN" | ssh \
                            -i "$EC2_SSH_KEY" \
                            -o BatchMode=yes \
                            -o StrictHostKeyChecking=accept-new \
                            "$EC2_SSH_USER@$EC2_HOST" \
                            "docker login ghcr.io \
                                -u '$GH_USER' \
                                --password-stdin && \
                             cd '$EC2_PRODUCTION_DIR' && \
                             ./scripts/deploy-blue-green.sh '$PRODUCTION_TAG'"
                    '''
                }
            }
        }

        stage('Production - API Test') {
            when {
                branch 'production'
            }

            steps {
                /*
                 * Verifică endpointul public /health după deployment.
                 *
                 * Acesta confirmă că:
                 * - EC2 este accesibil;
                 * - Nginx răspunde;
                 * - traficul merge către noul mediu;
                 * - Flask și PostgreSQL funcționează.
                 */
                sh '''
                    for i in $(seq 1 15); do
                        if curl -fsS "http://${EC2_HOST}/health"; then
                            echo "API-ul Production functioneaza."
                            exit 0
                        fi

                        echo "Astept API-ul Production: $i/15"
                        sleep 4
                    done

                    echo "API-ul Production nu raspunde."
                    exit 1
                '''
            }
        }

        stage('Production - UI Test') {
            when {
                branch 'production'
            }

            steps {
                /*
                 * Verifică dacă interfața publică Study4U este accesibilă.
                 */
                sh '''
                    curl -fsS "http://${EC2_HOST}/" > /dev/null
                '''
            }
        }
    }

    post {
        always {
            script {
                /*
                 * Curățarea imaginilor locale Jenkins.
                 * Evită umplerea discului serverului Jenkins.
                 */

                if (env.CHANGE_ID) {
                    sh '''
                        docker image rm -f "${CI_IMAGE}" || true
                    '''
                }

                if (env.BRANCH_NAME == 'main') {
                    sh '''
                        docker image rm -f "${BACKEND_IMAGE}" || true
                        docker image rm -f "${FRONTEND_IMAGE}" || true
                    '''
                }

                if (env.BRANCH_NAME == 'production') {
                    sh '''
                        docker image rm -f "${PRODUCTION_IMAGE}" || true
                    '''
                }
            }
        }

        success {
            script {
                /*
                 * Mesajele afișate în funcție de pipeline-ul executat.
                 */

                if (env.CHANGE_ID) {
                    echo 'Pipeline 1 CI a trecut cu succes.'
                } else if (env.BRANCH_NAME == 'main') {
                    echo 'Pipeline 2 Staging a trecut cu succes.'
                } else if (env.BRANCH_NAME == 'production') {
                    echo 'Pipeline 3 Blue/Green Production a trecut cu succes.'
                    echo "Imagine deployata: ${PRODUCTION_IMAGE}"
                    echo "Aplicatie: http://${EC2_HOST}"
                }
            }
        }

        failure {
            script {
                /*
                 * Acțiunile executate când un pipeline eșuează.
                 */

                if (env.CHANGE_ID) {
                    echo 'Pipeline 1 CI a esuat.'

                    /*
                     * Publică automat un comentariu în Pull Request.
                     */
                    pullRequest.comment(
                        """❌ **Pipeline 1 CI a eșuat**

Verifică build-ul Jenkins:

${env.BUILD_URL}

Commit verificat: `${env.GIT_COMMIT}`
"""
                    )
                } else if (env.BRANCH_NAME == 'main') {
                    echo 'Pipeline 2 Staging a esuat.'

                    /*
                     * Afișează logurile Staging pentru diagnostic.
                     */
                    sh '''
                        BACKEND_IMAGE="${BACKEND_IMAGE}" \
                        FRONTEND_IMAGE="${FRONTEND_IMAGE}" \
                        docker compose \
                            -f docker-compose.staging.yml \
                            logs || true
                    '''
                } else if (env.BRANCH_NAME == 'production') {
                    echo 'Pipeline 3 Blue/Green Production a esuat.'
                    echo 'Scriptul de deployment trebuie sa pastreze traficul pe mediul anterior.'
                }
            }
        }
    }
}