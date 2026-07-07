# Pin this tag to the Triton release approved for the project.
FROM nvcr.io/nvidia/tritonserver:24.08-py3

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/vajra \
    VAJRA_APP_ROOT=/opt/vajra \
    TCM_MODELLING_ROOT=/opt/vajra/tcm_modelling

WORKDIR /opt/vajra

COPY infra/triton/requirements.txt /tmp/vajra-triton-requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/vajra-triton-requirements.txt

COPY src /opt/vajra/src
COPY tcm_modelling /opt/vajra/tcm_modelling
COPY triton_model_repository /models

EXPOSE 8000 8001 8002

CMD ["tritonserver", "--model-repository=/models", "--strict-model-config=true"]
