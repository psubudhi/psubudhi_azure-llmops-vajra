# Next Actions After the First Coding Milestone

Do not start all platform components at once. Complete the following work packages in order so that each new layer has a stable dependency beneath it.

## Work Package 2 — Finish the API separation

### Objective

Remove direct infrastructure/model access from Streamlit and LangGraph.

### Repository changes

```text
services/vajra_api/
  app/
    main.py
    api/v1/
      predictions.py
      topology.py
      alarms.py
      telemetry.py
      investigations.py
      approvals.py
      feedback.py
      logbook.py
    dependencies/
    repositories/
    observability/

services/ui/
  api_client.py
```

### Actions

1. Move the current prediction API under the main `vajra_api` service.
2. Change LangGraph sensor nodes to call an injected `PredictionClient` rather than `src.agentic.ml_service.ml_service`.
3. Change Streamlit logbook, feedback, RCA, and health-check pages to call APIs.
4. Remove all database, model, and RAG imports from Streamlit.
5. Add request IDs and API version fields to all responses.
6. Add OpenAPI contract tests.

### Completion test

The Streamlit container must run without model files, FAISS files, or SQLite data mounted inside it.

---

## Work Package 3 — Replace SQLite and in-memory graph state

### Objective

Make the API safe for multiple replicas and pod restarts.

### Components

- PostgreSQL in local Kind for Phase 1;
- SQLAlchemy and Alembic;
- PostgreSQL LangGraph checkpointer;
- SQLite only for isolated unit tests.

### Tables

```text
agent_runs
agent_run_events
approvals
feedback_events
logbook_events
audit_events
evaluation_runs
kill_switch_events
model_deployments
rag_index_versions
```

### Actions

1. Define SQLAlchemy models.
2. Create Alembic migration `0001_initial_schema`.
3. Replace `runtime_store.py`, `memory.py`, and `audit.py` with repository interfaces.
4. Add transaction boundaries.
5. Add approval pause/resume tests.
6. Add database health/readiness checks.

### Completion test

Start an investigation, stop the API, restart it, and resume the same HITL workflow using its persisted thread ID.

---

## Work Package 4 — Replace FAISS/OpenAI embeddings with Milvus/local embeddings

### Objective

Make RAG persistent, versioned, and independent of hosted embeddings.

### Components

- Milvus standalone Helm release;
- local sentence-transformer embedding service;
- `candidate` and `production` collections/aliases;
- metadata-rich citations.

### Actions

1. Introduce a `VectorStore` interface.
2. Implement `MilvusVectorStore`.
3. Use a local embedding model such as `all-MiniLM-L6-v2` for the POC.
4. Preserve document ID, page, section, version, and chunk ID.
5. Add gold retrieval cases.
6. Remove `allow_dangerous_deserialization` and FAISS runtime loading.

### Completion test

A gold question must return the expected SOP and citation metadata after the Milvus pod is restarted.

---

## Work Package 5 — Airflow RAG ingestion

### Objective

Move document ingestion out of the application process.

### DAG

```text
discover
→ validate
→ parse
→ redact
→ chunk
→ embed
→ index candidate
→ retrieval evaluation
→ promote alias
```

### Actions

1. Add Airflow chart values for local Kind.
2. Package ingestion tasks as testable Python functions.
3. Make ingestion idempotent by document/version hash.
4. Store run results in PostgreSQL.
5. Export ingestion metrics.
6. Add index rollback to the previous alias.

### Completion test

A changed SOP creates a candidate collection, passes evaluation, and then atomically becomes the production alias.

---

## Work Package 6 — CPU vLLM proof

### Objective

Replace the hosted LLM dependency with a local OpenAI-compatible endpoint.

### Before installation

Record:

```bash
uname -m
lscpu | egrep 'Model name|Socket|Core|Thread|avx|avx2|avx512'
free -h
```

CPU support and installation differ by processor family. Follow the current official vLLM CPU instructions for the actual host rather than copying a GPU installation command.

### Recommended POC model

Use a small instruct model that can fit in host RAM. Start with a 1B–3B model and a 2,048-token context. Llama-family access may require licence acceptance and a Hugging Face token.

### Repository additions

```text
infra/images/vllm-cpu/
  Dockerfile
  entrypoint.sh
  README.md

platform/kserve/vllm/
  serving-runtime.yaml
  inference-service.yaml
  llm-inference-service.yaml
  values-local.yaml
  values-aks.yaml
```

### Initial resource profile

```text
CPU request: 4
CPU limit: 8
Memory request: 10 GiB
Memory limit: 16 GiB
max model length: 2048
max concurrent sequences: 2
```

### Application changes

Configure LangChain through an OpenAI-compatible base URL:

```text
VLLM_BASE_URL=http://vllm.inference.svc.cluster.local:8000/v1
VLLM_MODEL=<approved-model-id>
```

Add:

- request timeout;
- retry budget;
- max token guardrail;
- model version in traces;
- fallback response;
- token and latency metrics.

### Completion test

The same RAG gold queries must run against vLLM and return valid structured answers with citations.

---

## Work Package 7 — Local Kubernetes platform

### Objective

Deploy the complete POC locally before paying for AKS.

### Installation order

```text
1. Kind and Local Path Provisioner
2. cert-manager
3. Envoy Gateway
4. KServe
5. PostgreSQL
6. Triton and vLLM runtimes
7. Milvus
8. Airflow
9. ArgoCD
10. Prometheus/Grafana/OpenTelemetry
11. KEDA
12. OPA/Gatekeeper
13. Backstage
14. Vajra application services
```

### Repository additions

```text
platform/helm/
platform/argocd/
platform/kserve/
platform/envoy/
platform/monitoring/
platform/keda/
platform/opa/
platform/backstage/
```

Use common and environment-specific values:

```text
values-common.yaml
values-local.yaml
values-aks.yaml
```

### Completion test

Delete an API pod, confirm Kubernetes replaces it, and confirm ArgoCD reverts a manual deployment edit.

---

## Work Package 8 — Observability, evaluation, and rollback

### Objective

Make operational health and AI quality separately measurable.

### Instrumentation

Every request should carry:

```text
request_id
run_id
thread_id
asset_id
model_version
prompt_version
index_version
environment
cluster
```

### Metrics

```text
prediction latency and error rate
RAG retrieval score and citation coverage
LLM token count and time to first token
agent steps and tool calls
HITL request/decision count
guardrail blocks
canary quality score
```

### Canary process

```text
stable 90%
candidate 10%
→ evaluation
→ promote or GitOps rollback
```

### Completion test

Deploy a deliberately degraded candidate and show an evaluator-triggered Git commit that restores stable traffic through ArgoCD.

---

## Work Package 9 — Backstage templates

### Objective

Create three developer golden paths.

### Templates

1. Predictive/LLM model endpoint.
2. Milvus vector database/collection.
3. RAG and LangGraph agent service.

Each template generates:

```text
source skeleton
Dockerfile
tests
Helm chart
ArgoCD Application
GitHub Actions workflow
Prometheus resources
OPA-required labels
values-local.yaml
values-aks.yaml
```

### Completion test

Generate one service from each template and deploy it to the local Kind cluster.

---

# Azure Account Setup

Azure setup begins in read-only/plan mode. Do not create AKS resources until the local platform is accepted and the client approves a budget.

## 1. Required client information

Obtain:

```text
Azure tenant ID
Azure subscription ID
approved region
approved maximum spend
resource naming prefix
required tags
whether a service principal already exists
whether GitHub Actions OIDC is permitted
```

## 2. Local Azure login

For interactive local administration:

```bash
az login --tenant <TENANT_ID>
az account set --subscription <SUBSCRIPTION_ID>
az account show --output table
```

For automation, prefer workload identity federation/OIDC rather than a long-lived client secret.

## 3. Validate permissions

```bash
az role assignment list \
  --assignee <CURRENT_PRINCIPAL_OBJECT_ID> \
  --all \
  --output table
```

For Terraform planning, the principal needs permission to read the subscription and intended resource group. Resource creation requires only the roles approved for the project; avoid permanent Owner access.

## 4. Check/register providers

Inspect:

```bash
az provider show --namespace Microsoft.ContainerService --query registrationState -o tsv
az provider show --namespace Microsoft.Compute --query registrationState -o tsv
az provider show --namespace Microsoft.Network --query registrationState -o tsv
az provider show --namespace Microsoft.Storage --query registrationState -o tsv
az provider show --namespace Microsoft.KeyVault --query registrationState -o tsv
az provider show --namespace Microsoft.ContainerRegistry --query registrationState -o tsv
az provider show --namespace Microsoft.OperationalInsights --query registrationState -o tsv
az provider show --namespace Microsoft.Insights --query registrationState -o tsv
```

Register only when approved:

```bash
az provider register --namespace Microsoft.ContainerService
az provider register --namespace Microsoft.Compute
az provider register --namespace Microsoft.Network
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.KeyVault
az provider register --namespace Microsoft.ContainerRegistry
az provider register --namespace Microsoft.OperationalInsights
az provider register --namespace Microsoft.Insights
```

## 5. Check regional compute availability and quota

```bash
az vm list-skus \
  --location <REGION> \
  --resource-type virtualMachines \
  --all \
  --output table

az vm list-usage --location <REGION> --output table
```

For the CPU POC, identify a general-purpose VM size with enough RAM. Do not request a GPU quota during zero-cost development.

## 6. Prepare Terraform authentication

For local planning, Azure CLI authentication is sufficient:

```bash
export ARM_SUBSCRIPTION_ID=<SUBSCRIPTION_ID>
export ARM_TENANT_ID=<TENANT_ID>
```

For GitHub Actions, create federated/OIDC authentication in the later CI work package. Do not store an Azure client secret in the repository.

## 7. Build the Azure Terraform modules

```text
infra/terraform-azure/
  modules/
    resource-group/
    network/
    aks/
    node-pool/
    identity/
    optional-acr/
    optional-key-vault/
    optional-monitoring/
  environments/
    poc/
```

Defaults:

```text
AKS Free management tier
one CPU system node pool
OIDC issuer enabled
Workload Identity enabled
no GPU pool
no NAT Gateway
no Azure Firewall
no managed Grafana
no managed PostgreSQL
no public application gateway
```

Run only:

```bash
terraform init
terraform fmt -check
terraform validate
terraform plan
```

Do not run `terraform apply` until the client approves the plan and estimated cost.

## 8. AKS identity design

When AKS is eventually created:

- enable OIDC issuer;
- enable Microsoft Entra Workload Identity;
- use Kubernetes service accounts mapped to managed identities;
- use Key Vault/Secrets Store CSI for Azure secrets;
- avoid embedding Azure credentials in pods.

## 9. First temporary AKS validation

Only after all local acceptance tests pass:

1. create the resource group;
2. provision a small AKS CPU cluster;
3. deploy only ArgoCD and core Vajra services;
4. use self-hosted Prometheus/Grafana;
5. validate Workload Identity;
6. run prediction, RAG, and agent smoke tests;
7. record performance and cost;
8. destroy the environment.

---

# Recommended execution order summary

```text
Milestone 1: prediction parity and API boundary
→ API/agent/database separation
→ Milvus and Airflow RAG
→ CPU vLLM
→ local Kind/KServe platform
→ observability, canary, KEDA, OPA
→ Backstage templates
→ Azure Terraform plan
→ short-lived AKS validation
```
