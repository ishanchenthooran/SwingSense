from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import jwt
from jwt import PyJWKClient

from app.core.config import settings

# Algorithms Supabase issues JWKS-backed (asymmetric) tokens with. Deliberately
# excludes HS256/"none" — the algorithm is never taken from the token header,
# only from this fixed allow-list, to avoid algorithm-confusion attacks.
ALLOWED_ALGORITHMS = ["RS256", "ES256"]

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

# PyJWKClient caches fetched keys in-memory (cache_keys=True) and only re-fetches
# the JWKS endpoint when a kid isn't found in cache or the cache lifespan expires
# — built once per process, not per-request.
_jwk_client: Optional[PyJWKClient] = None


def _get_jwk_client() -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        if not settings.SUPABASE_JWKS_URL:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server misconfiguration: SUPABASE_JWKS_URL is not set",
            )
        _jwk_client = PyJWKClient(settings.SUPABASE_JWKS_URL, cache_keys=True)
    return _jwk_client


def _decode_verified(token: str) -> Dict[str, Any]:
    """Verify signature + expiry against Supabase's JWKS and return claims.
    Raises jwt exceptions / PyJWKClientError on any failure — callers must not
    fall back to an unverified decode."""
    signing_key = _get_jwk_client().get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=ALLOWED_ALGORITHMS,
        options={"verify_signature": True, "verify_exp": True},
    )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Parse JWT token from Authorization header, verify its signature against
    Supabase's JWKS, and extract user info.
    """
    try:
        decoded_token = _decode_verified(credentials.credentials)

        user_id = decoded_token.get("sub")
        email = decoded_token.get("email")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )

        return {
            "user_id": user_id,
            "email": email
        }

    except HTTPException:
        raise
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
) -> Optional[Dict[str, Any]]:
    """
    Like get_current_user but returns None instead of 401 when no token is provided
    or verification fails. Used for endpoints that are public but personalise when
    authenticated.
    """
    if not credentials:
        return None
    try:
        decoded = _decode_verified(credentials.credentials)
        user_id = decoded.get("sub")
        if not user_id:
            return None
        return {"user_id": user_id, "email": decoded.get("email")}
    except Exception:
        return None
