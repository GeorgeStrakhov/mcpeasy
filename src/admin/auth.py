"""
Admin authentication utilities
"""
from typing import Optional
from fastapi import HTTPException, Request, status

from src.database import DatabaseService


def verify_admin_session(request: Request) -> bool:
    """Check if user is authenticated as admin"""
    return request.session.get("admin_authenticated", False)


def get_current_admin_username(request: Request) -> Optional[str]:
    """Get currently authenticated admin username from session"""
    if verify_admin_session(request):
        return request.session.get("admin_username")
    return None


def require_admin_auth(request: Request):
    """Dependency to require admin authentication"""
    if not verify_admin_session(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required"
        )


async def authenticate_admin(request: Request, username: str, password: str, db: DatabaseService) -> bool:
    """Authenticate admin user and set session"""
    admin = await db.verify_admin_password(username, password)
    
    if admin:
        request.session["admin_authenticated"] = True
        request.session["admin_username"] = admin.username
        request.session["admin_id"] = admin.id
        return True
    
    return False


def logout_admin(request: Request):
    """Clear admin session"""
    request.session.pop("admin_authenticated", None)
    request.session.pop("admin_username", None)
    request.session.pop("admin_id", None)