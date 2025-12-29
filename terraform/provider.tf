terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"  #Azure Resource Manager
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  # Terraform utilisera automatiquement la session 'az login' active
}