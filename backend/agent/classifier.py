"""
Cortex Classification Agent
Uses Claude to classify unstructured text into structured categories.
"""

import json
from anthropic import Anthropic

CATEGORIES = [
    "task",       # Action items, todos, things to do
    "idea",       # Startup ideas, project ideas, creative thoughts
    "shopping",   # Purchase intent, product research, wishlists
    "note",       # General notes, research snippets, learnings
    "meeting",    # Meeting notes, agendas, action items from meetings
    "reflection", # Personal reflections, journal entries, feelings
    "contact",    # Contact info, people to remember
    "event",      # Events, dates, appointments
]

CLASSIFICATION_SYSTEM_PROMPT = """You are the classification engine for Cortex, a personal AI brain.
Your job: take ANY unstructured text a user dumps in and figure out what it is.

You MUST respond with valid JSON only. No markdown, no explanation, just JSON.

Classify the input into one of these categories: {categories}

For each category, extract the relevant structured fields:

**task**: {{"category": "task", "title": str, "description": str, "priority": "high"|"medium"|"low", "due_date": str|null, "tags": [str]}}
**idea**: {{"category": "idea", "title": str, "description": str, "domain": str, "tags": [str], "potential": "high"|"medium"|"low"}}
**shopping**: {{"category": "shopping", "product": str, "budget": str|null, "preferences": [str], "urgency": "high"|"medium"|"low", "tags": [str]}}
**note**: {{"category": "note", "title": str, "content": str, "tags": [str], "source": str|null}}
**meeting**: {{"category": "meeting", "title": str, "attendees": [str], "action_items": [str], "date": str|null, "tags": [str]}}
**reflection**: {{"category": "reflection", "title": str, "content": str, "mood": str, "tags": [str]}}
**contact**: {{"category": "contact", "name": str, "details": str, "context": str, "tags": [str]}}
**event**: {{"category": "event", "title": str, "date": str|null, "location": str|null, "description": str, "tags": [str]}}

Always include a "summary" field with a 1-sentence summary of the input.
Always include a "raw_input" field with the original text.
Be smart about classification - infer context, dates, priorities from natural language.
If the text contains multiple items (e.g. a shopping list), pick the primary category
and capture all items in the structured fields."""

CONVERSATION_SYSTEM_PROMPT = """You are Cortex, a friendly and sharp AI personal assistant.
You help users organize their thoughts, tasks, ideas, and life.

You have access to the user's personal database containing their:
- Tasks and todos
- Ideas and creative thoughts
- Shopping lists and purchase research
- Notes and research snippets
- Meeting notes
- Personal reflections
- Contacts
- Events

When the user asks a question, search their database and provide helpful, contextual answers.
Be conversational, warm, and proactive. If you notice patterns, mention them.
If something is time-sensitive, flag it.

You speak concisely but with personality. Think of yourself as a brilliant executive
assistant who actually knows the user well."""


class CortexClassifier:
    """Classifies unstructured text into structured categories using Claude."""

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"

    def classify(self, text: str) -> dict:
        """Classify raw text into a structured entry."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=CLASSIFICATION_SYSTEM_PROMPT.format(
                categories=", ".join(CATEGORIES)
            ),
            messages=[{"role": "user", "content": text}],
        )

        raw = response.content[0].text.strip()

        # Handle potential markdown code blocks in response
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]  # Remove first line
            raw = raw.rsplit("```", 1)[0]  # Remove last ```

        result = json.loads(raw)
        result["raw_input"] = text
        return result

    def chat(self, messages: list[dict], context: str = "") -> str:
        """Have a conversational exchange with context from the database."""
        system = CONVERSATION_SYSTEM_PROMPT
        if context:
            system += f"\n\nHere is relevant context from the user's database:\n{context}"

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system,
            messages=messages,
        )

        return response.content[0].text
