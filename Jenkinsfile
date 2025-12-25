pipeline {
    agent any

    environment {
        DOCKER_USER = 'sgmarwa'
        IMAGE_NAME = 'immobilier-app'
        AZURE_VM_IP = '20.251.192.87'
        // Identifiants Docker Hub
        DOCKER_HUB_CREDS = credentials('docker-hub-login')
    }

    stages {
        stage('1. Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('2. Terraform - Infra Check') {
            environment {
                ARM_CLIENT_ID       = credentials('AZURE_CLIENT_ID')
                ARM_CLIENT_SECRET   = credentials('AZURE_CLIENT_SECRET')
                ARM_SUBSCRIPTION_ID = credentials('AZURE_SUBSCRIPTION_ID')
                ARM_TENANT_ID       = credentials('AZURE_TENANT_ID')
            }
            steps {
                dir('terraform') {
                    bat 'terraform init'
                    bat 'terraform apply -auto-approve'
                }
            }
        }

        stage('3. Docker - Build & Push') {
            steps {
                script {
                    def imageTag = "${DOCKER_USER}/${IMAGE_NAME}:${env.BUILD_NUMBER}"
                    // Construction via le moteur Docker actif
                    bat "docker build -t ${imageTag} ."
                    bat "echo ${DOCKER_HUB_CREDS_PSW} | docker login -u ${DOCKER_HUB_CREDS_USR} --password-stdin"
                    bat "docker push ${imageTag}"
                    bat "docker tag ${imageTag} ${DOCKER_USER}/${IMAGE_NAME}:latest"
                    bat "docker push ${DOCKER_USER}/${IMAGE_NAME}:latest"
                }
            }
        }

       stage('4. Ansible - Deploy') {
            steps {
                withCredentials([sshUserPrivateKey(credentialsId: 'azure-vm-ssh-key', keyFileVariable: 'SSH_KEY')]) {
                    script {
                        bat """
                        docker run --rm ^
                        --dns 8.8.8.8 ^
                        -v "%WORKSPACE%":/ansible ^
                        -v "%SSH_KEY%":/root/.ssh/id_rsa ^
                        willhallonline/ansible:latest ^
                        ansible-playbook -i /ansible/ansible/inventory.ini /ansible/ansible/deploy.yml ^
                        -u azureuser ^
                        --private-key /root/.ssh/id_rsa ^
                        --extra-vars "ansible_ssh_common_args='-o StrictHostKeyChecking=no'"
                        """
                        
                    }
                }
            }
        }
    }

    post {
        success {
            echo "Félicitations ! L'application est en ligne sur http://${AZURE_VM_IP}:8000"
        }
        failure {
            echo "Le pipeline a échoué. Vérifiez les logs (Console Output)."
        }
    }
}
