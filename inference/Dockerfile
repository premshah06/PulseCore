FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV ONNX_MODEL_PATH=ml/models/vigil_anomaly_infra.onnx
ENV INFERENCE_PORT=8001

EXPOSE 8001

CMD ["sh", "-c", "uvicorn inference.main:app --host 0.0.0.0 --port ${INFERENCE_PORT}"]
