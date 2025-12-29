# ========================================
# Azure Kubernetes Service (AKS)
# ========================================

# Subnet dédié pour AKS
resource "azurerm_subnet" "aks_subnet" {
  name                 = "aks-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.3.0/24"]
}

# Cluster AKS
resource "azurerm_kubernetes_cluster" "aks" {
  name                = "immobilier-aks-cluster"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "immobilier-k8s"

  default_node_pool {
    name                = "default"
    node_count          = 2  # Nombre de nodes (VMs dans le cluster)
    vm_size = "Standard_B2as_v2" 
    vnet_subnet_id      = azurerm_subnet.aks_subnet.id
    enable_auto_scaling = true
    min_count           = 2
    max_count           = 5
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure"
    load_balancer_sku = "standard"
    service_cidr      = "10.1.0.0/16"
    dns_service_ip    = "10.1.0.10"
  }

  tags = {
    environment = "production"
    project     = "immobilier-ml"
    managed_by  = "terraform"
  }
}

# Output pour récupérer la kubeconfig
output "aks_cluster_name" {
  value       = azurerm_kubernetes_cluster.aks.name
  description = "Nom du cluster AKS"
}

output "aks_kubeconfig" {
  value       = azurerm_kubernetes_cluster.aks.kube_config_raw
  description = "Kubeconfig pour se connecter au cluster"
  sensitive   = true
}

output "aks_host" {
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].host
  description = "Host du cluster AKS"
  sensitive   = true
}

output "instructions_aks" {
  value = <<-EOT
    
    🎉 Cluster AKS créé avec succès !
    
    📋 Prochaines étapes:
    
    1. Récupérer la kubeconfig:
       az aks get-credentials --resource-group ${azurerm_resource_group.rg.name} --name ${azurerm_kubernetes_cluster.aks.name}
    
    2. Vérifier la connexion:
       kubectl get nodes
    
    3. Déployer l'application:
       kubectl apply -f k8s/
    
    4. Accéder à l'app:
       kubectl get svc -n immobilier-app
  EOT
  description = "Instructions pour utiliser AKS"
}