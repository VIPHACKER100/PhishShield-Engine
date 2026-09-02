"""
Auth Router — registration, login, and password-reset endpoints.

Rate limits (per IP address, enforced by SlowAPI):
  POST /auth/register              → 3 requests / minute
  POST /auth/login                 → 5 requests / minute
  POST /auth/password-reset-request → 3 requests / minute
  POST /auth/password-reset        → 5 requests / minute
"""

from fastapi import APIRouter, HTTPException, Request
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
)

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
