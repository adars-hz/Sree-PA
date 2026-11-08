"""
Security and Access Authentication for Project SREE
"""

import hmac
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from ..core.config import settings

security = HTTPBearer(auto_error=False)

def verify_access_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security), request: Request = None) -> bool:
    """
    Validates token for remote LAN requests if AUTH_TOKEN is enforced.
    Localhost requests (127.0.0.1) are granted access seamlessly.
    """
    client_host = request.client.host if request and request.client else "127.0.0.1"
    
    # Allow local machine without auth friction
    if client_host in ("127.0.0.1", "localhost", "::1"):
        return True
        
    expected_token = settings.AUTH_TOKEN
    if not expected_token:
        return True

    # Check header token
    provided_token = credentials.credentials if credentials else request.headers.get("X-SREE-AUTH")
    if not provided_token:
        # Check query param as fallback for quick mobile pairing
        provided_token = request.query_params.get("token")

    if not provided_token or not hmac.compare_digest(provided_token, expected_token):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Valid authentication token required for remote device access."
        )
    return True

