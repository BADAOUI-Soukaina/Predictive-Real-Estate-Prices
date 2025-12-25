pipeline {
    agent any
    
    environment {
        // Docker Hub
        DOCKER_HUB_CREDENTIALS = credentials('dockerhub-credentials')
        DOCKER_IMAGE = 'sgmarwa/immobilier_price_prediction-app'
        
        // Kubernetes
        K8S_NAMESPACE = 'immobilier-app'
        DEPLOYMENT_NAME = 'immobilier-deployment'
        
        // Azure
        RESOURCE_GROUP = 'Predictive-Real-Estate-Prices'
        AKS_CLUSTER = 'immobilier-aks-cluster'
    }
    
    stages {
        stage(' Checkout') {
            steps {
                echo ' Recuperation du code depuis Git...'
                checkout scm
            }
        }
        
        stage(' Verifier les prerequis') {
            steps {
                echo ' Verification des outils...'
                script {
                    // Sur Windows, utiliser bat au lieu de sh
                    if (isUnix()) {
                        sh 'docker --version'
                        sh 'kubectl version --client'
                        sh 'az --version'
                    } else {
                        bat 'docker --version'
                        bat 'kubectl version --client'
                        bat 'az --version'
                    }
                }
            }
        }
        
        stage(' Build Docker Image') {
            steps {
                echo ' Construction de l\'image Docker...'
                script {
                    dir('app') {
                        if (isUnix()) {
                            sh "docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} ."
                            sh "docker build -t ${DOCKER_IMAGE}:latest ."
                        } else {
                            bat "docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} ."
                            bat "docker build -t ${DOCKER_IMAGE}:latest ."
                        }
                    }
                }
            }
        }
        
        stage(' Tests') {
            steps {
                echo ' Execution des tests...'
                script {
                    if (isUnix()) {
                        sh """
                            docker run -d --name test-container-${BUILD_NUMBER} -p 9000:8000 ${DOCKER_IMAGE}:${BUILD_NUMBER}
                            sleep 10
                            curl -f http://localhost:9000/health || exit 1
                            docker stop test-container-${BUILD_NUMBER}
                            docker rm test-container-${BUILD_NUMBER}
                        """
                    } else {
                        bat """
                            docker run -d --name test-container-${BUILD_NUMBER} -p 9000:8000 ${DOCKER_IMAGE}:${BUILD_NUMBER}
                            timeout /t 10
                            curl -f http://localhost:9000/health
                            docker stop test-container-${BUILD_NUMBER}
                            docker rm test-container-${BUILD_NUMBER}
                        """
                    }
                }
            }
        }
        
        stage(' Push to Docker Hub') {
            steps {
                echo ' Push vers Docker Hub...'
                script {
                    if (isUnix()) {
                        sh "echo ${DOCKER_HUB_CREDENTIALS_PSW} | docker login -u ${DOCKER_HUB_CREDENTIALS_USR} --password-stdin"
                        sh "docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}"
                        sh "docker push ${DOCKER_IMAGE}:latest"
                        sh "docker logout"
                    } else {
                        bat "docker login -u ${DOCKER_HUB_CREDENTIALS_USR} -p ${DOCKER_HUB_CREDENTIALS_PSW}"
                        bat "docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}"
                        bat "docker push ${DOCKER_IMAGE}:latest"
                        bat "docker logout"
                    }
                }
            }
        }
        
        stage(' Deploy to Kubernetes') {
            steps {
                echo ' Déploiement sur Kubernetes AKS...'
                script {
                    withCredentials([
                        string(credentialsId: 'azure-sp-app-id', variable: 'AZURE_APP_ID'),
                        string(credentialsId: 'azure-sp-password', variable: 'AZURE_PASSWORD'),
                        string(credentialsId: 'azure-sp-tenant', variable: 'AZURE_TENANT')
                    ]) {
                        bat """
                            echo Connexion Azure...
                            az login --service-principal ^
                            -u %AZURE_APP_ID% ^
                            -p %AZURE_PASSWORD% ^
                            --tenant %AZURE_TENANT%

                            echo Récupération des credentials AKS...
                            az aks get-credentials ^
                            --resource-group ${RESOURCE_GROUP} ^
                            --name ${AKS_CLUSTER} ^
                            --overwrite-existing

                            echo Vérification connexion AKS...
                            kubectl get nodes

                            echo Déploiement application...
                            kubectl apply -f k8s/
                            kubectl set image deployment/${DEPLOYMENT_NAME} immobilier-container=${DOCKER_IMAGE}:${BUILD_NUMBER} -n ${K8S_NAMESPACE}
                            kubectl rollout status deployment/${DEPLOYMENT_NAME} -n ${K8S_NAMESPACE} --timeout=5m
                        """
                    }
                }
            }
        }

        
        stage(' Verification') {
            steps {
                echo ' Verification du déploiement...'
                script {
                    if (isUnix()) {
                        sh """
                            kubectl get pods -n ${K8S_NAMESPACE}
                            kubectl get svc -n ${K8S_NAMESPACE}
                            EXTERNAL_IP=\$(kubectl get svc immobilier-service -n ${K8S_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
                            echo " Application accessible sur: http://\${EXTERNAL_IP}"
                        """
                    } else {
                        bat """
                            kubectl get pods -n ${K8S_NAMESPACE}
                            kubectl get svc -n ${K8S_NAMESPACE}
                        """
                        script {
                            def externalIp = bat(
                                script: "kubectl get svc immobilier-service -n ${K8S_NAMESPACE} -o jsonpath=\"{.status.loadBalancer.ingress[0].ip}\"",
                                returnStdout: true
                            ).trim()
                            echo " Application accessible sur: http://${externalIp}"
                        }
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo ' Pipeline reussi ! Application déployée avec succès.'
        }
        failure {
            echo ' Pipeline echoue. Vérifier les logs ci-dessus.'
        }
        always {
            echo '🧹 Nettoyage des images Docker locales...'
            script {
                if (isUnix()) {
                    sh 'docker system prune -f || true'
                } else {
                    bat 'docker system prune -f || exit 0'
                }
            }
        }
    }
}
