# Team Brain - Multiplayer Poke

> The shared brain for your team. Coordinate calendars, share knowledge, and get things done — all via Poke (SMS/iMessage) and the web.

Built at **TreeHacks 2026**.

## What is Team Brain?

Team Brain is **multiplayer Poke** — a shared AI assistant for teams. Think of it as the "shared brain" of your whole team:

- **"Find a 30-min window where the whole dev team is free next week"** — Poke handles the calendar tetris across everyone at once
- **"Remember: our brand colors are #FF6B35 and #004E89"** — Shared knowledge base the whole team can query
- **"Book the Tuesday slot for our weekly standup"** — Sends calendar add requests to each member's Poke
- **Shopping lists, tasks, ideas** — Dump anything, AI classifies and stores for the team (Visa commerce, shared life coordination)

Everything works through **Poke** (SMS/iMessage/WhatsApp) — no separate app. Plus a web dashboard for the team view.

## How It Works

1. **Dump** -- Type or text anything into the single input box
2. **Classify** -- Claude AI auto-classifies into: task, idea, shopping, note, meeting, reflection, contact, event
3. **Structure** -- Extracts fields like priority, due dates, budgets, attendees, mood, tags
4. **Store** -- Everything goes into Elasticsearch with JINA v3 embeddings for semantic search
5. **Chat** -- Multi-turn conversational agent queries your database, stores new entries, and triggers actions
6. **Shop** -- Stagehand-powered web automation searches for products and compares prices
7. **Text** -- Works via Poke (SMS/iMessage/WhatsApp) through our MCP integration

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **AI Brain** | Claude Agent SDK (Anthropic) | Classification, conversation, tool use |
| **Frontend** | Next.js + Tailwind CSS | Beautiful dark-mode UI |
| **Backend** | Python FastAPI | API server |
| **Database** | Elasticsearch + JINA v3 Embeddings | Semantic search, storage |
| **SMS/Chat** | Poke MCP Server (FastMCP) | iMessage/WhatsApp/SMS interface |
| **Shopping** | Stagehand (Browserbase) | Web automation, price comparison |
| **Infra** | Elastic Cloud, Vercel, Render | Production deployment |

## Deployment

For production deployment (Render + Vercel), see **[DEPLOYMENT.md](./DEPLOYMENT.md)** for step-by-step instructions.

---

## Quick Start (Local)

### 1. Backend

```bash
cd backend
cp .env.example .env   # Add your API keys
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

### 3. MCP Server (for Poke)

```bash
cd mcp-server
pip install -r requirements.txt
python server.py   # http://localhost:8001/mcp
```

Then connect at [poke.com/settings/connections](https://poke.com/settings/connections).

### 4. Shopping Agent (optional)

```bash
cd shopping-agent
npm install
npx ts-node src/index.ts   # http://localhost:8002
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/dump` | Classify and store any text |
| POST | `/query` | Semantic search across all entries |
| GET | `/entries` | List entries (filterable by category) |
| POST | `/chat` | Multi-turn conversation with tool use |
| POST | `/shop` | Trigger shopping automation |

## Sponsor Prize Alignment

| Sponsor | Prize | How We Hit It |
|---------|-------|---------------|
| **Poke / Interaction Co.** | Build with Poke, Most Useful, Most Technically Impressive | MCP server with 11 tools; Poke-native calendar relay (no Google OAuth); team coordination via SMS |
| **Decagon** | Best Conversation Assistant | Multi-turn conversational agent; natural dialogue; guides tasks; improves workflow |
| **Anthropic** | Human Flourishing, Claude Agent SDK | Reduces calendar anxiety; team coordination; tool-using agent with search/dump/shop/calendar |
| **Greylock** | Best Multi-Turn Agent | Agent reasons about feedback; chains tools (find availability -> book meeting); complex multi-step tasks |
| **Visa** | Future of Commerce | Shopping automation via Stagehand; shared team shopping lists; smarter commerce |
| **Browserbase** | Best Web Automation with Stagehand | Stagehand-powered product search and price comparison |
| **Elastic** | Best Agentic System on Elasticsearch | JINA v3 embeddings; semantic search; team knowledge base |
| **Graphite** | Most Likely to get Acquired | Real product: team calendar coordination + shared brain; moves metrics; developer productivity |

## Environment Variables

```
ANTHROPIC_API_KEY=         # Required - Claude API
ELASTICSEARCH_URL=         # Elastic Cloud URL
ELASTICSEARCH_API_KEY=     # Elastic Cloud API key
POKE_API_KEY=              # Poke API key
BROWSERBASE_API_KEY=       # Browserbase API key
BROWSERBASE_PROJECT_ID=    # Browserbase project ID
```
