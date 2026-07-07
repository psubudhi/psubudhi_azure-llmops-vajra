# Vajra V2 → Azure-Ready Kubernetes MLOps/LLMOps Refactor Blueprint

## 1. Executive decision

Do **not** rewrite Vajra V2 from scratch. Preserve the existing predictive-maintenance rules, cascading analysis, prompts, decision trace, demo scenarios, evaluation questions, and Streamlit presentation. Refactor the runtime into a small number of clearly separated services:

```text
Streamlit UI
    |
    v
FastAPI Vajra API (domain logic + LangGraph orchestration)
    |----------------------|----------------------|
    v                      v                      v
KServe/Triton CPU      KServe/vLLM CPU        Milvus
predictive inference   OpenAI-compatible LLM   vector retrieval
    |                      |                      |
    +----------------------+----------------------+
                           |
                           v
                    PostgreSQL state
              logbook + feedback + approvals
              LangGraph checkpoints + audit

Airflow: documents -> parse -> chunk -> embed -> Milvus -> evaluate
MCP server: approved tools for telemetry, inference, RAG, health, work orders
Envoy AI Gateway: single entry point, auth hooks, rate/token limits, routing
Prometheus/Grafana/OpenTelemetry/LangSmith: metrics, traces, SLOs, evaluations
ArgoCD/Helm: deployment, reconciliation and rollback
Kind locally; AKS manifests and Terraform prepared for optional Azure validation
```

The cost-effective Phase 1 should run on a local Kind cluster. Azure is used first for credential validation and `terraform plan`; actual AKS provisioning is optional and short-lived.

---

## 2. Findings from the supplied repository

### 2.1 Current strengths

The repository already contains useful production-oriented domain logic:

- Predictive-maintenance inference wrapper and risk calculation.
- Anomaly/fault/RUL outputs and evidence extraction.
- Physical engineering rules and cascading impact analysis.
- LangGraph RCA/planning/report workflow.
- Decision trace and persistent audit records.
- Engineer feedback workflow.
- Gold evaluation prompts.
- Demo scenario simulator.
- SOP/manual corpus.
- Streamlit operational UI.

### 2.2 Current limitations that must be fixed

1. `app.py` directly calls Python singletons such as `ml_service`, `rag`, `runtime_store`, and `answer_maintenance_query`.
2. Inference directly loads local joblib models and a local parquet dataset.
3. The supplied ZIP does not include the required model files or processed parquet file.
4. `llm.py` is tied to OpenAI rather than an OpenAI-compatible vLLM endpoint.
5. `rag.py` uses local FAISS and OpenAI embeddings.
6. FAISS loading uses dangerous pickle deserialization and is unsuitable as the target platform store.
7. SQLite is local to one process/pod and is unsuitable for multiple API replicas.
8. LangGraph uses `MemorySaver`, so HITL/checkpoints disappear when a pod restarts.
9. The current graph proposes actions but does not implement a true pause/approval/resume action workflow.
10. No FastAPI/OpenAPI contract exists.
11. No Dockerfiles, Helm charts, Kubernetes resources, Terraform, ArgoCD, KEDA, OPA, Backstage, or Airflow deployment assets exist.
12. No request IDs, Prometheus metrics, OpenTelemetry propagation, API authentication, PII filtering, or structured policy layer exists.
13. `.env` is included in the archive. Remove it from source control and rotate any credential that may have been shared or committed.

---

## 3. Required missing Vajra assets

The following files are required before the existing inference path can run:

```text
tcm_modelling/models/model_metadata.json
tcm_modelling/models/anomaly_classifier.joblib
tcm_modelling/models/fault_multilabel_classifier.joblib
tcm_modelling/models/rul_urgency_classifier.joblib
tcm_modelling/models/proxy_rul_regressor.joblib

tcm_modelling/data/processed/tcm_features_dataset3.parquet
```

Optional but useful:

```text
tcm_modelling/models/case_memory_preprocessor.joblib
tcm_modelling/models/case_memory_nearest_neighbors.joblib
```

The CSV/JSON output artifacts are present in the supplied archive, but the trained model and feature parquet artifacts are not.

Before refactoring inference, obtain and freeze:

- model files;
- exact `model_metadata.json`;
- feature-generation notebook/code;
- Python package versions used for training;
- one normal, one warning, and one critical golden input row;
- expected prediction JSON for each golden row.

---

## 4. Target repository structure

```text
vajra-azure-llmops/
├── services/
│   ├── api/
│   │   ├── src/vajra_api/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── middleware/
│   │   │   │   ├── request_context.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── metrics.py
│   │   │   │   └── tracing.py
│   │   │   ├── routers/
│   │   │   │   ├── health.py
│   │   │   │   ├── telemetry.py
│   │   │   │   ├── predictions.py
│   │   │   │   ├── alarms.py
│   │   │   │   ├── rag.py
│   │   │   │   ├── agents.py
│   │   │   │   ├── approvals.py
│   │   │   │   ├── feedback.py
│   │   │   │   ├── logbook.py
│   │   │   │   ├── evaluations.py
│   │   │   │   └── controls.py
│   │   │   ├── schemas/
│   │   │   ├── clients/
│   │   │   │   ├── triton.py
│   │   │   │   ├── vllm.py
│   │   │   │   ├── milvus.py
│   │   │   │   └── mcp.py
│   │   │   ├── repositories/
│   │   │   │   ├── base.py
│   │   │   │   ├── postgres.py
│   │   │   │   └── sqlite_dev.py
│   │   │   ├── agents/
│   │   │   │   ├── graph.py
│   │   │   │   ├── state.py
│   │   │   │   ├── nodes.py
│   │   │   │   ├── policies.py
│   │   │   │   └── prompts.py
│   │   │   ├── domain/
│   │   │   │   ├── rules.py
│   │   │   │   ├── cascading.py
│   │   │   │   ├── decision_trace.py
│   │   │   │   ├── scenarios.py
│   │   │   │   └── spares.py
│   │   │   └── guardrails/
│   │   │       ├── input.py
│   │   │       ├── retrieval.py
│   │   │       ├── output.py
│   │   │       └── actions.py
│   │   ├── alembic/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── ui/
│   │   ├── app.py
│   │   ├── api_client.py
│   │   ├── pages/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── mcp-server/
│   │   ├── src/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── telemetry-simulator/
│   └── evaluator/
│
├── packages/
│   └── vajra-core/
│       ├── src/vajra_core/
│       ├── tests/
│       └── pyproject.toml
│
├── models/
│   ├── triton-model-repository/
│   │   └── vajra-risk/
│   │       ├── config.pbtxt
│   │       └── 1/model.py
│   ├── metadata/
│   └── test-fixtures/
│
├── pipelines/
│   └── airflow/
│       ├── dags/
│       │   ├── vajra_rag_ingestion.py
│       │   ├── vajra_drift_evaluation.py
│       │   └── vajra_model_evaluation.py
│       └── values/
│
├── platform/
│   ├── kind/
│   ├── helm/
│   │   ├── vajra-api/
│   │   ├── vajra-ui/
│   │   ├── mcp-server/
│   │   └── evaluator/
│   ├── kserve/
│   ├── envoy-ai-gateway/
│   ├── milvus/
│   ├── postgres/
│   ├── monitoring/
│   ├── keda/
│   ├── gatekeeper/
│   ├── backstage/
│   └── argocd/
│
├── infra/
│   └── azure/
│       ├── modules/
│       └── environments/
│           ├── plan-only/
│           └── aks-poc/
│
├── backstage/
│   └── templates/
│       ├── model-endpoint/
│       ├── vector-database/
│       └── rag-agent-service/
│
├── docs/
├── scripts/
├── tests/acceptance/
├── Makefile
└── README.md
```

---

## 5. Exact file-by-file refactor map

### 5.1 `app.py` → UI-only application

Current issue: `app.py` directly imports and invokes ML, RAG, graph, feedback, and SQLite objects.

Required change:

- Move reusable CSS/render functions into `services/ui/components/`.
- Replace every direct module call with `VajraApiClient` HTTP calls.
- Streamlit session state may retain only UI state such as selected alarm and chat display.
- Server-side state must be identified by `run_id`, `thread_id`, `approval_id`, and `request_id`.

Examples:

```text
ml_service.predict_condition(...)             -> POST /api/v1/predictions
ml_service.plant_topology(...)                 -> GET  /api/v1/assets/topology
ml_service.maintenance_queue(...)              -> GET  /api/v1/alarms
ml_service.telemetry_window(...)               -> GET  /api/v1/telemetry/window
answer_maintenance_query(...)                  -> POST /api/v1/agents/investigations
runtime_store.save_feedback(...)               -> POST /api/v1/feedback
runtime_store.load_logbook_events(...)         -> GET  /api/v1/logbook
runtime_store.update_log_status(...)           -> PATCH /api/v1/logbook/{log_id}
run_gold_tests(...)                            -> POST /api/v1/evaluations/runs
```

### 5.2 `src/agentic/config.py`

Replace frozen dataclass/environment reads with `pydantic-settings`:

- `APP_ENV`
- `DATABASE_URL`
- `TRITON_BASE_URL`
- `VLLM_BASE_URL`
- `MILVUS_URI`
- `MILVUS_COLLECTION_ALIAS`
- `EMBEDDING_MODEL`
- `LANGSMITH_*`
- `OTEL_EXPORTER_OTLP_ENDPOINT`
- `MCP_SERVER_URL`
- `MAX_AGENT_STEPS`
- `MAX_REQUEST_TOKENS`
- `KILL_SWITCH_*`

Support config profiles:

```text
local-kind
aks-poc
unit-test
```

### 5.3 `src/agentic/ml_service.py`

Split into three responsibilities.

#### A. Domain response builder

Keep:

- risk-band normalization;
- asset naming;
- evidence formatting;
- topology calculations;
- alarm grouping;
- maintenance queue construction.

Move to `packages/vajra-core`.

#### B. Triton model runtime

Move exact joblib inference into a Triton Python backend first. This preserves the existing four-model logic without risky conversion differences:

```text
anomaly classifier
fault multilabel classifier
RUL urgency classifier
proxy RUL regressor
```

Triton input:

```text
FEATURES: FP32 [batch, feature_count]
```

Triton outputs:

```text
ANOMALY_PROBABILITY
FAULT_PROBABILITIES
RUL_CLASS
PROXY_RUL_OBSERVATIONS
```

The FastAPI service computes the final response contract, rules, evidence, and risk score.

Later, convert individual compatible estimators to ONNX/TensorRT only after parity tests pass.

#### C. Feature data provider

The current service reads a complete local parquet file. Replace this with an interface:

```python
class FeatureProvider(Protocol):
    def get_by_row(self, row_index: int) -> FeatureRecord: ...
    def get_by_asset_time(self, asset_id: str, timestamp: datetime) -> FeatureRecord: ...
    def get_window(self, asset_id: str, end: datetime, size: int) -> list[FeatureRecord]: ...
```

Phase 1 implementations:

- `ParquetReplayFeatureProvider` for existing demo rows.
- `InMemoryTelemetryFeatureProvider` for simulated streaming windows.

This retains the existing Vajra demo while preparing for real telemetry.

### 5.4 `src/agentic/llm.py`

Replace OpenAI-only construction with an OpenAI-compatible provider abstraction:

```python
ChatOpenAI(
    base_url=settings.vllm_base_url,
    api_key=settings.vllm_api_key or "EMPTY",
    model=settings.vllm_model,
)
```

Add:

- connection timeout;
- request timeout;
- retry policy;
- streaming support;
- prompt/completion token extraction;
- model-version headers;
- Prometheus metrics;
- LangSmith trace metadata;
- deterministic fallback.

Retain an optional hosted provider adapter, but vLLM must be the default Phase 1 path.

### 5.5 `src/agentic/rag.py`

Replace FAISS and OpenAI embeddings.

New design:

- Local embedding model: `sentence-transformers/all-MiniLM-L6-v2` or approved equivalent.
- Milvus collection with vector plus metadata.
- Candidate/production collection aliases.
- Filter by document version, asset type, tenant, and effective date.
- Return normalized similarity and citation fields.
- Retain keyword fallback only as an explicit degraded mode.

Remove:

- FAISS pickle loading;
- `allow_dangerous_deserialization=True`;
- OpenAI embedding dependency;
- direct document ingestion from request-serving code.

Document ingestion moves to Airflow.

### 5.6 `src/agentic/runtime_store.py`

Replace direct SQLite operations with repository interfaces and SQLAlchemy/Alembic.

Phase 1 primary backend: single PostgreSQL pod with persistent local storage.

SQLite may remain only for unit tests or a one-process fallback.

Required tables:

```text
agent_runs
agent_run_events
approvals
logbook_events
feedback_events
evaluation_runs
evaluation_results
kill_switch_events
model_deployments
rag_index_versions
audit_events
```

PostgreSQL is required because KEDA/replicas and durable HITL cannot safely rely on a pod-local SQLite file.

### 5.7 `src/agentic/graph.py`

Keep the existing reasoning sequence but replace global singletons with injected dependencies.

Target graph:

```text
START
  -> request_guardrail
  -> router
  -> load_context
  -> predictive_inference
  -> physical_rules
  -> cascading_impact
  -> rag_retrieval
  -> root_cause
  -> planner
  -> action_policy
       -> no action: report
       -> approval needed: interrupt/persist
       -> automatically allowed read action: execute_tool
  -> output_guardrail
  -> audit
END
```

Required changes:

- Use durable PostgreSQL checkpointer instead of `MemorySaver`.
- Add `run_id`, `request_id`, `tenant_id`, and version metadata to state.
- Use MCP clients for tool execution.
- Add true `interrupt()`/resume behavior for HITL.
- Separate read-only and write tools.
- Add maximum-step/timeout protection.
- Check kill switches before each model or tool action.
- Persist node events for audit and observability.

### 5.8 `rules.py`, `cascading.py`, `decision_trace.py`, `spares.py`

Mostly reusable. Required changes:

- Remove implicit pandas/global-service dependencies where possible.
- Accept typed domain objects or dictionaries.
- Add unit tests using golden fixtures.
- Add rule/version identifiers to outputs.

### 5.9 `demo_scenarios.py`

Keep the scenario logic, but expose it through API endpoints and telemetry simulator events instead of process-local overrides.

The simulator should create an immutable scenario run with:

```text
scenario_run_id
base_row_index
scenario_name
stand
severity
created_at
```

### 5.10 `eval_harness.py`

Convert to evaluator service/Airflow tasks.

Add separate suites:

- predictive model parity;
- RAG retrieval recall/citation checks;
- agent graph path checks;
- guardrail checks;
- canary quality comparison;
- SLO checks.

Evaluation results must be persisted, not only returned as a DataFrame.

### 5.11 `ingest_faiss.py` and `vector_store/`

Deprecate/remove after Milvus migration.

Replace with:

```text
pipelines/airflow/dags/vajra_rag_ingestion.py
rag/indexing/*.py
rag/evaluation/*.py
```

### 5.12 `.env`

- Delete from repository.
- Add `.env.example` containing names only.
- Local secrets: untracked `.env.local` or Kubernetes Secret.
- AKS: Entra Workload Identity + Azure Key Vault CSI.
- Rotate any existing key that may have been shared in the archive/repository.

---

## 6. API contract

Use `/api/v1` for stable application APIs. Do not expose Triton, vLLM, Milvus, or PostgreSQL directly to the UI.

### Platform endpoints

```text
GET  /health/live
GET  /health/ready
GET  /api/v1/version
GET  /metrics
```

### Telemetry and demo scenarios

```text
POST   /api/v1/telemetry/events
GET    /api/v1/telemetry/window
POST   /api/v1/demo/scenarios
DELETE /api/v1/demo/scenarios/{scenario_run_id}
```

### Predictive maintenance

```text
POST /api/v1/predictions
GET  /api/v1/assets/topology
GET  /api/v1/alarms
GET  /api/v1/alarms/{alarm_id}
```

`POST /predictions` must accept either:

```json
{"source":"replay","row_index":18792}
```

or:

```json
{"source":"features","asset_id":"TCM-STAND-3","timestamp":"...","features":{}}
```

### RAG

```text
POST /api/v1/rag/query
POST /api/v1/rag/ingestion/runs
GET  /api/v1/rag/ingestion/runs/{run_id}
GET  /api/v1/rag/indexes
POST /api/v1/rag/indexes/{version}/promote
```

### Agent/HITL

```text
POST /api/v1/agents/investigations
GET  /api/v1/agents/runs/{run_id}
POST /api/v1/agents/runs/{run_id}/resume
GET  /api/v1/approvals
POST /api/v1/approvals/{approval_id}/decision
```

### Logbook and feedback

```text
GET   /api/v1/logbook
GET   /api/v1/logbook/{log_id}
PATCH /api/v1/logbook/{log_id}
POST  /api/v1/feedback
GET   /api/v1/feedback
```

### Evaluation and controls

```text
POST /api/v1/evaluations/runs
GET  /api/v1/evaluations/runs/{run_id}
GET  /api/v1/model-health
GET  /api/v1/controls/kill-switches
PUT  /api/v1/controls/kill-switches/{name}
```

### Response metadata required on all AI responses

```json
{
  "request_id": "uuid",
  "generated_at": "ISO-8601",
  "app_version": "...",
  "predictive_model_version": "...",
  "llm_model_version": "...",
  "prompt_version": "...",
  "rag_index_version": "..."
}
```

A complete draft OpenAPI file accompanies this blueprint.

---

## 7. Database design

### `agent_runs`

- `run_id`
- `thread_id`
- `request_id`
- `tenant_id`
- `status`
- `query`
- `asset_id`
- `alarm_id`
- version fields
- timestamps

### `agent_run_events`

One row per graph node/tool/model event:

- `event_id`
- `run_id`
- `node_name`
- `event_type`
- `input_json`
- `output_json`
- `latency_ms`
- `status`
- timestamp

### `approvals`

- `approval_id`
- `run_id`
- `action_type`
- `action_payload_json`
- `risk_level`
- `requested_by`
- `decision`
- `decided_by`
- `reason`
- timestamps

### Existing logbook/feedback tables

Migrate current fields and add:

- `request_id`
- `run_id`
- `tenant_id`
- `app_version`
- `model_version`
- `prompt_version`
- `index_version`

### `evaluation_runs` and `evaluation_results`

Persist quality measurements used for dashboards and canary rollback.

---

## 8. Detailed implementation sequence

## Work Package 0 — Baseline freeze and security

### Objective

Create a reproducible reference before changing architecture.

### Actions

1. Remove `.env` from the repository and rotate exposed keys.
2. Create a clean Git branch/tag: `vajra-v2-baseline`.
3. Add all missing model/parquet artifacts outside Git or via Git LFS/object storage.
4. Create three golden inference fixtures and expected JSON outputs.
5. Run the existing Streamlit app and record screenshots/output.
6. Pin current Python dependencies.

### Done when

The original application runs and golden outputs are reproducible.

---

## Work Package 1 — Extract `vajra-core`

### Objective

Separate reusable domain logic from Streamlit and infrastructure.

### Actions

1. Move rules, cascading, decision trace, prompts, scenario logic, and spares to `packages/vajra-core`.
2. Introduce typed Pydantic domain models.
3. Remove Streamlit imports from core.
4. Add unit tests for every rule and scenario.

### Done when

Core tests run without Streamlit, database, OpenAI, or Kubernetes.

---

## Work Package 2 — Build FastAPI skeleton

### Objective

Create the single application boundary consumed by UI and tools.

### Actions

1. Add FastAPI application factory.
2. Add `/health/live`, `/health/ready`, `/version`, and `/metrics`.
3. Add request-ID middleware and structured logging.
4. Add Pydantic request/response schemas.
5. Add exception handling and stable error format.
6. Generate and review OpenAPI.

### Done when

The API starts locally, health checks pass, and OpenAPI validates.

---

## Work Package 3 — Persistence and durable LangGraph state

### Objective

Make scaling and HITL reliable.

### Actions

1. Add PostgreSQL Helm deployment with PVC for local Kind.
2. Add SQLAlchemy models and Alembic migrations.
3. Implement repository interfaces.
4. Migrate logbook, feedback, and evaluation persistence.
5. Configure LangGraph PostgreSQL checkpointer.
6. Add approval table and pause/resume tests.

### Done when

An agent run pauses, the API pod is restarted, and the run resumes from persisted state.

---

## Work Package 4 — Predictive inference through KServe/Triton

### Objective

Preserve current ML output while standardizing serving.

### Actions

1. Package joblib artifacts in a Triton Python backend.
2. Define numeric input/output tensors.
3. Add KServe `ServingRuntime`/`InferenceService` manifests for CPU.
4. Implement async Triton client in FastAPI.
5. Keep replay and feature-input request modes.
6. Run parity tests against direct `MLModelService.predict_condition`.

### Done when

All golden predictions match the original application within defined tolerance.

---

## Work Package 5 — CPU vLLM and LLM abstraction

### Objective

Replace direct OpenAI dependency with self-hosted OpenAI-compatible inference.

### Actions

1. Build/test CPU vLLM image for an approved small Llama-family model.
2. Deploy with KServe custom runtime locally.
3. Add stable/candidate endpoints.
4. Update LLM client with vLLM base URL.
5. Record token counts, latency, model version, and failures.
6. Keep deterministic fallback.

### Done when

Vajra graph calls vLLM through an internal service and no OpenAI key is required.

---

## Work Package 6 — Milvus RAG and Airflow

### Objective

Replace local FAISS with a persistent, versioned RAG lifecycle.

### Actions

1. Deploy Milvus standalone with PVC.
2. Define collection schema and aliases.
3. Add local CPU embedding model.
4. Implement Airflow ingestion DAG.
5. Add document/version hashing and idempotency.
6. Add retrieval evaluation before index promotion.
7. Implement API Milvus retriever and citation response.

### Done when

A DAG builds a candidate index, gold retrieval tests pass, and the alias is promoted.

---

## Work Package 7 — Agent, MCP, guardrails, HITL, kill switches

### Objective

Turn the existing suggestion workflow into a governed action workflow.

### Actions

1. Refactor graph dependencies to API clients/repositories.
2. Add MCP server with read-only tools first.
3. Add mock write tool: `create_work_order`.
4. Add input, retrieval, output, and action guardrails.
5. Add PII redaction.
6. Add approval interrupt and resume.
7. Add kill switches checked before LLM/tool execution.
8. Add max steps, timeouts, and audit events.

### Done when

A write tool cannot run before approval, remains blocked after restart, and is immediately disabled by the kill switch.

---

## Work Package 8 — Streamlit UI migration

### Objective

Retain the Vajra experience while removing in-process coupling.

### Actions

1. Add typed `VajraApiClient` using `httpx`.
2. Convert page by page:
   - Command Center.
   - Alarm Investigation.
   - Telemetry Replay.
   - Copilot.
   - Logbook/Feedback.
   - Model Health.
3. Replace process-local demo override with scenario API.
4. Display request/run/version metadata.
5. Add approval UI and kill-switch status.

### Done when

The UI imports no ML/RAG/graph/runtime-store modules and communicates only through HTTP.

---

## Work Package 9 — Gateway, observability, SLOs, and security

### Objective

Create a governed platform boundary and unified monitoring.

### Actions

1. Deploy Envoy Gateway plus Envoy AI Gateway resources.
2. Route `/api/v1` only to Vajra API; keep model/data services internal.
3. Add local request and token budgets.
4. Add Prometheus metrics and ServiceMonitors.
5. Add OpenTelemetry instrumentation and collector.
6. Add LangSmith traces with redaction.
7. Create Grafana dashboards.
8. Add Gatekeeper policies and NetworkPolicies.
9. Add audit-log retention settings.

### Done when

One request is traceable from gateway through API, Triton, Milvus, vLLM, MCP, and database; excessive requests return 429; insecure manifests are rejected.

---

## Work Package 10 — KEDA, canary, and automated rollback

### Objective

Demonstrate elasticity and safe promotion.

### Actions

1. Expose pending-request/queue metrics.
2. Add KEDA ScaledObjects for API/evaluator and feasible CPU inference replicas.
3. Run load tests.
4. Deploy stable and candidate revisions.
5. Route a small traffic percentage to candidate.
6. Run evaluator against both.
7. Commit rollback to GitOps repo when thresholds fail.
8. Let ArgoCD reconcile candidate weight to zero.

### Done when

Replicas scale under load and a deliberately degraded candidate is returned to zero traffic through GitOps.

---

## Work Package 11 — Backstage templates

### Objective

Create repeatable platform golden paths.

Build three templates:

1. Model endpoint.
2. Milvus/vector database.
3. RAG/agent service.

Each must generate:

- source skeleton;
- Dockerfile;
- Helm chart;
- ArgoCD Application;
- CI workflow;
- monitoring resources;
- OPA-required labels;
- local and AKS values.

### Done when

Each template creates a repository/component that passes tests and deploys to Kind.

---

## Work Package 12 — Azure readiness

### Objective

Make the same artifacts deployable to AKS without creating paid resources during development.

### Actions

1. Add Azure Terraform modules for resource group, network, AKS, identity, optional ACR, storage, Key Vault, and budget.
2. Enable AKS OIDC issuer and Workload Identity in the AKS module.
3. Add Key Vault CSI and workload service-account annotations.
4. Add `values-aks.yaml` for storage classes and identity.
5. Run `terraform fmt`, `validate`, and `plan` only.
6. Add optional short-lived AKS acceptance workflow with explicit budget guard.

### Done when

Terraform produces a reviewed plan and all Helm/Kubernetes resources render for AKS.

---

## 9. Airflow DAGs

### `vajra_rag_ingestion`

```text
discover_documents
 -> validate_files
 -> parse_documents
 -> redact_sensitive_content
 -> chunk_documents
 -> create_embeddings
 -> upsert_candidate_collection
 -> run_retrieval_evaluation
 -> promote_collection_alias
 -> emit_metrics
```

### `vajra_drift_evaluation`

```text
collect_recent_samples
 -> calculate_feature_drift
 -> calculate_prediction_drift
 -> run_rag_gold_suite
 -> run_agent_gold_suite
 -> persist_results
 -> trigger_alert_or_training_candidate
```

### `vajra_model_evaluation`

```text
load_candidate_metadata
 -> predictive_parity_tests
 -> RAG_quality_tests
 -> latency_error_tests
 -> policy_checks
 -> write_promotion_recommendation
```

---

## 10. Azure-specific configuration

### Local profile

- Kind.
- Local Path PVCs.
- Kubernetes Secrets.
- Local PostgreSQL.
- Local image loading/GHCR.
- No Azure charges.

### AKS profile

- Entra Workload Identity.
- Key Vault CSI.
- Azure Disk StorageClass.
- Optional ACR.
- Azure Blob or object-storage adapter for model/document artifacts.
- Optional Azure Monitor export.

Application code must not import Azure SDKs directly except through adapters. Use interfaces for object storage and secret/config providers.

---

## 11. Test strategy

### Unit tests

- Engineering rules.
- Cascading calculations.
- Risk response builder.
- Scenario transformations.
- Guardrails.
- API schemas.

### Contract tests

- FastAPI to Triton.
- FastAPI to vLLM.
- FastAPI to Milvus.
- FastAPI to MCP.

### Parity tests

Direct current inference versus Triton response on golden rows.

### RAG tests

- expected document in top-k;
- citation correctness;
- no-answer behavior;
- tenant filter.

### Agent tests

- graph path;
- maximum steps;
- write action approval;
- resume after pod restart;
- kill switch.

### Platform tests

- ArgoCD drift correction;
- KEDA scale-out/scale-in;
- rate limits;
- OPA rejection;
- PVC persistence;
- canary rollback.

---

## 12. Definition of done

The refactor is complete only when:

1. Streamlit uses only the Vajra API.
2. Existing golden ML predictions match Triton outputs.
3. CPU vLLM provides the LLM endpoint.
4. Milvus replaces FAISS and persists across pod restart.
5. Airflow builds and promotes the RAG index.
6. LangGraph uses durable PostgreSQL checkpoints.
7. HITL survives API pod restart.
8. MCP tools are governed by read/write policies.
9. Guardrails, PII redaction, and kill switches work.
10. Envoy enforces request/token limits.
11. Metrics, traces, LLM traces, and audit records correlate through request/run IDs.
12. ArgoCD reconciles drift and performs rollback.
13. KEDA scales under load.
14. A poor candidate is automatically removed from traffic through GitOps.
15. Three Backstage templates produce deployable components.
16. Azure Terraform validates and plans without provisioning paid infrastructure.

---

## 13. Recommended first implementation milestone

Do not install every platform component first. The safest sequence is:

```text
1. Restore missing model assets and run current app.
2. Freeze golden outputs.
3. Extract vajra-core.
4. Build FastAPI prediction/health endpoints.
5. Package Triton model and prove parity.
6. Migrate Streamlit Prediction/Alarm pages to API.
7. Add PostgreSQL and migrate logbook/feedback.
8. Refactor LangGraph with durable checkpointing.
9. Add Milvus and RAG.
10. Add CPU vLLM.
11. Add MCP/HITL/guardrails.
12. Add Kind/Helm/ArgoCD and remaining platform components.
```

This avoids debugging application refactoring, model serving, Kubernetes, and LLM infrastructure simultaneously.
