#!/usr/bin/env bash
set -euo pipefail

: "${AZURE_SUBSCRIPTION_ID:?AZURE_SUBSCRIPTION_ID is required}"
: "${AZURE_LOCATION:?AZURE_LOCATION is required}"
: "${SYSTEM_VM_SIZE:?SYSTEM_VM_SIZE is required}"

CREATE_LLM_POOL="${CREATE_LLM_POOL:-false}"

echo "=================================================="
echo "VAJRA AKS PREFLIGHT"
echo "=================================================="
echo "Subscription: ${AZURE_SUBSCRIPTION_ID}"
echo "Location:     ${AZURE_LOCATION}"
echo "System SKU:   ${SYSTEM_VM_SIZE}"
echo "LLM pool:     ${CREATE_LLM_POOL}"

az account set \
  --subscription "${AZURE_SUBSCRIPTION_ID}"

ACCOUNT_STATE="$(
  az account show \
    --query state \
    --output tsv
)"

if [[ "${ACCOUNT_STATE}" != "Enabled" ]]; then
  echo "ERROR: Azure subscription is not enabled."
  exit 1
fi

check_provider() {
  local provider="$1"

  local state
  state="$(
    az provider show \
      --namespace "${provider}" \
      --query registrationState \
      --output tsv
  )"

  if [[ "${state}" != "Registered" ]]; then
    echo "ERROR: Provider is not registered: ${provider}"
    exit 1
  fi

  echo "Provider registered: ${provider}"
}

check_sku() {
  local sku="$1"

  echo
  echo "Checking SKU: ${sku}"

  local record
  record="$(
    timeout 60s az vm list-skus \
      --location "${AZURE_LOCATION}" \
      --resource-type virtualMachines \
      --size "${sku}" \
      --query "[?name=='${sku}'] | [0]" \
      --output json \
      --only-show-errors
  )"

  if [[ -z "${record}" || "${record}" == "null" ]]; then
    echo "ERROR: SKU not found in ${AZURE_LOCATION}: ${sku}"
    exit 1
  fi

  local restriction_count
  restriction_count="$(
    jq '(.restrictions // []) | length' <<<"${record}"
  )"

  if [[ "${restriction_count}" != "0" ]]; then
    echo "ERROR: SKU is restricted: ${sku}"
    jq '.restrictions' <<<"${record}"
    exit 1
  fi

  local family
  family="$(jq -r '.family' <<<"${record}")"

  echo "SKU access passed: ${sku}"
  echo "SKU family: ${family}"
}

check_provider "Microsoft.ContainerService"
check_provider "Microsoft.Compute"
check_provider "Microsoft.Network"
check_provider "Microsoft.Storage"
check_provider "Microsoft.ManagedIdentity"

check_sku "${SYSTEM_VM_SIZE}"

if [[ "${CREATE_LLM_POOL}" == "true" ]]; then
  : "${LLM_VM_SIZE:?LLM_VM_SIZE is required when CREATE_LLM_POOL=true}"
  check_sku "${LLM_VM_SIZE}"
fi

echo
echo "Regional quota:"
az vm list-usage \
  --location "${AZURE_LOCATION}" \
  --query "[
    ?name.localizedValue=='Total Regional vCPUs'
  ].{
    Name:name.localizedValue,
    Used:currentValue,
    Limit:limit
  }" \
  --output table

echo
echo "Relevant VM-family quotas:"
az vm list-usage \
  --location "${AZURE_LOCATION}" \
  --output table \
  | grep -Ei \
    'Total Regional|DSv4|DSv5|DSv6|DSv7|ESv4|ESv5|ESv6|ESv7' \
  || true

echo
echo "Preflight checks passed."
