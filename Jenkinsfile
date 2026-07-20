pipeline {
    agent any

    environment {
        CI_IMAGE = "study4u-ci:${BUILD_NUMBER}"
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
            steps {
                sh 'docker build -t ${CI_IMAGE} -f docker/Dockerfile .'
            }
        }

        stage('Backend Lint') {
            steps {
                sh 'docker run --rm ${CI_IMAGE} ruff check .'
            }
        }

        stage('Frontend Lint') {
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
            steps {
                sh 'docker run --rm ${CI_IMAGE} python -m pytest -q'
            }
        }
    }

    post {
        always {
            sh 'docker image rm -f ${CI_IMAGE} || true'
        }

        success {
            echo 'Pipeline 1 CI a trecut cu succes.'
        }

        failure {
            echo 'Pipeline 1 CI a esuat. Verifica etapa marcata cu rosu.'

            script {
                if (env.CHANGE_ID) {
                    pullRequest.comment(
                        """❌ **Pipeline 1 CI a eșuat**

    Verifică build-ul Jenkins pentru etapa care a eșuat:

    ${env.BUILD_URL}

    Commit verificat: `${env.GIT_COMMIT}`
    """
                    )
                } else {
                    echo 'Build-ul nu apartine unui Pull Request; comentariul nu este trimis.'
                }
            }
        }
    }
}