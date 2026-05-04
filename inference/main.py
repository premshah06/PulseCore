"""PulseCore Inference Sidecar — FastAPI application.

Environment variables:
  ONNX_MODEL_PATH  path to vigil_anomaly_{domain}.onnx  (required)
  FEATURE_MAP_PATH path to feature_map.json              (default: same dir as model)
  INFERENCE_PORT   TCP port to bind                      (default: 8001)

Start with:
  ONNX_MODEL_PATH=ml/models/vigil_anomaly_infra.onnx \
  uvicorn inference.main:app --host 0.0.0.0 --port 8001
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status

from inference.predictor import Predictor
from inference.schemas import AnomalyResult, PredictRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Module-level so tests can inject a pre-built Predictor.
_predictor: Predictor | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _predictor

    model_path = Path(
        os.environ.get("ONNX_MODEL_PATH", "ml/models/vigil_anomaly_infra.onnx")
    )
    feature_map_path = Path(
        os.environ.get(
            "FEATURE_MAP_PATH",
            str(model_path.parent / "feature_map.json"),
        )
    )

    logger.info("Loading ONNX model: %s", model_path)
    _predictor = Predictor(model_path, feature_map_path)
    logger.info("Inference sidecar ready (domain=%s).", _predictor.domain)

    yield

    logger.info("Inference sidecar shutting down.")
    _predictor = None


app = FastAPI(
    title="PulseCore Inference Sidecar",
    description="Anomaly detection via ONNX IsolationForest. See CONTRACTS.md.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", summary="Liveness + model-load check")
async def health() -> dict:
    return {
        "status": "ok",
        "model_loaded": _predictor is not None,
        "domain": _predictor.domain if _predictor else None,
    }


@app.post(
    "/predict",
    response_model=AnomalyResult,
    summary="Score one event against the loaded Isolation Forest model",
)
async def predict(request: PredictRequest) -> AnomalyResult:
    if _predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Check sidecar startup logs.",
        )
    try:
        return _predictor.predict(request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
