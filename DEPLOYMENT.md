# Team Brain - Full Deployment Guide

This guide walks you through deploying Team Brain so it runs in production (not localhost). You'll deploy three services:

1. **Backend** (FastAPI) → Render
2. **MCP Server** (for Poke) → Render
3. **Frontend** (Next.js) → Vercel

---

## Prerequisites

- GitHub account (code is at https://github.com/bassiarmaan/treehacks2026)
- [Render](https://render.com) account (free tier)
- [Vercel](https://vercel.com) account (free tier)
- [Anthropic](https://console.anthropic.com) API key
- [Poke](https://poke.com) account (for testing)

---

## Part 1: Deploy Backend to Render

### Step 1.1: Create the Backend Service

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **New** → **Web Service**
3. Connect your GitHub account if not already connected
4. Select the repository: **bassiarmaan/treehacks2026**
5. Configure:
   - **Name**: `team-brain-api` (or any name)
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Step 1.2: Set Environment Variables

In the Render dashboard, go to your service → **Environment** → **Add Environment Variable**:

| Key | Value | Notes |
|-----|-------|-------|
| `ANTHROPIC_API_KEY` | `sk-ant-api03-...` | From console.anthropic.com |
| `ELASTICSEARCH_URL` | *(leave empty for now)* | Optional; app works without it (memory mode) |
| `ELASTICSEARCH_API_KEY` | *(leave empty for now)* | Optional |

### Step 1.3: Deploy

1. Click **Create Web Service**
2. Wait for the build to complete (2–5 minutes)
3. Copy your backend URL, e.g. `https://team-brain-api-xxxx.onrender.com`

### Step 1.4: Note the Backend URL

You'll need this for the MCP server and frontend. Example: `https://team-brain-api-xxxx.onrender.com`

**Important**: Render free tier spins down after 15 minutes of inactivity. The first request after idle may take 30–60 seconds to wake up.

---

## Part 2: Deploy MCP Server to Render

### Step 2.1: Create the MCP Service

1. In Render dashboard, click **New** → **Web Service**
2. Select the same repository: **bassiarmaan/treehacks2026**
3. Configure:
   - **Name**: `team-brain-mcp`
   - **Root Directory**: `mcp-server`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`

### Step 2.2: Set Environment Variables

| Key | Value |
|-----|-------|
| `CORTEX_API_URL` | `https://team-brain-api-xxxx.onrender.com` (your backend URL from Part 1) |
| `TEAM_APP_API_KEY` | *(optional)* For single-user demo; leave empty if each user will use their own API key |

### Step 2.3: Deploy

1. Click **Create Web Service**
2. Wait for the build to complete
3. Copy your MCP URL, e.g. `https://team-brain-mcp-xxxx.onrender.com`

### Step 2.4: MCP Endpoint for Poke

The MCP server uses **Streamable HTTP** transport. The endpoint Poke needs is:

```
https://team-brain-mcp-xxxx.onrender.com/mcp
```

**Note**: FastMCP may expose `/mcp` or `/sse`. If Poke fails to connect, try:
- `https://team-brain-mcp-xxxx.onrender.com/mcp`
- `https://team-brain-mcp-xxxx.onrender.com/sse`

---

## Part 3: Deploy Frontend to Vercel

### Step 3.1: Import the Project

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import the repository: **bassiarmaan/treehacks2026**
3. Configure:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `frontend` (click Edit and set this)
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `.next` (default)

### Step 3.2: Set Environment Variables

Before deploying, add:

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_API_URL` | `https://team-brain-api-xxxx.onrender.com` (your backend URL) |

**Important**: Use `NEXT_PUBLIC_` prefix so the variable is available in the browser.

### Step 3.3: Deploy

1. Click **Deploy**
2. Wait for the build (1–2 minutes)
3. Copy your frontend URL, e.g. `https://treehacks2026-xxxx.vercel.app`

---

## Part 4: Connect Poke to Your MCP Server

### Step 4.1: Add the Integration in Poke

1. Go to [poke.com/integrations/library](https://poke.com/integrations/library)
2. Click **Create Integration**
3. Fill in:
   - **MCP Server URL**: `https://team-brain-mcp-xxxx.onrender.com/mcp`
   - **API Key**: *(optional)* Leave empty if each user will add their own; or add a shared demo key
   - **Name**: `Team Brain`
4. Click **Create**

### Step 4.2: Verify Connection

1. Open Poke (SMS, iMessage, or WhatsApp)
2. Send: `Use the Team Brain integration to get my team status`
3. If it works, Poke will call your MCP and return team info

---

## Part 5: End-to-End Test

### 5.1: Web Flow

1. Open your Vercel URL: `https://your-app.vercel.app`
2. Go to **Team** tab
3. Register with your name → **Continue**
4. Copy your API key
5. **Create Team** → enter team name → **Create**
6. Copy the invite code
7. Open the app in an incognito window (or another browser)
8. Register as a second user → **Join Team** → enter invite code
9. Add your Poke API key (from poke.com/settings/advanced) in the Team dashboard

### 5.2: Poke Flow

1. Ensure both users have added the Team Brain MCP in Poke (poke.com/integrations/library)
2. User 1 texts Poke: `Find a 30-minute window when the whole team is free next week`
3. Poke relays to User 2's Poke; both report availability; you get free slots

---

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Vercel         │     │  Render          │     │  Render         │
│  (Frontend)     │────▶│  (Backend API)   │◀────│  (MCP Server)   │
│  Next.js        │     │  FastAPI         │     │  FastMCP        │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
        │                           │                      │
        │                           │                      │
        │                   SQLite (ephemeral              │
        │                   on Render free tier)           │
        │                                                   │
        │                                            Poke (SMS/iMessage)
        │                                            calls MCP tools
        └──────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Backend returns 503 or times out
- Render free tier spins down after 15 min idle. First request may take 30–60s.
- Check Render logs for errors.

### MCP connection fails in Poke
- Verify MCP URL ends with `/mcp` (or try `/sse`)
- Ensure the MCP service is running (check Render dashboard)
- Check Render logs for the MCP service

### CORS errors in frontend
- Backend has `allow_origins=["*"]`; should work. If not, add your Vercel domain to CORS.

### "Invalid API key" when using team features
- Ensure you're using the API key from the web dashboard (starts with `ctx_`)
- Pass it in Poke's integration config if using a shared key

### SQLite data resets on redeploy
- Render's free tier has ephemeral disk. Data resets on each deploy.
- For persistent data: use a hosted database (Supabase, Neon) or Render's paid persistent disk.

---

## Optional: Add a Custom Domain

### Backend (Render)
- Service → Settings → Custom Domain → add your domain

### Frontend (Vercel)
- Project → Settings → Domains → add your domain

### MCP (Render)
- Usually not needed; Poke uses the Render URL directly

---

## Summary Checklist

- [ ] Backend deployed on Render, URL copied
- [ ] MCP Server deployed on Render, URL copied
- [ ] Frontend deployed on Vercel with `NEXT_PUBLIC_API_URL` set
- [ ] Team Brain integration added in poke.com/integrations/library
- [ ] Tested: create team, join team, add Poke key
- [ ] Tested: text Poke to find availability (if team has Poke keys)
