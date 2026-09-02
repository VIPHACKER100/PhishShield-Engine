"""
Auth Router — registration, login, and password-reset endpoints.

Rate limits (per IP address, enforced by SlowAPI):
  POST /auth/register              → 3 requests / minute
  POST /auth/login                 → 5 requests / minute
  POST /auth/password-reset-request → 3 requests / minute
  POST /auth/password-reset        → 5 requests / minute
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.api.schemas import (
    RegisterRequest,
    LoginRequest,
    PasswordResetRequestSchema,
    PasswordResetSchema,
)
from src.api.auth import (
    register_user,
    authenticate_user,
    request_password_reset,
    reset_password,
    get_user_logs,
    get_user_log_by_id,
    get_user_feedback_by_id,
    delete_user_feedback,
)
from src.api.dependencies import get_current_user
from src.core.database import User

router = APIRouter(prefix="/auth", tags=["auth"])
_limiter = Limiter(key_func=get_remote_address)


@router.post("/register")
@_limiter.limit("3/minute")
async def register(request: Request, body: RegisterRequest):
    """
    Create a new user account.

    The api_key in the response is a one-time secret — store it securely.
    It will not be shown again.
    """
    try:
        result = register_user(body.username, body.password, body.email)
        return result
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/login")
@_limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest):
    """
    Authenticate and receive a short-lived JWT bearer token.

    Returns 401 for any failure (wrong credentials, locked account) without
    revealing which condition triggered it.
    """
    result = authenticate_user(body.username, body.password)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return result


@router.post("/password-reset-request")
@_limiter.limit("3/minute")
async def password_reset_request(request: Request, body: PasswordResetRequestSchema):
    """
    Request a password reset token.

    Always returns HTTP 200 with a generic message regardless of whether the
    username exists — prevents user enumeration via this endpoint.

    In a production deployment the raw token should be emailed to the registered
    address. Here it is returned in the response body for development/testing.
    """
    raw_token = request_password_reset(body.username)
    # Return a uniform response body to prevent user enumeration.
    # In production: send raw_token via email and do NOT include it in the response.
    return {
        "detail": "If that username exists, a password-reset token has been issued.",
        # DEV ONLY — remove the line below before deploying to production:
        "_dev_token": raw_token,
    }


@router.post("/password-reset")
@_limiter.limit("5/minute")
async def password_reset(request: Request, body: PasswordResetSchema):
    """
    Consume a one-time password reset token and set a new password.

    The token is valid for a limited time (default 1 hour) and is invalidated
    after first use.
    """
    try:
        ok = reset_password(body.username, body.token, body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")
    return {"detail": "Password updated successfully."}


# ---------------------------------------------------------------------------
# User Profile & Owned Resource Access (IDOR Protected)
# ---------------------------------------------------------------------------


@router.get("/me")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile information."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_email_verified": current_user.is_email_verified,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }


@router.get("/logs")
async def get_my_logs(current_user: User = Depends(get_current_user)):
    """Retrieve usage logs owned strictly by the authenticated user."""
    return get_user_logs(current_user.id)


@router.get("/logs/{log_id}")
async def get_my_log_by_id(log_id: int, current_user: User = Depends(get_current_user)):
    """
    Retrieve a specific usage log by log_id.
    Prevents IDOR by verifying ownership: log.user_id == current_user.id.
    """
    log = get_user_log_by_id(log_id, current_user.id)
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found or access denied")
    return log


@router.get("/feedback/{feedback_id}")
async def get_my_feedback_by_id(feedback_id: int, current_user: User = Depends(get_current_user)):
    """
    Retrieve a specific feedback entry by feedback_id.
    Prevents IDOR by verifying ownership: feedback.user_id == current_user.id.
    """
    fb = get_user_feedback_by_id(feedback_id, current_user.id)
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback entry not found or access denied")
    return fb


@router.delete("/feedback/{feedback_id}")
async def delete_my_feedback(feedback_id: int, current_user: User = Depends(get_current_user)):
    """
    Delete a specific feedback entry by feedback_id.
    Prevents IDOR by verifying ownership: feedback.user_id == current_user.id.
    """
    deleted = delete_user_feedback(feedback_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Feedback entry not found or access denied")
    return {"detail": "Feedback entry deleted successfully."}
