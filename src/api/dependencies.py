from fastapi import Request
from typing import Optional
from src.api.auth import verify_token, verify_api_key
from src.models.ab_testing import ABTest
from src.models.drift_monitor import DriftMonitor

# Global instances
ab_test = ABTest("naive_bayes", "svm", split=0.5)
drift_monitor = DriftMonitor()

async def optional_auth(request: Request) -> Optional[str]:
    """
    Attempt to authenticate via Bearer token or X-API-Key header.
    Returns username or None (open access when no users registered).
    """
    auth_header = request.headers.get("Authorization", "")
    api_key = request.headers.get("X-API-Key", "")

    if auth_header.startswith("Bearer "):
        user = verify_token(auth_header[7:])
        if user:
            return user

    if api_key:
        user = verify_api_key(api_key)
        if user:
            return user

    return None
