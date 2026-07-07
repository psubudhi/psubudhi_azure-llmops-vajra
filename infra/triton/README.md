# Vajra Triton CPU image

Before building, restore these files under `tcm_modelling/`:

- `models/model_metadata.json`
- `models/anomaly_classifier.joblib`
- `models/fault_multilabel_classifier.joblib`
- `models/rul_urgency_classifier.joblib`
- `models/proxy_rul_regressor.joblib`
- optional case-memory joblib files
- `data/processed/tcm_features_dataset3.parquet`

Build and run:

```bash
docker build -f infra/triton/Dockerfile -t vajra-triton:0.1.0 .
docker run --rm --name vajra-triton \
  -p 8000:8000 -p 8001:8001 -p 8002:8002 \
  vajra-triton:0.1.0
```

Check readiness:

```bash
curl -f http://127.0.0.1:8000/v2/health/ready
curl -f http://127.0.0.1:8000/v2/models/vajra_predictor/ready
```
