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
        
        // Terraform
        TF_VAR_admin_username = 'azureuser'
        TF_IN_AUTOMATION = 'true'
    }
    
    stages {
        stage(' Checkout') {
            steps {
                echo ' Récupération du code depuis Git...'
                checkout scm
            }
        }
        
        stage(' Verifier les prerequis') {
            steps {
                echo ' Vérification des outils...'
                script {
                    if (isUnix()) {
                        sh '''
                            docker --version
                            kubectl version --client
                            az --version
                            terraform --version
                            ansible --version
                        '''
                    } else {
                        bat '''
                            docker --version
                            kubectl version --client
                            az --version
                            terraform --version
                            ansible --version
                        '''
                    }
                }
            }
        }
        
        stage(' Infrastructure avec Terraform') {
            steps {
                echo ' Déploiement de l\'infrastructure Azure avec Terraform...'
                script {
                    withCredentials([
                        string(credentialsId: 'azure-sp-app-id', variable: 'ARM_CLIENT_ID'),
                        string(credentialsId: 'azure-sp-password', variable: 'ARM_CLIENT_SECRET'),
                        string(credentialsId: 'azure-sp-tenant', variable: 'ARM_TENANT_ID'),
                        string(credentialsId: 'azure-subscription-id', variable: 'ARM_SUBSCRIPTION_ID')
                    ]) {
                        dir('terraform') {
                            if (isUnix()) {
                                sh '''
                                    # Initialiser Terraform
                                    terraform init
                                    
                                    # Planifier les changements
                                    terraform plan -out=tfplan
                                    
                                    # Appliquer les changements
                                    terraform apply -auto-approve tfplan
                                    
                                    # Sauvegarder les outputs
                                    terraform output -json > ../terraform-outputs.json
                                '''
                            } else {
                                bat '''
                                    echo Initialisation Terraform...
                                    terraform init
                                    
                                    echo Planification...
                                    terraform plan -out=tfplan
                                    
                                    echo Application...
                                    terraform apply -auto-approve tfplan
                                    
                                    echo Sauvegarde des outputs...
                                    terraform output -json > ../terraform-outputs.json
                                '''
                            }
                        }
                    }
                }
            }
        }
        
        stage(' Connexion a AKS') {
            steps {
                echo ' Récupération des credentials AKS...'
                script {
                    withCredentials([
                        string(credentialsId: 'azure-sp-app-id', variable: 'AZURE_APP_ID'),
                        string(credentialsId: 'azure-sp-password', variable: 'AZURE_PASSWORD'),
                        string(credentialsId: 'azure-sp-tenant', variable: 'AZURE_TENANT')
                    ]) {
                        if (isUnix()) {
                            sh '''
                                # Login Azure
                                az login --service-principal -u ${AZURE_APP_ID} -p ${AZURE_PASSWORD} --tenant ${AZURE_TENANT}
                                
                                # Récupérer credentials AKS
                                az aks get-credentials --resource-group ${RESOURCE_GROUP} --name ${AKS_CLUSTER} --overwrite-existing
                                
                                # Vérifier la connexion
                                kubectl get nodes
                            '''
                        } else {
                            bat '''
                                echo Connexion Azure...
                                az login --service-principal -u %AZURE_APP_ID% -p %AZURE_PASSWORD% --tenant %AZURE_TENANT%
                                
                                echo Récupération credentials AKS...
                                az aks get-credentials --resource-group %RESOURCE_GROUP% --name %AKS_CLUSTER% --overwrite-existing
                                
                                echo Vérification connexion...
                                kubectl get nodes
                            '''
                        }
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
                            sh """
                                docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} .
                                docker build -t ${DOCKER_IMAGE}:latest .
                            """
                        } else {
                            bat """
                                docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} .
                                docker build -t ${DOCKER_IMAGE}:latest .
                            """
                        }
                    }
                }
            }
        }
        
        stage(' Tests Docker') {
            steps {
                echo ' Exécution des tests...'
                script {
                    if (isUnix()) {
                        sh """
                            # Démarrer le conteneur de test
                            docker run -d --name test-container-${BUILD_NUMBER} -p 9000:8000 ${DOCKER_IMAGE}:${BUILD_NUMBER}
                            
                            # Attendre le démarrage
                            sleep 15
                            
                            # Tester le endpoint health
                            curl -f http://localhost:9000/health || exit 1
                            
                            # Nettoyer
                            docker stop test-container-${BUILD_NUMBER}
                            docker rm test-container-${BUILD_NUMBER}
                        """
                    } else {
                        bat """
                            echo Démarrage conteneur test...
                            docker run -d --name test-container-${BUILD_NUMBER} -p 9000:8000 ${DOCKER_IMAGE}:${BUILD_NUMBER}
                            
                            echo Attente démarrage...
                            ping 127.0.0.1 -n 16 > nul
                            
                            echo Test health endpoint...
                            curl -f http://localhost:9000/health
                            if errorlevel 1 exit 1
                            
                            echo Nettoyage...
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
                        sh """
                            echo ${DOCKER_HUB_CREDENTIALS_PSW} | docker login -u ${DOCKER_HUB_CREDENTIALS_USR} --password-stdin
                            docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}
                            docker push ${DOCKER_IMAGE}:latest
                            docker logout
                        """
                    } else {
                        bat """
                            docker login -u ${DOCKER_HUB_CREDENTIALS_USR} -p ${DOCKER_HUB_CREDENTIALS_PSW}
                            docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}
                            docker push ${DOCKER_IMAGE}:latest
                            docker logout
                        """
                    }
                }
            }
        }
        
        stage(' Deploiement avec Ansible') {
            steps {
                echo ' Déploiement sur AKS avec Ansible...'
                script {
                    dir('ansible') {
                        if (isUnix()) {
                            sh '''
                                # Exécuter le playbook Ansible
                                ansible-playbook -i inventory/hosts.ini deploy-to-aks.yml -v
                            '''
                        } else {
                            bat '''
                                echo Exécution playbook Ansible...
                                ansible-playbook -i inventory/hosts.ini deploy-to-aks.yml -v
                            '''
                        }
                    }
                }
            }
        }
        
        stage(' Update Deployment Image') {
            steps {
                echo ' Mise à jour de l\'image du déploiement...'
                script {
                    if (isUnix()) {
                        sh """
                            # Mettre à jour l'image du déploiement
                            kubectl set image deployment/${DEPLOYMENT_NAME} \
                                immobilier-container=${DOCKER_IMAGE}:${BUILD_NUMBER} \
                                -n ${K8S_NAMESPACE}
                            
                            # Attendre le rollout
                            kubectl rollout status deployment/${DEPLOYMENT_NAME} -n ${K8S_NAMESPACE} --timeout=5m
                        """
                    } else {
                        bat """
                            echo Mise à jour image déploiement...
                            kubectl set image deployment/${DEPLOYMENT_NAME} immobilier-container=${DOCKER_IMAGE}:${BUILD_NUMBER} -n ${K8S_NAMESPACE}
                            
                            echo Attente rollout...
                            kubectl rollout status deployment/${DEPLOYMENT_NAME} -n ${K8S_NAMESPACE} --timeout=5m
                        """
                    }
                }
            }
        }
        
        stage(' Verification finale') {
            steps {
                echo ' Vérification du déploiement...'
                script {
                    if (isUnix()) {
                        sh """
                            echo "=== PODS ==="
                            kubectl get pods -n ${K8S_NAMESPACE}
                            
                            echo ""
                            echo "=== SERVICES ==="
                            kubectl get svc -n ${K8S_NAMESPACE}
                            
                            echo ""
                            echo "=== URL APPLICATION ==="
                            EXTERNAL_IP=\$(kubectl get svc immobilier-service -n ${K8S_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
                            echo " Application accessible sur: http://\${EXTERNAL_IP}"
                        """
                    } else {
                        bat """
                            echo === PODS ===
                            kubectl get pods -n ${K8S_NAMESPACE}
                            
                            echo.
                            echo === SERVICES ===
                            kubectl get svc -n ${K8S_NAMESPACE}
                        """
                        script {
                            try {
                                def externalIp = bat(
                                    script: "kubectl get svc immobilier-service -n ${K8S_NAMESPACE} -o jsonpath=\"{.status.loadBalancer.ingress[0].ip}\"",
                                    returnStdout: true
                                ).trim()
                                echo " Application accessible sur: http://${externalIp}"
                            } catch (Exception e) {
                                echo " Impossible de récupérer l'IP externe pour le moment"
                            }
                        }
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo ' Pipeline réussi ! Application déployée avec succès.'
            script {
                // Afficher un résumé
                if (isUnix()) {
                    sh '''
                        echo ""
                        echo "╔════════════════════════════════════════╗"
                        echo "║    DÉPLOIEMENT RÉUSSI !         ║"
                        echo "╚════════════════════════════════════════╝"
                        echo ""
                        echo "Résumé:"
                        echo "  - Image Docker: ${DOCKER_IMAGE}:${BUILD_NUMBER}"
                        echo "  - Cluster AKS: ${AKS_CLUSTER}"
                        echo "  - Namespace: ${K8S_NAMESPACE}"
                        echo ""
                    '''
                } else {
                    bat '''
                        echo.
                        echo ========================================
                        echo    DEPLOIEMENT REUSSI !
                        echo ========================================
                        echo.
                        echo Résumé:
                        echo   - Image Docker: %DOCKER_IMAGE%:%BUILD_NUMBER%
                        echo   - Cluster AKS: %AKS_CLUSTER%
                        echo   - Namespace: %K8S_NAMESPACE%
                        echo.
                    '''
                }
            }
        }
        failure {
            echo ' Pipeline échoué. Vérifier les logs ci-dessus.'
            script {
                // Afficher les logs des pods en cas d'échec
                if (isUnix()) {
                    sh '''
                        echo ""
                        echo " Logs des pods (si disponibles):"
                        kubectl logs -l app=immobilier -n ${K8S_NAMESPACE} --tail=50 || echo "Pas de logs disponibles"
                    '''
                } else {
                    bat '''
                        echo.
                        echo Logs des pods (si disponibles):
                        kubectl logs -l app=immobilier -n %K8S_NAMESPACE% --tail=50 || echo Pas de logs disponibles
                    '''
                }
            }
        }
        always {
            echo ' Nettoyage des images Docker locales...'
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
