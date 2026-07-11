resource "azurerm_resource_group" "vajra" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    project     = "vajra"
    environment = "poc"
    managed_by  = "terraform"
  }
}

resource "azurerm_virtual_network" "vajra" {
  name                = "vnet-vajra-poc"
  location            = azurerm_resource_group.vajra.location
  resource_group_name = azurerm_resource_group.vajra.name
  address_space       = ["10.40.0.0/16"]

  tags = azurerm_resource_group.vajra.tags
}

resource "azurerm_subnet" "aks" {
  name                 = "snet-aks"
  resource_group_name  = azurerm_resource_group.vajra.name
  virtual_network_name = azurerm_virtual_network.vajra.name
  address_prefixes     = ["10.40.0.0/22"]
}

resource "azurerm_user_assigned_identity" "aks_control_plane" {
  name                = "id-vajra-aks-control-plane"
  location            = azurerm_resource_group.vajra.location
  resource_group_name = azurerm_resource_group.vajra.name

  tags = azurerm_resource_group.vajra.tags
}

resource "azurerm_role_assignment" "aks_subnet_network_contributor" {
  scope                = azurerm_subnet.aks.id
  role_definition_name = "Network Contributor"
  principal_id         = azurerm_user_assigned_identity.aks_control_plane.principal_id
}

resource "azurerm_kubernetes_cluster" "vajra" {
  name                = var.cluster_name
  location            = azurerm_resource_group.vajra.location
  resource_group_name = azurerm_resource_group.vajra.name
  dns_prefix          = "vajra-poc"

  sku_tier = "Free"

  role_based_access_control_enabled = true

  oidc_issuer_enabled       = true
  workload_identity_enabled = true

  default_node_pool {
    name       = "sysnp"
    vm_size    = var.system_vm_size
    node_count = var.system_node_count

    type           = "VirtualMachineScaleSets"
    vnet_subnet_id = azurerm_subnet.aks.id

    os_sku          = "Ubuntu"
    os_disk_type    = "Managed"
    os_disk_size_gb = var.system_os_disk_size_gb

    max_pods = var.system_max_pods

    only_critical_addons_enabled = false

    upgrade_settings {
      max_surge = "1"
    }
  }

  identity {
    type = "UserAssigned"

    identity_ids = [
      azurerm_user_assigned_identity.aks_control_plane.id
    ]
  }

  network_profile {
    network_plugin      = "azure"
    network_plugin_mode = "overlay"
    network_policy      = "azure"

    load_balancer_sku = "standard"
    outbound_type     = "loadBalancer"

    pod_cidr       = "10.42.0.0/16"
    service_cidr   = "10.41.0.0/16"
    dns_service_ip = "10.41.0.10"
  }

  tags = azurerm_resource_group.vajra.tags

  depends_on = [
    azurerm_role_assignment.aks_subnet_network_contributor
  ]
}

resource "azurerm_kubernetes_cluster_node_pool" "llm" {
  count = var.create_llm_node_pool ? 1 : 0

  name                  = "llmnp"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.vajra.id

  vm_size    = var.llm_vm_size
  node_count = var.llm_node_count

  mode     = "User"
  priority = "Regular"

  os_type = "Linux"
  os_sku  = "Ubuntu"

  vnet_subnet_id = azurerm_subnet.aks.id

  os_disk_type    = "Managed"
  os_disk_size_gb = var.llm_os_disk_size_gb

  max_pods = var.llm_max_pods

  node_labels = {
    workload = "llm"
  }

  node_taints = [
    "workload=llm:NoSchedule"
  ]

  upgrade_settings {
    max_surge = "1"
  }

  tags = azurerm_resource_group.vajra.tags
}
