from fastapi import Header, HTTPException
from typing import Optional
from app.core.config import ADMIN_SECRET_KEY

async def verify_admin_token(x_admin_token: Optional[str] = Header(None)):
    if not x_admin_token:
        raise HTTPException(status_code=401, detail="Missing admin token")
    if x_admin_token != ADMIN_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return x_admin_token
