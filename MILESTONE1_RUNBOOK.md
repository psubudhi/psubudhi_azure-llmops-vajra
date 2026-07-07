# Vajra Azure LLMOps — First Coding Milestone Runbook

This milestone deliberately preserves the current Vajra prediction logic. The first goal is to create a stable API boundary and prove identical predictions before changing runtimes, storage, RAG, or agent orchestration.

## Milestone outcome

At the end of this milestone:

1. the original Vajra application still runs as `app_legacy.py`;
2. three golden predictions are frozen;
3. reusable domain code exists under `packages/vajra_core`;
4. FastAPI exposes health, prediction, alarm, topology, telemetry, and model-health endpoints;
5. the current Streamlit `app.py` retrieves prediction data through FastAPI;
6. the same predictor runs inside a Triton Python backend on CPU;
7. automated scripts verify local API and Triton parity.

---

## 1. Restore the model assets

Place the files at these exact paths:

```text
tcm_modelling/models/model_metadata.json
tcm_modelling/models/anomaly_classifier.joblib
tcm_modelling/models/fault_multilabel_classifier.joblib
tcm_modelling/models/rul_urgency_classifier.joblib
tcm_modelling/models/proxy_rul_regressor.joblib
tcm_modelling/data/processed/tcm_features_dataset3.parquet
```

Optional historical-neighbour files:

```text
tcm_modelling/models/case_memory_preprocessor.joblib
tcm_modelling/models/case_memory_nearest_neighbors.joblib
```

Verify:

```bash
python scripts/check_artifacts.py
```

Expected result:

```text
All mandatory artifacts are present.
```

If joblib loading reports a scikit-learn or XGBoost compatibility error, recreate the Python environment using the versions that were used when the notebook produced the artifacts. Do not retrain or resave models until the baseline outputs have been captured.

---

## 2. Create a clean Python environment

Use Python 3.11.

```bash
cd vajra_milestone1
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-milestone1.txt
cp .env.example .env
```

The predictive pages do not require an OpenAI key. The existing RCA/Copilot pages fall back gracefully when no key is configured.

Validate imports:

```bash
python -m compileall -q packages services scripts src app.py app_legacy.py
pytest packages/vajra_core/tests -q
```

---

## 3. Run and freeze the existing baseline

`app_legacy.py` is the unchanged Streamlit application from the uploaded ZIP.

```bash
streamlit run app_legacy.py
```

Manually verify:

- Plant Command Center loads.
- Alarm Investigation page loads.
- Latest prediction works.
- Highest-risk prediction works.
- One demo scenario can be applied and cleared.
- Telemetry charts load.

Do not modify model code if these fail. First correct artifact paths or dependency versions.

---

## 4. Freeze three golden predictions

Generate normal, warning, and critical reference outputs:

```bash
python scripts/freeze_golden_predictions.py
```

Output:

```text
tests/golden/golden_predictions.json
```

Commit this file with the code. It is the regression contract for local FastAPI, Triton, KServe, and later AKS deployments.

Review it:

```bash
python -m json.tool tests/golden/golden_predictions.json | less
```

The file records:

- selected positional row index;
- original timestamp index;
- expected fault and stand;
- anomaly probability;
- RUL band;
- risk score and band;
- health index;
- evidence;
- SHA-256 of `model_metadata.json`.

---

## 5. Understand the extracted `vajra-core`

Reusable infrastructure-independent code is located at:

```text
packages/vajra_core/src/vajra_core/
```

It currently contains:

```text
rules.py
cascading.py
decision_trace.py
prompts.py
spares.py
utils.py
schemas.py
```

Install it in editable mode through `requirements-milestone1.txt`.

During this milestone, old `src.agentic.*` imports remain available to avoid breaking the application. In the next work package, imports will be migrated module by module to `vajra_core`.

---

## 6. Start the FastAPI prediction service in local mode

Terminal 1:

```bash
source .venv/bin/activate
export TCM_MODELLING_ROOT=./tcm_modelling
export VAJRA_PREDICTION_BACKEND=local
uvicorn services.prediction_api.app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload
```

Validate liveness:

```bash
curl -s http://127.0.0.1:8000/health/live | python -m json.tool
```

Validate artifact readiness:

```bash
curl -s http://127.0.0.1:8000/health/ready | python -m json.tool
```

Open API documentation:

```text
http://127.0.0.1:8000/docs
```

Create a prediction:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/predictions \
  -H 'Content-Type: application/json' \
  -d '{"strategy":"highest_risk","row_index":null}' \
  | python -m json.tool
```

Relevant endpoints:

```text
GET  /health/live
GET  /health/ready
GET  /api/v1/model/info
POST /api/v1/predictions
GET  /api/v1/rows/{row_index}
GET  /api/v1/topology
GET  /api/v1/alarms/active
GET  /api/v1/alarms/events
GET  /api/v1/maintenance/queue
GET  /api/v1/telemetry/window
GET  /api/v1/telemetry/groups
GET  /api/v1/model/metrics
GET  /api/v1/model/drift
GET  /api/v1/model/feature-importance
POST /api/v1/demo/apply
POST /api/v1/demo/clear
```

---

## 7. Prove FastAPI parity

Keep the API running, then execute:

```bash
python scripts/verify_api_golden.py \
  --base-url http://127.0.0.1:8000
```

Required result:

```text
PASS normal
PASS warning
PASS critical
All API predictions match the frozen baseline.
```

Do not proceed to Triton if this fails.

---

## 8. Run the migrated Streamlit application

The only import-level change in `app.py` is that the object named `ml_service` is now a compatibility client backed by FastAPI:

```python
from services.ui.prediction_client import prediction_api as ml_service
```

Terminal 2:

```bash
source .venv/bin/activate
export VAJRA_PREDICTION_API_URL=http://127.0.0.1:8000
streamlit run app.py
```

Validate the same pages used in the legacy baseline:

- Plant Command Center;
- Alarm Investigation & RCA prediction context;
- Live Telemetry Replay;
- Model Health & Evaluation;
- demo scenario application and clearing.

The Streamlit process should no longer load prediction artifacts for those page-level calls. The current LangGraph agent still uses the legacy in-process model service internally; that is intentionally deferred to the next refactor package.

---

## 9. Build the Triton CPU image

The Triton Python backend reuses the same `MLModelService`, making it the safest first model-serving migration.

Build:

```bash
docker build \
  -f infra/triton/Dockerfile \
  -t vajra-triton:0.1.0 \
  .
```

Run Triton on host ports 8002–8004 because FastAPI already uses 8000:

```bash
docker run --rm --name vajra-triton \
  -p 8002:8000 \
  -p 8003:8001 \
  -p 8004:8002 \
  vajra-triton:0.1.0
```

Validate:

```bash
curl -f http://127.0.0.1:8002/v2/health/live
curl -f http://127.0.0.1:8002/v2/health/ready
curl -f http://127.0.0.1:8002/v2/models/vajra_predictor/ready
```

Inspect model status:

```bash
curl -s http://127.0.0.1:8002/v2/models/vajra_predictor | python -m json.tool
```

---

## 10. Prove direct Triton parity

With Triton running:

```bash
python scripts/verify_triton_parity.py \
  --url 127.0.0.1:8002
```

Required result:

```text
PASS normal
PASS warning
PASS critical
Triton output matches all frozen predictions.
```

If Triton cannot deserialize a joblib model, inspect the model-training environment and pin the exact scikit-learn/XGBoost versions in `infra/triton/requirements.txt`.

---

## 11. Switch FastAPI from local inference to Triton

Stop FastAPI and restart it:

```bash
export VAJRA_PREDICTION_BACKEND=triton
export VAJRA_TRITON_URL=127.0.0.1:8002
export VAJRA_TRITON_MODEL_NAME=vajra_predictor
uvicorn services.prediction_api.app.main:app \
  --host 0.0.0.0 \
  --port 8000
```

Verify:

```bash
curl -s http://127.0.0.1:8000/api/v1/version | python -m json.tool
python scripts/verify_api_golden.py --base-url http://127.0.0.1:8000
```

The version endpoint must show:

```json
{
  "prediction_backend": "triton"
}
```

Then reload `app.py`. The Streamlit prediction pages now follow:

```text
Streamlit → FastAPI → Triton CPU → existing Vajra model artifacts
```

### Temporary demo-mode limitation

The in-memory demo override remains local to FastAPI's metadata service during this first milestone. Normal replay predictions are fully supported through Triton. Request-scoped synthetic features will replace global demo state in the subsequent API refactor.

---

## 12. Optional Docker Compose run

Local API and UI:

```bash
docker compose -f docker-compose.milestone1.yml up --build
```

Triton profile:

```bash
VAJRA_PREDICTION_BACKEND=triton \
  docker compose -f docker-compose.milestone1.yml \
  --profile triton up --build
```

For the first debugging cycle, running processes separately is preferred because logs are easier to isolate.

---

## 13. Commit sequence

Use separate commits:

```text
1. chore: restore and validate Vajra model artifacts
2. test: freeze Vajra golden predictions
3. refactor: extract reusable vajra-core package
4. feat: add FastAPI prediction boundary
5. feat: migrate Streamlit prediction calls to API client
6. feat: package Vajra predictor for Triton CPU
7. test: add local and Triton parity verification
```

Do not commit `.env`, credentials, model files that exceed repository limits, generated SQLite databases, or Terraform state.

---

## Definition of done

The milestone is complete only when:

- `app_legacy.py` produces the original results;
- golden JSON contains three cases;
- FastAPI local mode matches every golden case;
- migrated `app.py` loads prediction pages through FastAPI;
- Triton reports the model ready;
- direct Triton predictions match every golden case;
- FastAPI Triton mode matches every golden case;
- no secret is committed;
- all code compiles and unit tests pass.
