# 1. Créer un Groupe de Ressources (le dossier virtuel)
resource "azurerm_resource_group" "rg" {
  name     = "Predictive-Real-Estate-Prices"
  location = "norwayeast" 
}

# 2. Créer le réseau virtuel
resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-mlops"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}
