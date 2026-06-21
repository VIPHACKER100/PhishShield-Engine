import os
import json
from fastapi import APIRouter
from src.api.dependencies import ab_test

router = APIRouter(tags=["analytics"])

@router.get("/ab/summary")
async def get_ab_summary():
    return ab_test.summary()

@router.get("/analytics")
async def analytics():
    metrics_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "models", "metrics.json")
    if not os.path.exists(metrics_path):
        return {"error": "No metrics available. Train models first."}
    with open(metrics_path) as f:
        data = json.load(f)
    return data
