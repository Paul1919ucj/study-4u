pipeline {

    agent any
    stages {
        stage('Checkout') {
            steps {
                echo 'Codul a fost preluat din GitHub'
            }
        }
        stage('Docker Build') {
            steps {
                sh 'docker --version'
                sh 'docker compose version'
            }
        }
        stage('Build') {
            steps {
                sh 'docker compose build'
            }
        }
    }
}