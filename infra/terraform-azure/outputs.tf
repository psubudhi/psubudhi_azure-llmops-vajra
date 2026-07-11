output "cluster_name" {
  description = "AKS cluster name."
  value       = azurerm_kubernetes_cluster.vajra.name
}

output "resource_group_name" {
  description = "Vajra POC resource group."
  value       = azurerm_resource_group.vajra.name
}

output "location" {
  description = "Azure deployment location."
  value       = azurerm_resource_group.vajra.location
}

output "system_vm_size" {
  description = "System-pool VM SKU."
  value       = var.system_vm_size
}

output "system_node_count" {
  description = "System-pool node count."
  value       = var.system_node_count
}

output "llm_pool_enabled" {
  description = "Whether the optional LLM pool is enabled."
  value       = var.create_llm_node_pool
}

output "llm_vm_size" {
  description = "LLM-pool VM SKU when enabled."
  value       = var.create_llm_node_pool ? var.llm_vm_size : null
}

output "oidc_issuer_url" {
  description = "AKS OIDC issuer URL."
  value       = azurerm_kubernetes_cluster.vajra.oidc_issuer_url
}

output "node_resource_group" {
  description = "Azure-managed AKS node resource group."
  value       = azurerm_kubernetes_cluster.vajra.node_resource_group
}

output "aks_control_plane_identity_id" {
  description = "User-assigned AKS control-plane identity resource ID."
  value       = azurerm_user_assigned_identity.aks_control_plane.id
}
