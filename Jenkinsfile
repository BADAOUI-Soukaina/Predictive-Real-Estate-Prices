pipeline {
    agent any

    environment {
        // Variables à adapter
        DOCKER_USER = 'sgmarwa'
        IMAGE_NAME = 'immobilier-app'
        AZURE_VM_IP = '20.251.192.87'
        // IDs des credentials enregistrés dans Jenkins
        DOCKER_HUB_CREDS = credentials('docker-hub-login')
        SSH_KEY_ID = credentials('azure-vm-ssh-key')
    }

    stages {
        stage('1. Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('2. Terraform - Infra Check') {
            steps {
                dir('terraform') {
                    sh 'terraform init'
                    sh 'terraform apply -auto-approve'
                }
            }
        }

        stage('3. Docker - Build & Push') {
            steps {
                script {
                    def imageTag = "${DOCKER_USER}/${IMAGE_NAME}:${env.BUILD_NUMBER}"
                    sh "docker build -t ${imageTag} ."
                    sh "echo ${DOCKER_HUB_CREDS_PSW} | docker login -u ${DOCKER_HUB_CREDS_USR} --password-stdin"
                    sh "docker push ${imageTag}"
                    sh "docker tag ${imageTag} ${DOCKER_USER}/${IMAGE_NAME}:latest"
                    sh "docker push ${DOCKER_USER}/${IMAGE_NAME}:latest"
                }
            }
        }

        stage('4. Ansible - Deploy') {
            steps {
                dir('ansible') {
                    sh "ansible-playbook -i inventory.ini deploy.yml --extra-vars 'docker_image_tag=${env.BUILD_NUMBER}'"
                }
            }
        }
    }

    post {
        success {
            echo "Félicitations ! L'application est en ligne sur http://${AZURE_VM_IP}:8000"
        }
        failure {
            echo "Le pipeline a échoué. Vérifiez les logs de l'étape correspondante."
        }
    }
}
