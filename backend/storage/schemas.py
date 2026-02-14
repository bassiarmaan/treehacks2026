"""
Elasticsearch index schemas for Cortex content types.
Uses JINA v3 embeddings (1024 dimensions) for semantic search.
"""

# Shared embedding field config for JINA v3
EMBEDDING_FIELD = {
    "type": "dense_vector",
    "dims": 1024,
    "index": True,
    "similarity": "cosine",
}

TIMESTAMP_FIELD = {"type": "date"}
KEYWORD_FIELD = {"type": "keyword"}
TEXT_FIELD = {"type": "text"}

# Base mappings shared by all indices
BASE_PROPERTIES = {
    "raw_input": TEXT_FIELD,
    "summary": TEXT_FIELD,
    "category": KEYWORD_FIELD,
    "tags": KEYWORD_FIELD,
    "created_at": TIMESTAMP_FIELD,
    "updated_at": TIMESTAMP_FIELD,
    "embedding": EMBEDDING_FIELD,
}

INDEX_SCHEMAS = {
    "cortex-tasks": {
        "mappings": {
            "properties": {
                **BASE_PROPERTIES,
                "title": TEXT_FIELD,
                "description": TEXT_FIELD,
                "priority": KEYWORD_FIELD,
                "due_date": {"type": "date", "format": "yyyy-MM-dd||strict_date_optional_time||epoch_millis", "ignore_malformed": True},
                "status": KEYWORD_FIELD,
            }
        }
    },
    "cortex-ideas": {
        "mappings": {
            "properties": {
                **BASE_PROPERTIES,
                "title": TEXT_FIELD,
                "description": TEXT_FIELD,
                "domain": KEYWORD_FIELD,
                "potential": KEYWORD_FIELD,
            }
        }
    },
    "cortex-shopping": {
        "mappings": {
            "properties": {
                **BASE_PROPERTIES,
                "product": TEXT_FIELD,
                "budget": KEYWORD_FIELD,
                "preferences": KEYWORD_FIELD,
                "urgency": KEYWORD_FIELD,
                "results": {"type": "object", "enabled": False},  # Stagehand results
            }
        }
    },
    "cortex-notes": {
        "mappings": {
            "properties": {
                **BASE_PROPERTIES,
                "title": TEXT_FIELD,
                "content": TEXT_FIELD,
                "source": KEYWORD_FIELD,
            }
        }
    },
    "cortex-meetings": {
        "mappings": {
            "properties": {
                **BASE_PROPERTIES,
                "title": TEXT_FIELD,
                "attendees": KEYWORD_FIELD,
                "action_items": TEXT_FIELD,
                "date": {"type": "date", "format": "yyyy-MM-dd||strict_date_optional_time||epoch_millis", "ignore_malformed": True},
            }
        }
    },
    "cortex-reflections": {
        "mappings": {
            "properties": {
                **BASE_PROPERTIES,
                "title": TEXT_FIELD,
                "content": TEXT_FIELD,
                "mood": KEYWORD_FIELD,
            }
        }
    },
    "cortex-contacts": {
        "mappings": {
            "properties": {
                **BASE_PROPERTIES,
                "name": TEXT_FIELD,
                "details": TEXT_FIELD,
                "context": TEXT_FIELD,
            }
        }
    },
    "cortex-events": {
        "mappings": {
            "properties": {
                **BASE_PROPERTIES,
                "title": TEXT_FIELD,
                "date": {"type": "date", "format": "yyyy-MM-dd||strict_date_optional_time||epoch_millis", "ignore_malformed": True},
                "location": TEXT_FIELD,
                "description": TEXT_FIELD,
            }
        }
    },
}

# Category to index mapping
CATEGORY_INDEX_MAP = {
    "task": "cortex-tasks",
    "idea": "cortex-ideas",
    "shopping": "cortex-shopping",
    "note": "cortex-notes",
    "meeting": "cortex-meetings",
    "reflection": "cortex-reflections",
    "contact": "cortex-contacts",
    "event": "cortex-events",
}
