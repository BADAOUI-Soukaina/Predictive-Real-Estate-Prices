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

# 3. Créer un sous-réseau
resource "azurerm_subnet" "subnet" {
  name                 = "internal"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.2.0/24"]
}

# 4. Créer une IP Publique (pour accéder à ton API via Internet)
resource "azurerm_public_ip" "pip" {
  name                = "api-public-ip"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  
  # On passe du Basic au Standard
  sku                 = "Standard" 
  allocation_method   = "Static"
}

# 5. Ouvrir le port 8000 dans le pare-feu (NSG)
resource "azurerm_network_security_group" "nsg" {
  name                = "api-nsg"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  # Règle existante pour l'API
  security_rule {
    name                       = "fastapi"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "8000"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
  name                       = "allow-api"
  priority                   = 120
  direction                  = "Inbound"
  access                     = "Allow"
  protocol                   = "Tcp"
  source_port_range          = "*"
  destination_port_range     = "8000"
  source_address_prefix      = "*"
  destination_address_prefix = "*"
}

  # NOUVELLE Règle pour autoriser SSH (Indispensable pour Ansible)
  security_rule {
    name                       = "allow-ssh"
    priority                   = 110 # Priorité différente de la première
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

# 6. Créer la Carte Réseau
resource "azurerm_network_interface" "nic" {
  name                = "api-nic"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.pip.id
  }
}
resource "azurerm_network_interface_security_group_association" "example" {
  network_interface_id      = azurerm_network_interface.nic.id
  network_security_group_id = azurerm_network_security_group.nsg.id
}
# 7. Créer la Machine Virtuelle
resource "azurerm_linux_virtual_machine" "vm" {
  name                = "vm-predict-api"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  size                = "Standard_D2s_v3" # Taille gratuite
  admin_username      = "azureuser"
  network_interface_ids = [
    azurerm_network_interface.nic.id,
  ]

  admin_ssh_key {
    username   = "azureuser"
    public_key = file("C:/Users/souka/.ssh/id_rsa.pub")
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-focal"
    sku       = "20_04-lts"
    version   = "latest"
  }
}
