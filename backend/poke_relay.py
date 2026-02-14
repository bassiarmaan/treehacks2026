"""
Poke API Relay Service.
Sends messages to team members' Pokes to trigger calendar sync,
then polls for availability reports.
"""

import asyncio

import httpx

from models import (
    get_team_members,
    get_availability,
    get_team_availability,
    create_sync_token,
)
from calendar_logic import find_free_slots

POKE_API_URL = "https://poke.com/api/v1/inbound-sms/webhook"


async def send_poke_message(poke_api_key: str, message: str) -> dict:
    """
    Send a message to a user's Poke via the inbound SMS webhook.
    This sends the message AS the user to their Poke assistant.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            POKE_API_URL,
            headers={
                "Authorization": f"Bearer {poke_api_key}",
                "Content-Type": "application/json",
            },
            json={"message": message},
        )
        resp.raise_for_status()
        return resp.json()


async def request_calendar_sync(
    poke_api_key: str,
    user_id: str,
    team_id: str,
    start_date: str,
    end_date: str,
    integration_name: str = "Team Brain",
) -> bool:
    """
    Ask a team member's Poke to check their calendar and report
    availability via our MCP sync_my_calendar tool.
    Uses a one-time sync token for secure user identification.
    """
    token = create_sync_token(user_id, team_id, start_date, end_date)
    message = (
        f"Check my calendar from {start_date} to {end_date} "
        f'and use the "{integration_name}" integration\'s sync_my_calendar tool '
        f"with sync_token={token}, start_date={start_date}, end_date={end_date} "
        f"to share my busy times with the team."
    )
    try:
        await send_poke_message(poke_api_key, message)
        return True
    except Exception as e:
        print(f"Failed to relay Poke message: {e}")
        return False


async def request_team_availability(
    team_id: str,
    start_date: str,
    end_date: str,
    requesting_user_id: str,
    duration_minutes: int = 30,
    timeout: float = 45.0,
) -> dict:
    """
    Orchestrate the full team availability flow:
    1. Send Poke relay messages to all other team members
    2. Poll for availability reports
    3. Compute free slots
    """
    members = get_team_members(team_id)
    if not members:
        return {"success": False, "message": "No team members found.", "slots": []}

    member_ids = [m["id"] for m in members]
    member_names = {m["id"]: m["name"] for m in members}

    # Step 1: Send relay messages to all members (except requester)
    relay_tasks = []
    for member in members:
        if member["id"] == requesting_user_id:
            continue  # Requesting user's Poke is already handling this
        poke_key = member.get("poke_api_key", "")
        if not poke_key:
            print(f"Member {member['name']} has no Poke API key, skipping relay")
            continue
        relay_tasks.append(
            request_calendar_sync(poke_key, member["id"], team_id, start_date, end_date)
        )

    if relay_tasks:
        await asyncio.gather(*relay_tasks, return_exceptions=True)

    # Step 2: Poll for availability (wait for sync_my_calendar callbacks)
    poll_interval = 2.0
    elapsed = 0.0

    while elapsed < timeout:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

        # Check how many members have reported
        team_avail = get_team_availability(team_id, start_date, end_date)
        reported_count = len(team_avail)

        if reported_count >= len(member_ids):
            break  # All members reported

        # Exponential backoff (cap at 5s)
        poll_interval = min(poll_interval * 1.3, 5.0)

    # Step 3: Compute free slots with whatever data we have
    team_avail = get_team_availability(team_id, start_date, end_date)
    reported_names = [
        member_names.get(uid, "Unknown") for uid in team_avail.keys()
    ]
    missing_names = [
        member_names[uid]
        for uid in member_ids
        if uid not in team_avail
    ]

    all_busy = list(team_avail.values())

    if not all_busy:
        return {
            "success": False,
            "message": f"No availability data received yet. Missing: {', '.join(missing_names)}",
            "slots": [],
            "reported": reported_names,
            "missing": missing_names,
        }

    slots = find_free_slots(all_busy, duration_minutes, start_date, end_date)

    if not slots:
        msg = f"No {duration_minutes}-minute windows found where everyone is free between {start_date} and {end_date}."
    else:
        slot_strs = []
        for s in slots[:6]:  # Show top 6
            slot_strs.append(f"  - {s['start']} to {s['end']}")
        msg = f"Found {len(slots)} open windows:\n" + "\n".join(slot_strs)

    if missing_names:
        msg += f"\n\n(Still waiting on: {', '.join(missing_names)})"

    return {
        "success": True,
        "message": msg,
        "slots": slots,
        "reported": reported_names,
        "missing": missing_names,
    }


async def send_booking_to_team(
    team_id: str,
    title: str,
    start_time: str,
    duration_minutes: int,
    booked_by: str,
) -> dict:
    """
    Send a calendar booking message to all team members' Pokes.
    Each member's Poke will create the calendar event via its native integration.
    """
    members = get_team_members(team_id)
    booked_by_name = next((m["name"] for m in members if m["id"] == booked_by), "Someone")

    message = (
        f"Schedule a meeting called '{title}' starting at {start_time} "
        f"for {duration_minutes} minutes. This was booked by {booked_by_name} for the team."
    )

    results = []
    for member in members:
        poke_key = member.get("poke_api_key", "")
        if not poke_key:
            results.append({"name": member["name"], "sent": False, "reason": "No Poke API key"})
            continue
        try:
            await send_poke_message(poke_key, message)
            results.append({"name": member["name"], "sent": True})
        except Exception as e:
            results.append({"name": member["name"], "sent": False, "reason": str(e)})

    sent_count = sum(1 for r in results if r["sent"])
    return {
        "success": sent_count > 0,
        "message": f"Meeting '{title}' booking sent to {sent_count}/{len(members)} team members.",
        "details": results,
    }
