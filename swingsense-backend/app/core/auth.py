from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import jwt

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Parse JWT token from Authorization header and extract user info.
    For MVP: decode unverified and extract sub (user_id) and email.
    TODO: Add JWKS verification for production security.
    """
    try:
        token = credentials.credentials
        
        # For MVP: decode without verification
        # TODO: Implement JWKS verification for production
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        
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
        
    except jwt.InvalidTokenError:
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
    Like get_current_user but returns None instead of 401 when no token is provided.
    Used for endpoints that are public but personalise when authenticated.
    """
    if not credentials:
        return None
    try:
        decoded = jwt.decode(credentials.credentials, options={"verify_signature": False})
        user_id = decoded.get("sub")
        if not user_id:
            return None
        return {"user_id": user_id, "email": decoded.get("email")}
    except Exception:
        return None
