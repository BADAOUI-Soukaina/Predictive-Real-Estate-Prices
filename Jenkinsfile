pipeline {
    agent any
    
    environment {
        // Docker Hub credentials (à configurer dans Jenkins)
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
        stage('📥 Checkout') {
            steps {
                echo '📥 Récupération du code depuis Git...'
                checkout scm
            }
        }
        
        stage('🔍 Vérifier les prérequis') {
            steps {
                echo '🔍 Vérification des outils...'
                sh '''
                    docker --version
                    kubectl version --client
                    az --version
                '''
            }
        }
        
        stage('🐳 Build Docker Image') {
            steps {
                echo '🐳 Construction de l\'image Docker...'
                script {
                    dir('app') {
                        // Build avec le numéro de build
                        sh "docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} ."
                        sh "docker build -t ${DOCKER_IMAGE}:latest ."
                    }
                }
            }
        }
        
        stage('🧪 Tests') {
            steps {
                echo '🧪 Exécution des tests...'
                script {
                    // Test basique : vérifier que l'image démarre
                    sh """
                        docker run -d --name test-container-${BUILD_NUMBER} -p 9000:8000 ${DOCKER_IMAGE}:${BUILD_NUMBER}
                        sleep 10
                        curl -f http://localhost:9000/health || exit 1
                        docker stop test-container-${BUILD_NUMBER}
                        docker rm test-container-${BUILD_NUMBER}
                    """
                }
            }
        }
        
        stage('📤 Push to Docker Hub') {
            steps {
                echo '📤 Push vers Docker Hub...'
                script {
                    // Login Docker Hub
                    sh "echo ${DOCKER_HUB_CREDENTIALS_PSW} | docker login -u ${DOCKER_HUB_CREDENTIALS_USR} --password-stdin"
                    
                    // Push les deux tags
                    sh "docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}"
                    sh "docker push ${DOCKER_IMAGE}:latest"
                    
                    // Logout
                    sh "docker logout"
                }
            }
        }
        
        stage('☸️ Deploy to Kubernetes') {
            steps {
                echo '☸️ Déploiement sur Kubernetes AKS...'
                script {
                    // S'assurer que kubectl est configuré pour AKS
                    sh """
                        # Se connecter à AKS (utilise la session az déjà configurée)
                        az aks get-credentials --resource-group ${RESOURCE_GROUP} --name ${AKS_CLUSTER} --overwrite-existing
                        
                        # Vérifier la connexion
                        kubectl get nodes
                        
                        # Mettre à jour le deployment avec la nouvelle image
                        kubectl set image deployment/${DEPLOYMENT_NAME} \
                            immobilier-container=${DOCKER_IMAGE}:${BUILD_NUMBER} \
                            -n ${K8S_NAMESPACE}
                        
                        # Attendre que le rollout soit terminé
                        kubectl rollout status deployment/${DEPLOYMENT_NAME} -n ${K8S_NAMESPACE} --timeout=5m
                    """
                }
            }
        }
        
        stage('✅ Vérification') {
            steps {
                echo '✅ Vérification du déploiement...'
                script {
                    sh """
                        # Afficher les pods
                        kubectl get pods -n ${K8S_NAMESPACE}
                        
                        # Afficher le service
                        kubectl get svc -n ${K8S_NAMESPACE}
                        
                        # Obtenir l'URL de l'application
                        EXTERNAL_IP=\$(kubectl get svc immobilier-service -n ${K8S_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
                        echo "🌐 Application accessible sur: http://\${EXTERNAL_IP}"
                        
                        # Test health check
                        if [ ! -z "\$EXTERNAL_IP" ]; then
                            curl -f http://\${EXTERNAL_IP}/health || echo "⚠️ Health check échoué (peut prendre quelques minutes)"
                        fi
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo '✅ Pipeline réussi ! Application déployée avec succès.'
            script {
                // Récupérer l'URL de l'app
                def externalIp = sh(
                    script: "kubectl get svc immobilier-service -n ${K8S_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' || echo 'pending'",
                    returnStdout: true
                ).trim()
                
                if (externalIp && externalIp != 'pending') {
                    echo """
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    🎉 DÉPLOIEMENT RÉUSSI !
                    
                    📦 Image Docker : ${DOCKER_IMAGE}:${BUILD_NUMBER}
                    🌐 URL Application : http://${externalIp}
                    🔍 Health Check : http://${externalIp}/health
                    
                    📊 Commandes utiles :
                    kubectl get pods -n ${K8S_NAMESPACE}
                    kubectl logs -f -l app=immobilier -n ${K8S_NAMESPACE}
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    """
                }
            }
        }
        failure {
            echo '❌ Pipeline échoué. Vérifier les logs ci-dessus.'
        }
        always {
            echo '🧹 Nettoyage des images Docker locales...'
            sh '''
                docker system prune -f || true
            '''
        }
    }
}