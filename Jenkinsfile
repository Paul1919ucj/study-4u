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
        }
    }
}