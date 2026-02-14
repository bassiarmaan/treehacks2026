"""
Multiplayer Poke MCP Server - Team Brain.
Exposes tools for team calendar coordination, shared brain, and more.
Each user connects Poke with their API key (from team dashboard).
"""

import os
import json
import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

CORTEX_API = os.getenv("CORTEX_API_URL", "http://localhost:8000")
# For demo: single API key. In production, Poke would pass per-connection API key.
DEFAULT_API_KEY = os.getenv("TEAM_APP_API_KEY", "")

mcp = FastMCP(
    name="Team Brain",
    instructions="""You are the Team Brain - a multiplayer AI assistant for teams using Poke.
    You help coordinate calendars, manage shared knowledge, and improve team workflows.
    When users ask to find meeting times, use find_team_availability.
    When they want to share info with the team, use dump_to_team.
    When they ask about team knowledge, use ask_team_brain.
    Be conversational, helpful, and proactive. Guide users through tasks.""",
)


def _headers(api_key: str | None = None):
    key = api_key or DEFAULT_API_KEY
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}"}


async def _call(method: str, path: str, data: dict | None = None, api_key: str | None = None) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        url = f"{CORTEX_API}{path}"
        headers = _headers(api_key)
        if method == "GET":
            resp = await client.get(url, params=data, headers=headers)
        else:
            resp = await client.post(url, json=data, headers=headers)
        resp.raise_for_status()
        return resp.json()


# ── Team Calendar Tools ───────────────────────────────────────────────────────

@mcp.tool
async def find_team_availability(
    duration_minutes: int = 30,
    start_date: str = "",
    end_date: str = "",
    api_key: str = "",
) -> str:
    """
    Find a time window when the whole team is free.
    Triggers calendar sync across all team members via Poke, then computes free slots.

    Args:
        duration_minutes: Meeting duration (default 30).
        start_date: Start of range (YYYY-MM-DD). Default: next Monday.
        end_date: End of range (YYYY-MM-DD). Default: next Friday.
        api_key: Your API key from the team dashboard (optional if configured).
    """
    from datetime import datetime, timedelta

    if not start_date or not end_date:
        today = datetime.now().date()
        # Next Monday
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        start_d = today + timedelta(days=days_until_monday)
        end_d = start_d + timedelta(days=4)  # Mon-Fri
        start_date = start_d.isoformat()
        end_date = end_d.isoformat()

    key = api_key or DEFAULT_API_KEY
    if not key:
        return "Please configure your API key. Get it from the team dashboard and add it to your Poke connection."

    try:
        # Get user's team
        teams = await _call("GET", "/teams/me", api_key=key)
        team_list = teams.get("teams", [])
        if not team_list:
            return "You're not in a team yet. Create or join a team at the web dashboard first."
        team_id = team_list[0]["id"]

        result = await _call(
            "POST",
            f"/teams/{team_id}/availability/find",
            {
                "duration_minutes": duration_minutes,
                "start_date": start_date,
                "end_date": end_date,
            },
            api_key=key,
        )
        return result.get("message", json.dumps(result))
    except httpx.HTTPStatusError as e:
        return f"Could not find availability: {e.response.text}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool
async def sync_my_calendar(
    sync_token: str,
    start_date: str,
    end_date: str,
    busy_times: list[dict],
) -> str:
    """
    Report your calendar busy times to the team. Called by Poke after checking your calendar.
    Do not call this directly - it's used when the team requests availability.

    Args:
        sync_token: One-time token from the relay message.
        start_date: Date range start (YYYY-MM-DD).
        end_date: Date range end (YYYY-MM-DD).
        busy_times: List of {"start": "ISO", "end": "ISO"} intervals when you're busy.
    """
    try:
        result = await _call(
            "POST",
            "/teams/availability/sync",
            {
                "sync_token": sync_token,
                "start_date": start_date,
                "end_date": end_date,
                "busy_times": busy_times,
            },
        )
        return result.get("message", "Synced!")
    except Exception as e:
        return f"Sync failed: {str(e)}"


@mcp.tool
async def book_team_meeting(
    title: str,
    start_time: str,
    duration_minutes: int = 30,
    api_key: str = "",
) -> str:
    """
    Book a meeting for the whole team. Sends calendar add requests to each member's Poke.

    Args:
        title: Meeting title.
        start_time: Start time (e.g. "2026-02-18 14:00" or "Tuesday 2pm").
        duration_minutes: Duration (default 30).
        api_key: Your API key (optional if configured).
    """
    key = api_key or DEFAULT_API_KEY
    if not key:
        return "Please configure your API key in the team dashboard."

    try:
        teams = await _call("GET", "/teams/me", api_key=key)
        team_list = teams.get("teams", [])
        if not team_list:
            return "Join a team first."
        team_id = team_list[0]["id"]

        result = await _call(
            "POST",
            f"/teams/{team_id}/book",
            {
                "title": title,
                "start_time": start_time,
                "duration_minutes": duration_minutes,
            },
            api_key=key,
        )
        return result.get("message", json.dumps(result))
    except Exception as e:
        return f"Booking failed: {str(e)}"


# ── Shared Team Brain ─────────────────────────────────────────────────────────

@mcp.tool
async def dump_to_team(text: str, api_key: str = "") -> str:
    """
    Share something with your team's shared brain. Classifies and stores for everyone.

    Args:
        text: What to share - a task, idea, note, meeting summary, etc.
        api_key: Your API key (optional if configured).
    """
    try:
        result = await _call("POST", "/dump", {"text": text}, api_key=api_key or DEFAULT_API_KEY)
        entry = result.get("entry", {})
        return f"Shared with team as **{entry.get('category', 'note')}**: {entry.get('summary', 'Saved')}"
    except Exception as e:
        return f"Could not share: {str(e)}"


@mcp.tool
async def ask_team_brain(question: str, api_key: str = "") -> str:
    """
    Search your team's shared knowledge base. Find tasks, ideas, notes, meeting info.

    Args:
        question: What you want to find.
        api_key: Your API key (optional if configured).
    """
    try:
        result = await _call("POST", "/query", {"query": question, "limit": 5}, api_key=api_key or DEFAULT_API_KEY)
        results = result.get("results", [])
        if not results:
            return "Nothing found in the team brain. Try dumping some info first!"
        parts = [f"Found {len(results)} relevant entries:\n"]
        for i, r in enumerate(results, 1):
            parts.append(f"{i}. [{r.get('category', '?')}] {r.get('summary', r.get('title', '?'))}")
        return "\n".join(parts)
    except Exception as e:
        return f"Search failed: {str(e)}"


@mcp.tool
async def get_team_status(api_key: str = "") -> str:
    """
    Get an overview of your team - members, recent activity, tasks.
    """
    key = api_key or DEFAULT_API_KEY
    if not key:
        return "Configure your API key first."
    try:
        teams = await _call("GET", "/teams/me", api_key=key)
        team_list = teams.get("teams", [])
        if not team_list:
            return "You're not in a team. Create or join one at the dashboard."
        team_id = team_list[0]["id"]
        team_data = await _call("GET", f"/teams/{team_id}/members", api_key=key)
        members = team_data.get("members", [])
        entries = await _call("GET", "/entries", {"limit": 10}, api_key=key)
        ent_list = entries.get("entries", [])

        parts = [f"Team: {team_list[0]['name']}\n", f"Members ({len(members)}):"]
        for m in members:
            status = "Poke connected" if m.get("poke_connected") else "No Poke"
            parts.append(f"  - {m['name']} ({status})")
        if ent_list:
            parts.append("\nRecent entries:")
            for e in ent_list[:5]:
                parts.append(f"  - [{e.get('category')}] {e.get('summary', e.get('title', '?'))[:50]}")
        return "\n".join(parts)
    except Exception as e:
        return f"Error: {str(e)}"


# ── Legacy personal tools (still work for solo use) ─────────────────────────────

@mcp.tool
async def dump_thought(text: str) -> str:
    """Dump a thought to your personal brain. Classifies and stores."""
    try:
        result = await _call("POST", "/dump", {"text": text})
        entry = result.get("entry", {})
        return f"Got it! **{entry.get('category')}**: {entry.get('summary', 'Saved')}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool
async def query_brain(question: str) -> str:
    """Search your personal database."""
    try:
        result = await _call("POST", "/query", {"query": question, "limit": 5})
        results = result.get("results", [])
        if not results:
            return "Nothing found."
        return "\n".join([f"{i}. [{r.get('category')}] {r.get('summary', '?')}" for i, r in enumerate(results, 1)])
    except Exception as e:
        return f"Search failed: {str(e)}"


@mcp.tool
async def get_tasks() -> str:
    """Get your tasks."""
    try:
        result = await _call("GET", "/entries", {"category": "task", "limit": 20})
        entries = result.get("entries", [])
        if not entries:
            return "No tasks."
        return "\n".join([f"{i}. {e.get('title', e.get('summary', '?'))}" for i, e in enumerate(entries, 1)])
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool
async def get_shopping_list() -> str:
    """Get your shopping list."""
    try:
        result = await _call("GET", "/entries", {"category": "shopping", "limit": 20})
        entries = result.get("entries", [])
        if not entries:
            return "No shopping items."
        return "\n".join([f"{i}. {e.get('product', e.get('summary', '?'))}" for i, e in enumerate(entries, 1)])
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool
async def shop(product_query: str) -> str:
    """Search for products (Visa commerce prize - Stagehand automation)."""
    try:
        await _call("POST", "/dump", {"text": f"I want to buy: {product_query}"})
        result = await _call("POST", "/shop", {"query": product_query})
        return result.get("comparison", json.dumps(result))
    except Exception as e:
        return f"Shopping note saved. Automation: {str(e)}"


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
        stateless_http=True,
    )
