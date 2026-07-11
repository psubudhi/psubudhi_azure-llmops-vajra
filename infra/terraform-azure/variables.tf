variable "subscription_id" {
  description = "Azure subscription used for the Vajra POC."
  type        = string
  sensitive   = true
}

variable "resource_group_name" {
  description = "Dedicated resource group for the Vajra POC."
  type        = string
  default     = "rg-vajra-poc"
}

variable "location" {
  description = "Azure region selected after SKU and quota validation."
  type        = string
  default     = "centralindia"
}

variable "cluster_name" {
  description = "AKS cluster name."
  type        = string
  default     = "aks-vajra-poc"
}

variable "system_vm_size" {
  description = "Approved unrestricted four-vCPU system-pool SKU."
  type        = string

  validation {
    condition     = length(trimspace(var.system_vm_size)) > 0
    error_message = "system_vm_size must be a verified unrestricted Azure SKU."
  }
}

variable "system_node_count" {
  description = "Number of base system-pool nodes."
  type        = number
  default     = 2

  validation {
    condition     = var.system_node_count >= 2
    error_message = "The Vajra full-demo system pool must use at least two nodes."
  }
}

variable "system_os_disk_size_gb" {
  description = "System-node managed OS disk size."
  type        = number
  default     = 128

  validation {
    condition     = var.system_os_disk_size_gb >= 128
    error_message = "Use at least 128 GB because the Triton image is approximately 18 GB before extraction."
  }
}

variable "system_max_pods" {
  description = "Maximum pods per system node."
  type        = number
  default     = 40
}

variable "create_llm_node_pool" {
  description = "Whether to create the CPU-vLLM user pool."
  type        = bool
  default     = false
}

variable "llm_vm_size" {
  description = "Approved memory-optimized CPU-vLLM SKU."
  type        = string
  default     = ""

  validation {
    condition = (
      !var.create_llm_node_pool ||
      length(trimspace(var.llm_vm_size)) > 0
    )

    error_message = "llm_vm_size is required when create_llm_node_pool is true."
  }
}

variable "llm_node_count" {
  description = "Number of CPU-vLLM nodes."
  type        = number
  default     = 1

  validation {
    condition     = var.llm_node_count >= 1
    error_message = "Use at least one node when the LLM node pool is enabled."
  }
}

variable "llm_os_disk_size_gb" {
  description = "LLM-node managed OS disk size."
  type        = number
  default     = 128
}

variable "llm_max_pods" {
  description = "Maximum pods on the LLM node."
  type        = number
  default     = 30
}
