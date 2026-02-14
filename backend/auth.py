"""
Lightweight auth for Cortex.
Resolves API key from request headers to user_id + team_id.
Used by both the FastAPI backend and MCP server.
"""

from fastapi import Header, HTTPException

from models import get_user_by_api_key, get_user_team_id


class AuthContext:
    """Holds the resolved user and team for a request."""

    def __init__(self, user_id: str, team_id: str | None, user: dict):
        self.user_id = user_id
        self.team_id = team_id
        self.user = user


async def resolve_auth(authorization: str = Header(default="")) -> AuthContext:
    """
    FastAPI dependency that extracts the API key from Authorization header
    and resolves the user + team. Returns AuthContext.
    Non-authenticated requests get a None context (for public endpoints).
    """
    api_key = ""
    if authorization.startswith("Bearer "):
        api_key = authorization[7:]
    elif authorization.startswith("ctx_"):
        api_key = authorization

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key. Set Authorization: Bearer <api_key>")

    user = get_user_by_api_key(api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    team_id = get_user_team_id(user["id"])
    return AuthContext(user_id=user["id"], team_id=team_id, user=user)


async def optional_auth(authorization: str = Header(default="")) -> AuthContext | None:
    """Same as resolve_auth but returns None instead of raising on missing key."""
    api_key = ""
    if authorization.startswith("Bearer "):
        api_key = authorization[7:]
    elif authorization.startswith("ctx_"):
        api_key = authorization

    if not api_key:
        return None

    user = get_user_by_api_key(api_key)
    if not user:
        return None

    team_id = get_user_team_id(user["id"])
    return AuthContext(user_id=user["id"], team_id=team_id, user=user)
