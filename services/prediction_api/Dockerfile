FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY services/prediction_api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY src /app/src
COPY services /app/services
COPY packages /app/packages
COPY tcm_modelling /app/tcm_modelling

RUN pip install --no-cache-dir -e /app/packages/vajra_core

EXPOSE 8000

CMD ["uvicorn", "services.prediction_api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
