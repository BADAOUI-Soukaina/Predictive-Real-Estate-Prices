# ========================================
# VM Jenkins
# ========================================

# Subnet pour Jenkins
resource "azurerm_subnet" "jenkins_subnet" {
  name                 = "jenkins-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.4.0/24"]
}

# IP Publique pour Jenkins
resource "azurerm_public_ip" "jenkins_pip" {
  name                = "jenkins-public-ip"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "Standard"
  allocation_method   = "Static"
  
  tags = {
    environment = "production"
    role        = "jenkins"
  }
}

# Network Security Group pour Jenkins
resource "azurerm_network_security_group" "jenkins_nsg" {
  name                = "jenkins-nsg"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  # SSH
  security_rule {
    name                       = "allow-ssh"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Jenkins Web UI
  security_rule {
    name                       = "allow-jenkins"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "8080"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

# Network Interface pour Jenkins
resource "azurerm_network_interface" "jenkins_nic" {
  name                = "jenkins-nic"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.jenkins_subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.jenkins_pip.id
  }
}

# Association NSG avec NIC
resource "azurerm_network_interface_security_group_association" "jenkins_nsg_assoc" {
  network_interface_id      = azurerm_network_interface.jenkins_nic.id
  network_security_group_id = azurerm_network_security_group.jenkins_nsg.id
}

# VM Jenkins
resource "azurerm_linux_virtual_machine" "jenkins_vm" {
  name                = "jenkins-vm"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  size                = "Standard_B2s"  # 2 vCPU, 4GB RAM
  admin_username      = var.admin_username

  network_interface_ids = [
    azurerm_network_interface.jenkins_nic.id,
  ]

  admin_ssh_key {
    username   = var.admin_username
    public_key = file(pathexpand(var.ssh_public_key_path))
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 30
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-focal"
    sku       = "20_04-lts"
    version   = "latest"
  }

  tags = {
    environment = "production"
    role        = "jenkins-server"
  }
}

# ========================================
# Outputs Jenkins
# ========================================

output "jenkins_public_ip" {
  value       = azurerm_public_ip.jenkins_pip.ip_address
  description = "Adresse IP publique du serveur Jenkins"
}

output "jenkins_url" {
  value       = "http://${azurerm_public_ip.jenkins_pip.ip_address}:8080"
  description = "URL pour accéder à Jenkins"
}

output "jenkins_ssh_command" {
  value       = "ssh ${var.admin_username}@${azurerm_public_ip.jenkins_pip.ip_address}"
  description = "Commande SSH pour se connecter à Jenkins"
}

output "jenkins_instructions" {
  value = <<-EOT
    
    🤖 VM Jenkins créée avec succès !
    
    📋 Prochaines étapes:
    
    1. Se connecter à la VM:
       ssh ${var.admin_username}@${azurerm_public_ip.jenkins_pip.ip_address}
    
    2. Installer Jenkins avec Ansible:
       cd ansible/
       ansible-playbook -i inventory/hosts.ini setup-jenkins.yml
    
    3. Accéder à Jenkins:
       ${azurerm_public_ip.jenkins_pip.ip_address}:8080
    
    4. Récupérer le mot de passe initial:
       ssh ${var.admin_username}@${azurerm_public_ip.jenkins_pip.ip_address} "sudo cat /var/lib/jenkins/secrets/initialAdminPassword"
  EOT
  description = "Instructions pour configurer Jenkins"
}