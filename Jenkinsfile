pipeline {
    agent any

    environment {
        CI_IMAGE = "study4u-ci:${BUILD_NUMBER}"
        REGISTRY = "ghcr.io"
        REGISTRY_NAMESPACE = "paul1919ucj"
        BACKEND_IMAGE = "${REGISTRY}/${REGISTRY_NAMESPACE}/study4u-backend:${BUILD_NUMBER}"
        FRONTEND_IMAGE = "${REGISTRY}/${REGISTRY_NAMESPACE}/study4u-frontend:${BUILD_NUMBER}"
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

        stage('Docker Build') {
            when { changeRequest target: 'main' }
            steps {
                sh 'docker build -t ${CI_IMAGE} -f docker/Dockerfile .'
            }
        }

        stage('Backend Lint') {
            when { changeRequest target: 'main' }
            steps {
                sh 'docker run --rm ${CI_IMAGE} ruff check .'
            }
        }

        stage('Frontend Lint') {
            when { changeRequest target: 'main' }
            steps {
                sh '''
                    docker run --rm -v "$PWD:/workspace" -w /workspace node:22-alpine \
                    sh -c "npm ci && npm run lint:frontend"
                '''
            }
        }

        stage('Unit Tests') {
            when { changeRequest target: 'main' }
            steps {
                sh 'docker run --rm ${CI_IMAGE} python -m pytest -q'
            }
        }

        stage('Build Backend Image') {
            when { branch 'main' }
            steps {
                sh 'docker build -f docker/Dockerfile -t ${BACKEND_IMAGE} .'
            }
        }

        stage('Build Frontend Image') {
            when { branch 'main' }
            steps {
                sh 'docker build -f nginx/Dockerfile -t ${FRONTEND_IMAGE} .'
            }
        }

        stage('Push Images') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'github-packages',
                    usernameVariable: 'GH_USER',
                    passwordVariable: 'GH_TOKEN'
                )]) {
                    sh '''
                        echo "$GH_TOKEN" | docker login ghcr.io -u "$GH_USER" --password-stdin
                        docker push ${BACKEND_IMAGE}
                        docker push ${FRONTEND_IMAGE}
                        docker logout ghcr.io
                    '''
                }
            }
        }

        stage('Deploy Staging') {
            when { branch 'main' }
            steps {
                sh 'BACKEND_IMAGE=${BACKEND_IMAGE} FRONTEND_IMAGE=${FRONTEND_IMAGE} docker compose -f docker-compose.staging.yml up -d --remove-orphans'
            }
        }

        stage('API Test') {
            when { branch 'main' }
            steps {
                sh '''
                    for i in $(seq 1 30); do
                        curl -f http://localhost:8081/health && exit 0
                        echo "Astept pornirea aplicatiei: $i/30"
                        sleep 5
                    done
                    exit 1
                '''
            }
        }

        stage('UI Test') {
            when { branch 'main' }
            steps {
                sh 'curl -f http://localhost:8081/'
            }
        }
    }

    post {
        always {
            script {
                if (env.CHANGE_ID) {
                    sh 'docker image rm -f ${CI_IMAGE} || true'
                }
            }
        }

        success {
            script {
                if (env.CHANGE_ID) {
                    echo 'Pipeline 1 CI a trecut cu succes.'
                } else if (env.BRANCH_NAME == 'main') {
                    echo 'Pipeline 2 Staging a trecut cu succes.'
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
                    sh 'BACKEND_IMAGE=${BACKEND_IMAGE} FRONTEND_IMAGE=${FRONTEND_IMAGE} docker compose -f docker-compose.staging.yml logs || true'
                }
            }
        }
    }
}