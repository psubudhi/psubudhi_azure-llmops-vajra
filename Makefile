PYTHON ?= python
API_URL ?= http://127.0.0.1:8000

.PHONY: install check-artifacts baseline api ui golden verify-api triton-build triton-run verify-triton test

install:
	$(PYTHON) -m pip install -r requirements-milestone1.txt

check-artifacts:
	$(PYTHON) scripts/check_artifacts.py

baseline:
	streamlit run app.py

api:
	uvicorn services.prediction_api.app.main:app --host 0.0.0.0 --port 8000 --reload

ui:
	VAJRA_PREDICTION_API_URL=$(API_URL) streamlit run app.py

golden:
	$(PYTHON) scripts/freeze_golden_predictions.py

verify-api:
	$(PYTHON) scripts/verify_api_golden.py --base-url $(API_URL)

triton-build:
	docker build -f infra/triton/Dockerfile -t vajra-triton:0.1.0 .

triton-run:
	docker run --rm --name vajra-triton -p 8002:8000 -p 8003:8001 -p 8004:8002 vajra-triton:0.1.0

verify-triton:
	$(PYTHON) scripts/verify_triton_parity.py --url 127.0.0.1:8002

test:
	$(PYTHON) -m compileall -q packages services scripts src
	$(PYTHON) -m pytest packages/vajra_core/tests -q
