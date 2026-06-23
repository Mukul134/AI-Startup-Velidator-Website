import logging
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.config import settings
from app.database import get_db_session
from app.models.entities import User

logger = logging.getLogger("uvicorn.error")
security = HTTPBearer()

# Cache for JWKS public keys
_jwks_cache = None

async def get_jwks_keys():
    """Fetches and caches the JWKS public keys from the Supabase Auth server."""
    global _jwks_cache
    if _jwks_cache is None:
        url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=5.0)
                response.raise_for_status()
                _jwks_cache = response.json()
                logger.info("Successfully fetched and cached Supabase JWKS keys.")
        except Exception as e:
            logger.error(f"Failed to fetch JWKS keys from Supabase: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service unreachable"
            )
    return _jwks_cache

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Decodes and validates the Supabase JWT token dynamically using JWKS public keys 
    to support asymmetric ES256/RS256 signatures, and returns the User profile object.
    """
    token = credentials.credentials
    try:
        # Extract headers to locate key ID (kid) and algorithm (alg)
        unverified_headers = jwt.get_unverified_header(token)
        kid = unverified_headers.get("kid")
        alg = unverified_headers.get("alg")
        
        if not kid or not alg:
            raise JWTError("Missing kid or alg in token headers")

        # Fetch active public keys
        jwks = await get_jwks_keys()
        
        # Locate the key that matches the token's kid
        target_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                target_key = key
                break
                
        if not target_key:
            # Force refresh cache once and try again in case keys rotated
            global _jwks_cache
            _jwks_cache = None
            jwks = await get_jwks_keys()
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    target_key = key
                    break
            
            if not target_key:
                raise JWTError("Matching public key not found in JWKS")
        
        # Decode and verify the token using the located public key
        payload = jwt.decode(
            token, 
            target_key, 
            algorithms=[alg], 
            audience="authenticated"
        )
        
        user_id_str: str = payload.get("sub")
        email: str = payload.get("email")
        
        if not user_id_str or not email:
            raise JWTError("Invalid sub or email in token payload")
            
        user_id = UUID(user_id_str)
        
    except JWTError as e:
        logger.error(f"JWT Validation Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate JWT: {str(e)}"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token"
        )

    # Lookup user in public.users table
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()
    
    # If trigger is delayed and user not found, create a fallback entry immediately
    if not user:
        user = User(
            id=user_id,
            email=email,
            full_name=payload.get("user_metadata", {}).get("full_name") or ""
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    return user
