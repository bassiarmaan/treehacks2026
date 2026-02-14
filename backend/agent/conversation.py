"""
Cortex Multi-Turn Conversation Engine
Uses Claude with tool use for dynamic, context-aware conversations.
This is the core for the Decagon (conversational) and Greylock (multi-turn agent) prizes.
"""

import json
from anthropic import Anthropic

TOOLS = [
    {
        "name": "search_brain",
        "description": "Search the user's personal Cortex database for relevant entries. Use this when the user asks about something they've previously stored, or when you need context about their tasks, ideas, notes, shopping lists, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant entries in the user's database.",
                },
                "categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional filter by category: task, idea, shopping, note, meeting, reflection, contact, event",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "dump_entry",
        "description": "Store a new entry in the user's Cortex database. Use this when the user tells you something new they want to remember, a task to track, an idea to store, etc. The text will be auto-classified.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The raw text to classify and store.",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "get_entries",
        "description": "Get recent entries from the user's database, optionally filtered by category. Good for showing overviews or listing items.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Optional category filter: task, idea, shopping, note, meeting, reflection, contact, event",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max entries to return. Default 10.",
                },
            },
        },
    },
    {
        "name": "shop_for_product",
        "description": "Trigger a web search for products. Use this when the user wants to buy something or compare prices. Returns product results with prices and sources.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Product search query.",
                },
            },
            "required": ["query"],
        },
    },
]

SYSTEM_PROMPT = """You are Cortex, an AI-powered personal assistant and second brain.
You are warm, sharp, proactive, and helpful. You speak naturally and conversationally.

You have tools to:
1. Search the user's personal database (search_brain)
2. Store new thoughts/tasks/ideas/notes (dump_entry)
3. Browse their entries (get_entries)
4. Search for products to buy (shop_for_product)

IMPORTANT BEHAVIORS:
- When the user mentions something that should be remembered, proactively offer to store it
- When answering questions, search the database first for relevant context
- If the user asks about their tasks/ideas/shopping, use get_entries to fetch them
- For shopping requests, use shop_for_product to find deals
- Notice patterns and offer insights ("You've been thinking a lot about X lately")
- Be concise but conversational -- like a brilliant friend who knows everything about you
- If you can handle something with a tool, DO IT instead of just describing what you would do

You can chain multiple tool calls to accomplish complex requests."""


class ConversationEngine:
    """Multi-turn conversation engine with tool use for dynamic interactions."""

    def __init__(self, api_key: str, classifier=None, storage=None, memory_store=None):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        self.classifier = classifier
        self.storage = storage
        self.memory_store = memory_store  # Fallback in-memory list

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool call and return the result as a string."""

        if tool_name == "search_brain":
            query = tool_input["query"]
            categories = tool_input.get("categories")
            if self.storage:
                try:
                    results = self.storage.search(query=query, categories=categories, limit=5)
                    if results:
                        parts = []
                        for r in results:
                            cat = r.get("category", "unknown")
                            summary = r.get("summary", r.get("title", "No summary"))
                            raw = r.get("raw_input", "")[:200]
                            parts.append(f"[{cat}] {summary}\n  Original: {raw}")
                        return "\n\n".join(parts)
                    return "No results found."
                except Exception as e:
                    return f"Search error: {e}"

            # Fallback to memory store
            if self.memory_store is not None:
                import json as _json
                query_lower = query.lower()
                matches = []
                for entry in self.memory_store:
                    text = _json.dumps(entry).lower()
                    if any(word in text for word in query_lower.split()):
                        matches.append(entry)
                if matches:
                    parts = []
                    for r in matches[:5]:
                        cat = r.get("category", "unknown")
                        summary = r.get("summary", r.get("title", "No summary"))
                        raw = r.get("raw_input", "")[:200]
                        parts.append(f"[{cat}] {summary}\n  Original: {raw}")
                    return "\n\n".join(parts)
                return "No results found matching your query."
            return "Database not connected. No results available."

        elif tool_name == "dump_entry":
            text = tool_input["text"]
            if self.classifier:
                try:
                    entry = self.classifier.classify(text)
                    if self.storage:
                        self.storage.store(entry)
                        return f"Stored as [{entry.get('category')}]: {entry.get('summary', 'Saved')}"
                    elif self.memory_store is not None:
                        self.memory_store.append(entry)
                        return f"Stored as [{entry.get('category')}]: {entry.get('summary', 'Saved')}"
                    return f"Classified as [{entry.get('category')}]: {entry.get('summary', 'Processed')} (not stored)"
                except Exception as e:
                    return f"Failed to process: {e}"
            return "Classifier not available."

        elif tool_name == "get_entries":
            category = tool_input.get("category")
            limit = tool_input.get("limit", 10)
            if self.storage:
                try:
                    entries = self.storage.get_entries(category=category, limit=limit)
                    if entries:
                        parts = []
                        for e in entries:
                            cat = e.get("category", "unknown")
                            title = e.get("title", e.get("summary", "Untitled"))
                            date = e.get("created_at", "")[:10]
                            parts.append(f"[{cat}] {title} ({date})")
                        return "\n".join(parts)
                    return "No entries found."
                except Exception as e:
                    return f"Error fetching entries: {e}"

            # Fallback to memory store
            if self.memory_store is not None:
                entries = list(self.memory_store)
                if category:
                    entries = [e for e in entries if e.get("category") == category]
                entries = entries[-limit:]
                if entries:
                    parts = []
                    for e in entries:
                        cat = e.get("category", "unknown")
                        title = e.get("title", e.get("summary", "Untitled"))
                        parts.append(f"[{cat}] {title}")
                    return "\n".join(parts)
                return "No entries found."
            return "Database not connected."

        elif tool_name == "shop_for_product":
            query = tool_input["query"]
            return f"Shopping search initiated for: {query}. Check the shopping tab for results."

        return f"Unknown tool: {tool_name}"

    def chat(self, messages: list[dict]) -> str:
        """
        Run a multi-turn conversation with tool use.
        Handles the full agentic loop: user message -> tool calls -> final response.
        """
        # Run the conversation loop
        current_messages = list(messages)
        max_iterations = 5  # Prevent infinite loops

        for _ in range(max_iterations):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=current_messages,
            )

            # Check if we need to execute tools
            if response.stop_reason == "tool_use":
                # Add assistant response (with tool use blocks)
                current_messages.append({
                    "role": "assistant",
                    "content": response.content,
                })

                # Execute each tool call
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                # Add tool results
                current_messages.append({
                    "role": "user",
                    "content": tool_results,
                })
            else:
                # No tool use -- extract text response
                text_parts = []
                for block in response.content:
                    if hasattr(block, "text"):
                        text_parts.append(block.text)
                return "\n".join(text_parts) if text_parts else "I'm not sure how to help with that."

        return "I've been thinking too hard about this. Could you rephrase?"
