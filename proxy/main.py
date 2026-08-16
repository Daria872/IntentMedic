from fastapi import FastAPI

from .decision_engine import assess_message
from .schemas import InterceptRequest, InterceptResponse

app = FastAPI(title="IntentMedic Tier 1 Proxy", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/intercept", response_model=InterceptResponse)
def intercept(payload: InterceptRequest) -> InterceptResponse:
    decision = assess_message(payload.message)
    return InterceptResponse(**decision)
