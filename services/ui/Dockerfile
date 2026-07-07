FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install --no-cache-dir 'httpx>=0.27,<1'

COPY app.py /app/app.py
COPY src /app/src
COPY services /app/services
COPY docs /app/docs
COPY vector_store /app/vector_store
COPY data /app/data
COPY tcm_modelling /app/tcm_modelling

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
