"""
Security and Access Authentication for Project SREE
"""

import hmac
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
from ..core.config import settings
from ..core.logger import logger

security = HTTPBearer(auto_error=False)

class SREEAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce authentication for remote LAN requests.
    Localhost requests are bypassed for ease of development and local usage.
    """
    async def dispatch(self, request: Request, call_next):
        client_host = request.client.host if request.client else "127.0.0.1"

        # 1. Allow local machine without auth friction
        if client_host in ("127.0.0.1", "localhost", "::1"):
            return await call_next(request)

        # 2. Check if LAN access is globally disabled
        if not settings.ALLOW_LAN_ACCESS:
            logger.warning(f"Blocked remote access attempt from {client_host}")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=403,
                content={"detail": "Remote access to SREE is disabled in configuration."}
            )

        # 3. Verify Token
        expected_token = settings.AUTH_TOKEN
        provided_token = (
            request.headers.get("Authorization").replace("Bearer ", "")
            if request.headers.get("Authorization")
            else request.headers.get("X-SREE-AUTH")
            or request.query_params.get("token")
        )

        if not provided_token or not hmac.compare_digest(provided_token, expected_token):
            logger.warning(f"Unauthorized access attempt from {client_host} - Invalid Token")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized: Valid authentication token required for remote device access."}
            )

        return await call_next(request)

def verify_access_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security), request: Request = None) -> bool:
    """
    Legacy helper for specific endpoint protection.
    Most access is now handled by SREEAuthMiddleware.
    """
    client_host = request.client.host if request and request.client else "127.0.0.1"
    if client_host in ("127.0.0.1", "localhost", "::1"):
        return True

    expected_token = settings.AUTH_TOKEN
    provided_token = credentials.credentials if credentials else request.headers.get("X-SREE-AUTH")
    if not provided_token or not hmac.compare_digest(provided_token, expected_token):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Valid authentication token required for remote device access."
        )
    return True
