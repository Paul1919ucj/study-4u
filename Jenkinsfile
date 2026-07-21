pipeline {
    agent any

    options {
        disableConcurrentBuilds()
    }

    environment {
        CI_IMAGE = "study4u-ci:${BUILD_NUMBER}"

        REGISTRY = "ghcr.io"
        REGISTRY_NAMESPACE = "paul1919ucj"

        BACKEND_IMAGE = "${REGISTRY}/${REGISTRY_NAMESPACE}/study4u-backend:${BUILD_NUMBER}"
        FRONTEND_IMAGE = "${REGISTRY}/${REGISTRY_NAMESPACE}/study4u-frontend:${BUILD_NUMBER}"

        PRODUCTION_TAG = "production-${BUILD_NUMBER}"
        PRODUCTION_IMAGE = "${REGISTRY}/${REGISTRY_NAMESPACE}/study4u-backend:production-${BUILD_NUMBER}"

        EC2_HOST = "35.159.70.167"
        EC2_PRODUCTION_DIR = "/home/ubuntu/study4u/production"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Verify Docker') {
            steps {
                sh 'docker --version'
                sh 'docker compose version'
            }
        }

        /*
         * PIPELINE 1
         * Pull Request: development -> main
         */

        stage('Docker Build') {
            when {
                changeRequest target: 'main'
            }

            steps {
                sh 'docker build -t ${CI_IMAGE} -f docker/Dockerfile .'
            }
        }

        stage('Backend Lint') {
            when {
                changeRequest target: 'main'
            }

            steps {
                sh 'docker run --rm ${CI_IMAGE} ruff check .'
            }
        }

        stage('Frontend Lint') {
            when {
                changeRequest target: 'main'
            }

            steps {
                sh '''
                    docker run --rm \
                    -v "$PWD:/workspace" \
                    -w /workspace \
                    node:22-alpine \
                    sh -c "npm ci && npm run lint:frontend"
                '''
            }
        }

        stage('Unit Tests') {
            when {
                changeRequest target: 'main'
            }

            steps {
                sh 'docker run --rm ${CI_IMAGE} python -m pytest -q'
            }
        }

        /*
         * PIPELINE 2
         * Branch: main
         * Build, push GHCR și deploy în Staging
         */

        stage('Build Backend Image') {
            when {
                branch 'main'
            }

            steps {
                sh 'docker build -f docker/Dockerfile -t ${BACKEND_IMAGE} .'
            }
        }

        stage('Build Frontend Image') {
            when {
                branch 'main'
            }

            steps {
                sh 'docker build -f nginx/Dockerfile -t ${FRONTEND_IMAGE} .'
            }
        }

        stage('Push Images') {
            when {
                branch 'main'
            }

            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'github-packages',
                        usernameVariable: 'GH_USER',
                        passwordVariable: 'GH_TOKEN'
                    )
                ]) {
                    sh '''
                        echo "$GH_TOKEN" | docker login ghcr.io \
                            -u "$GH_USER" \
                            --password-stdin

                        docker push ${BACKEND_IMAGE}
                        docker push ${FRONTEND_IMAGE}

                        docker logout ghcr.io
                    '''
                }
            }
        }

        stage('Deploy Staging') {
            when {
                branch 'main'
            }

            steps {
                sh '''
                    BACKEND_IMAGE=${BACKEND_IMAGE} \
                    FRONTEND_IMAGE=${FRONTEND_IMAGE} \
                    docker compose \
                        -f docker-compose.staging.yml \
                        up -d \
                        --remove-orphans
                '''
            }
        }

        stage('API Test') {
            when {
                branch 'main'
            }

            steps {
                sh '''
                    for i in $(seq 1 30); do
                        if curl -f http://localhost:8081/health; then
                            exit 0
                        fi

                        echo "Astept pornirea aplicatiei: $i/30"
                        sleep 5
                    done

                    exit 1
                '''
            }
        }

        stage('UI Test') {
            when {
                branch 'main'
            }

            steps {
                sh 'curl -f http://localhost:8081/'
            }
        }

        /*
         * PIPELINE 3
         * Branch: production
         * Build, push și Blue/Green Deployment pe AWS EC2
         */

        stage('Build Production Image') {
            when {
                branch 'production'
            }

            steps {
                sh '''
                    docker build \
                        -f docker/Dockerfile \
                        -t ${PRODUCTION_IMAGE} \
                        .
                '''
            }
        }

        stage('Push Production Image') {
            when {
                branch 'production'
            }

            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'github-packages',
                        usernameVariable: 'GH_USER',
                        passwordVariable: 'GH_TOKEN'
                    )
                ]) {
                    sh '''
                        echo "$GH_TOKEN" | docker login ghcr.io \
                            -u "$GH_USER" \
                            --password-stdin

                        docker push ${PRODUCTION_IMAGE}

                        docker logout ghcr.io
                    '''
                }
            }
        }

        stage('Deploy Production Blue Green') {
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

        stage('Production API Test') {
            when {
                branch 'production'
            }

            steps {
                sh '''
                    for i in $(seq 1 15); do
                        if curl -fsS "http://${EC2_HOST}/health"; then
                            echo "Production API este functionala."
                            exit 0
                        fi

                        echo "Astept Production API: $i/15"
                        sleep 4
                    done

                    exit 1
                '''
            }
        }

        stage('Production UI Test') {
            when {
                branch 'production'
            }

            steps {
                sh 'curl -fsS "http://${EC2_HOST}/" > /dev/null'
            }
        }
    }

    post {
        always {
            script {
                if (env.CHANGE_ID) {
                    sh 'docker image rm -f ${CI_IMAGE} || true'
                }

                if (env.BRANCH_NAME == 'main') {
                    sh 'docker image rm -f ${BACKEND_IMAGE} || true'
                    sh 'docker image rm -f ${FRONTEND_IMAGE} || true'
                }

                if (env.BRANCH_NAME == 'production') {
                    sh 'docker image rm -f ${PRODUCTION_IMAGE} || true'
                }
            }
        }

        success {
            script {
                if (env.CHANGE_ID) {
                    echo 'Pipeline 1 CI a trecut cu succes.'
                } else if (env.BRANCH_NAME == 'main') {
                    echo 'Pipeline 2 Staging a trecut cu succes.'
                } else if (env.BRANCH_NAME == 'production') {
                    echo 'Pipeline 3 Blue Green Production a trecut cu succes.'
                    echo "Imagine deployata: ${PRODUCTION_IMAGE}"
                    echo "Aplicatie: http://${EC2_HOST}"
                }
            }
        }

        failure {
            script {
                if (env.CHANGE_ID) {
                    echo 'Pipeline 1 CI a esuat.'

                    pullRequest.comment(
                        """❌ **Pipeline 1 CI a eșuat**

Verifică build-ul Jenkins:

${env.BUILD_URL}

Commit verificat: `${env.GIT_COMMIT}`
"""
                    )
                } else if (env.BRANCH_NAME == 'main') {
                    echo 'Pipeline 2 Staging a esuat.'

                    sh '''
                        BACKEND_IMAGE=${BACKEND_IMAGE} \
                        FRONTEND_IMAGE=${FRONTEND_IMAGE} \
                        docker compose \
                            -f docker-compose.staging.yml \
                            logs || true
                    '''
                } else if (env.BRANCH_NAME == 'production') {
                    echo 'Pipeline 3 Blue Green Production a esuat.'
                    echo 'Traficul trebuie sa ramana pe mediul anterior datorita rollback-ului.'
                }
            }
        }
    }
}