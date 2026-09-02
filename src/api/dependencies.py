from fastapi import Request, HTTPException, Depends
from typing import Optional
from src.api.auth import verify_token, verify_api_key, get_user_by_username
from src.core.database import User
from src.models.ab_testing import ABTest
from src.models.drift_monitor import DriftMonitor

# Global instances
ab_test = ABTest("naive_bayes", "svm", split=0.5)
drift_monitor = DriftMonitor()

async def optional_auth(request: Request) -> Optional[User]:
    """
    Attempt to authenticate via Bearer token or X-API-Key header.
    Returns User DB instance or None.
    """
    auth_header = request.headers.get("Authorization", "")
    api_key = request.headers.get("X-API-Key", "")

    username = None
    if auth_header.startswith("Bearer "):
        username = verify_token(auth_header[7:])
    elif api_key:
        username = verify_api_key(api_key)

    if username:
        user = get_user_by_username(username)
        if user:
            return user

    return None

async def get_current_user(request: Request, user: Optional[User] = Depends(optional_auth)) -> User:
    """
    Require authentication via Bearer token or X-API-Key header.
    Raises HTTPException(401) if unauthenticated or user invalid.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
