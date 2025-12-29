variable "ssh_public_key_path" {
  description = "Chemin vers la clé SSH publique"
  type        = string
  default     = "~/.ssh/id_rsa.pub"  # Chemin par défaut
}

variable "admin_username" {
  description = "Nom d'utilisateur admin pour la VM"
  type        = string
  default     = "azureuser"
}