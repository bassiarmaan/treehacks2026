"""
Cortex Backend - FastAPI server
The brain behind the universal AI inbox.
"""

import os
import json
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

from agent.classifier import CortexClassifier
from agent.conversation import ConversationEngine
from models import init_db as init_sqlite
from routes.teams import router as teams_router
from storage.elasticsearch import CortexStorage

# ── Global instances ──────────────────────────────────────────────────────────

classifier: CortexClassifier | None = None
conversation_engine: ConversationEngine | None = None
storage: CortexStorage | None = None

# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global classifier, conversation_engine, storage

    # Initialize SQLite for teams, users, availability
    init_sqlite()

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("WARNING: ANTHROPIC_API_KEY not set. Classification will fail.")

    classifier = CortexClassifier(api_key=api_key)

    es_url = os.getenv("ELASTICSEARCH_URL", "")
    es_api_key = os.getenv("ELASTICSEARCH_API_KEY", "")

    if es_url and es_url.startswith("http"):
        storage = CortexStorage(es_url=es_url, es_api_key=es_api_key)
        try:
            storage.initialize_indices()
            print("Elasticsearch indices initialized.")
        except Exception as e:
            print(f"WARNING: Could not connect to Elasticsearch: {e}")
            print("Running in memory-only mode.")
            storage = None
    else:
        print("WARNING: ELASTICSEARCH_URL not set. Running in memory-only mode.")
        storage = None

    # Initialize conversation engine with tool access
    conversation_engine = ConversationEngine(
        api_key=api_key,
        classifier=classifier,
        storage=storage,
        memory_store=memory_store,
    )
    print("Conversation engine initialized.")

    yield

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Cortex API",
    description="Universal AI Inbox - dump anything, get structure back",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount team routes (multiplayer Poke)
app.include_router(teams_router)

# ── In-memory fallback store ─────────────────────────────────────────────────

memory_store: list[dict] = []

# ── Request/Response Models ───────────────────────────────────────────────────

class DumpRequest(BaseModel):
    text: str

class DumpResponse(BaseModel):
    success: bool
    entry: dict
    storage: dict | None = None

class QueryRequest(BaseModel):
    query: str
    categories: list[str] | None = None
    limit: int = 10

class ChatRequest(BaseModel):
    messages: list[dict]

class ChatResponse(BaseModel):
    response: str

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "classifier": classifier is not None,
        "storage": storage is not None,
    }


@app.post("/dump", response_model=DumpResponse)
async def dump(req: DumpRequest):
    """
    The core endpoint. Dump ANY text and get structured data back.
    The AI classifies it, extracts structure, and stores it.
    """
    if not classifier:
        raise HTTPException(status_code=503, detail="Classifier not initialized")

    try:
        # Step 1: Classify the input
        entry = classifier.classify(req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

    # Step 2: Store it
    storage_result = None
    if storage:
        try:
            storage_result = storage.store(entry)
        except Exception as e:
            print(f"Storage error: {e}")
            # Fall back to memory
            memory_store.append(entry)
            storage_result = {"fallback": "memory", "index": len(memory_store) - 1}
    else:
        memory_store.append(entry)
        storage_result = {"fallback": "memory", "index": len(memory_store) - 1}

    return DumpResponse(success=True, entry=entry, storage=storage_result)


@app.post("/query")
async def query(req: QueryRequest):
    """Semantic search across the user's personal database."""
    if storage:
        try:
            results = storage.search(
                query=req.query,
                categories=req.categories,
                limit=req.limit,
            )
            return {"results": results, "count": len(results)}
        except Exception as e:
            print(f"Search error: {e}")

    # Fallback to memory store search
    results = []
    query_lower = req.query.lower()
    for entry in memory_store:
        text = json.dumps(entry).lower()
        if query_lower in text:
            results.append(entry)
    return {"results": results[:req.limit], "count": len(results[:req.limit])}


@app.get("/entries")
async def get_entries(category: str | None = None, limit: int = 50):
    """Get recent entries, optionally filtered by category."""
    if storage:
        try:
            results = storage.get_entries(category=category, limit=limit)
            return {"entries": results, "count": len(results)}
        except Exception as e:
            print(f"Entries error: {e}")

    # Fallback to memory store
    entries = memory_store
    if category:
        entries = [e for e in entries if e.get("category") == category]
    entries = entries[-limit:]
    entries.reverse()
    return {"entries": entries, "count": len(entries)}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Multi-turn conversational interface with tool use.
    The agent can search the database, store new entries, and trigger shopping
    dynamically within the conversation.
    """
    if not conversation_engine:
        raise HTTPException(status_code=503, detail="Conversation engine not initialized")

    try:
        response_text = conversation_engine.chat(req.messages)
        return ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


# ── Shopping Proxy ────────────────────────────────────────────────────────────

class ShopRequest(BaseModel):
    query: str

@app.post("/shop")
async def shop(req: ShopRequest):
    """
    Trigger Stagehand-powered shopping automation.
    Proxies to the Node.js shopping agent service.
    """
    shopping_url = os.getenv("SHOPPING_AGENT_URL", "http://localhost:8002")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{shopping_url}/shop",
                json={"query": req.query},
            )
            resp.raise_for_status()
            result = resp.json()

            # Store the shopping results
            if storage:
                try:
                    storage.store({
                        "category": "shopping",
                        "product": req.query,
                        "summary": result.get("comparison", ""),
                        "results": result.get("results", []),
                        "raw_input": f"Shopping search: {req.query}",
                        "tags": ["shopping", "automated"],
                    })
                except Exception as e:
                    print(f"Failed to store shopping results: {e}")

            return result
    except httpx.ConnectError:
        # Shopping agent not running - still record the intent
        if storage:
            try:
                storage.store({
                    "category": "shopping",
                    "product": req.query,
                    "summary": f"Shopping intent: {req.query}",
                    "raw_input": f"Shopping search: {req.query}",
                    "tags": ["shopping", "pending"],
                })
            except Exception:
                pass
        return {
            "query": req.query,
            "results": [],
            "comparison": f"Shopping agent is offline. Your intent to buy '{req.query}' has been saved.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shopping failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
