"""
Team management and calendar routes for Multiplayer Poke.
"""

import asyncio
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import AuthContext, resolve_auth
from models import (
    create_user,
    create_team,
    join_team,
    get_team_by_id,
    get_team_by_invite_code,
    get_team_members,
    get_user_teams,
    store_availability,
    get_team_availability,
    consume_sync_token,
)
from poke_relay import request_team_availability, send_booking_to_team

router = APIRouter(prefix="/teams", tags=["teams"])


# ── Request/Response Models ───────────────────────────────────────────────────

class CreateUserRequest(BaseModel):
    name: str
    email: str = ""


class CreateTeamRequest(BaseModel):
    name: str


class JoinTeamRequest(BaseModel):
    invite_code: str


class UpdatePokeKeyRequest(BaseModel):
    poke_api_key: str


class FindAvailabilityRequest(BaseModel):
    duration_minutes: int = 30
    start_date: str
    end_date: str


class BookMeetingRequest(BaseModel):
    title: str
    start_time: str
    duration_minutes: int = 30


class SyncCalendarRequest(BaseModel):
    sync_token: str
    start_date: str
    end_date: str
    busy_times: list[dict]


# ── Public routes (no auth) ───────────────────────────────────────────────────

@router.post("/users")
async def register_user(req: CreateUserRequest):
    """Create a new user and get an API key for Poke MCP connection."""
    user = create_user(name=req.name, email=req.email)
    return {
        "user_id": user["id"],
        "name": user["name"],
        "api_key": user["api_key"],
        "message": "Add this API key to Poke at poke.com/settings/connections",
    }


@router.post("/join")
async def join_team_route(req: JoinTeamRequest):
    """Join a team by invite code. Requires user_id and api_key in headers for auth."""
    team = get_team_by_invite_code(req.invite_code)
    if not team:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    # Note: We need auth to know which user is joining. Caller must pass Authorization.
    return {"team_id": team["id"], "team_name": team["name"], "invite_code": team["invite_code"]}


# ── Auth-required routes ──────────────────────────────────────────────────────

@router.post("")
async def create_team_route(req: CreateTeamRequest, auth: AuthContext = Depends(resolve_auth)):
    """Create a new team. Requires Authorization: Bearer <api_key>."""
    team = create_team(name=req.name, created_by=auth.user_id)
    return {
        "team_id": team["id"],
        "name": team["name"],
        "invite_code": team["invite_code"],
        "message": f"Share invite code {team['invite_code']} with your team",
    }


@router.post("/join-with-auth")
async def join_team_with_auth(req: JoinTeamRequest, auth: AuthContext = Depends(resolve_auth)):
    """Join a team by invite code (authenticated)."""
    team = get_team_by_invite_code(req.invite_code)
    if not team:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    success = join_team(team["id"], auth.user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Already a member or join failed")
    return {
        "team_id": team["id"],
        "team_name": team["name"],
        "message": f"Joined {team['name']}",
    }


@router.get("/me")
async def get_my_teams(auth: AuthContext = Depends(resolve_auth)):
    """Get all teams the user belongs to."""
    teams = get_user_teams(auth.user_id)
    return {"teams": teams}


@router.get("/{team_id}")
async def get_team(team_id: str, auth: AuthContext = Depends(resolve_auth)):
    """Get team details. User must be a member."""
    team = get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    members = get_team_members(team_id)
    member_ids = [m["id"] for m in members]
    if auth.user_id not in member_ids:
        raise HTTPException(status_code=403, detail="Not a member of this team")
    return {"team": team, "members": members}


@router.get("/{team_id}/members")
async def list_members(team_id: str, auth: AuthContext = Depends(resolve_auth)):
    """List team members with sync status."""
    team = get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    members = get_team_members(team_id)
    member_ids = [m["id"] for m in members]
    if auth.user_id not in member_ids:
        raise HTTPException(status_code=403, detail="Not a member of this team")
    # Add sync status (has Poke key = can sync)
    for m in members:
        m["poke_connected"] = bool(m.get("poke_api_key"))
        del m["poke_api_key"]  # Don't expose keys
        del m["api_key"]
    return {"members": members}


@router.put("/{team_id}/members/me/poke-key")
async def update_my_poke_key(
    team_id: str,
    req: UpdatePokeKeyRequest,
    auth: AuthContext = Depends(resolve_auth),
):
    """Update the current user's Poke API key for relay messages."""
    from models import update_user_poke_key

    team = get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    members = get_team_members(team_id)
    if auth.user_id not in [m["id"] for m in members]:
        raise HTTPException(status_code=403, detail="Not a member of this team")
    update_user_poke_key(auth.user_id, req.poke_api_key)
    return {"message": "Poke API key updated. You can now receive calendar sync requests."}


@router.post("/{team_id}/availability/find")
async def find_availability(
    team_id: str,
    req: FindAvailabilityRequest,
    auth: AuthContext = Depends(resolve_auth),
):
    """
    Find free slots for the whole team.
    Triggers Poke relay to all members, polls for reports, computes free slots.
    """
    team = get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    members = get_team_members(team_id)
    if auth.user_id not in [m["id"] for m in members]:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    result = await request_team_availability(
        team_id=team_id,
        start_date=req.start_date,
        end_date=req.end_date,
        requesting_user_id=auth.user_id,
        duration_minutes=req.duration_minutes,
    )
    return result


@router.post("/{team_id}/book")
async def book_meeting(
    team_id: str,
    req: BookMeetingRequest,
    auth: AuthContext = Depends(resolve_auth),
):
    """Book a meeting by sending calendar add requests to all team members' Pokes."""
    team = get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    members = get_team_members(team_id)
    if auth.user_id not in [m["id"] for m in members]:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    result = await send_booking_to_team(
        team_id=team_id,
        title=req.title,
        start_time=req.start_time,
        duration_minutes=req.duration_minutes,
        booked_by=auth.user_id,
    )
    return result


# ── Availability sync (called by MCP when Poke reports calendar) ────────────────

@router.post("/availability/sync")
async def sync_calendar(req: SyncCalendarRequest):
    """
    Called by the MCP server when a user's Poke invokes sync_my_calendar.
    Uses a one-time sync_token (from the relay message) to identify the user.
    No auth required - the token is the auth.
    """
    token_data = consume_sync_token(req.sync_token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid or expired sync token")
    user_id = token_data["user_id"]
    store_availability(user_id, req.start_date, req.end_date, req.busy_times)
    return {"message": "Availability synced", "user_id": user_id}
