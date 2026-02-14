"""
Elasticsearch client for Cortex.
Handles indexing, searching, and embedding via JINA on Elastic Inference Service.
"""

import os
import uuid
from datetime import datetime, timezone

import httpx
from elasticsearch import Elasticsearch

from .schemas import CATEGORY_INDEX_MAP, INDEX_SCHEMAS


class CortexStorage:
    """Manages Elasticsearch storage with JINA embeddings for Cortex."""

    def __init__(
        self,
        es_url: str | None = None,
        es_api_key: str | None = None,
    ):
        self.es_url = es_url or os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.es_api_key = es_api_key or os.getenv("ELASTICSEARCH_API_KEY", "")

        if self.es_api_key:
            self.es = Elasticsearch(self.es_url, api_key=self.es_api_key)
        else:
            self.es = Elasticsearch(self.es_url)

    def initialize_indices(self):
        """Create all indices if they don't exist."""
        for index_name, schema in INDEX_SCHEMAS.items():
            if not self.es.indices.exists(index=index_name):
                self.es.indices.create(index=index_name, body=schema)
                print(f"Created index: {index_name}")
            else:
                print(f"Index already exists: {index_name}")

    def _get_embedding(self, text: str) -> list[float]:
        """Get JINA embedding for text via Elastic Inference Service.
        Falls back to a simple hash-based embedding for local dev."""
        try:
            # Try Elastic Inference Service (JINA v3)
            response = self.es.inference.inference(
                inference_id="jina-embeddings",
                body={"input": [text]},
            )
            return response["data"][0]["embedding"]
        except Exception:
            # Fallback: use Anthropic-compatible embedding or a simple approach
            # For hackathon, we'll use a deterministic hash-based vector as fallback
            import hashlib
            h = hashlib.sha256(text.encode()).hexdigest()
            # Generate a 1024-dim vector from hash (good enough for dev)
            vec = []
            for i in range(0, min(len(h), 64), 1):
                val = int(h[i], 16) / 15.0 * 2 - 1  # normalize to [-1, 1]
                vec.append(val)
            # Pad to 1024
            while len(vec) < 1024:
                vec.extend(vec[:min(len(vec), 1024 - len(vec))])
            return vec[:1024]

    def store(self, entry: dict) -> dict:
        """Store a classified entry in the appropriate index."""
        category = entry.get("category", "note")
        index_name = CATEGORY_INDEX_MAP.get(category, "cortex-notes")

        # Add metadata
        entry["id"] = str(uuid.uuid4())
        entry["created_at"] = datetime.now(timezone.utc).isoformat()
        entry["updated_at"] = entry["created_at"]

        # Generate embedding from raw input + summary
        embed_text = f"{entry.get('summary', '')} {entry.get('raw_input', '')}"
        entry["embedding"] = self._get_embedding(embed_text)

        # Index in Elasticsearch
        self.es.index(index=index_name, id=entry["id"], document=entry)

        return {"id": entry["id"], "index": index_name, "category": category}

    def search(self, query: str, categories: list[str] | None = None, limit: int = 10) -> list[dict]:
        """Semantic search across all or specific category indices."""
        if categories:
            indices = [CATEGORY_INDEX_MAP[c] for c in categories if c in CATEGORY_INDEX_MAP]
        else:
            indices = list(CATEGORY_INDEX_MAP.values())

        index_str = ",".join(indices)
        query_embedding = self._get_embedding(query)

        body = {
            "size": limit,
            "query": {
                "bool": {
                    "should": [
                        # Semantic search via embedding
                        {
                            "script_score": {
                                "query": {"match_all": {}},
                                "script": {
                                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                    "params": {"query_vector": query_embedding},
                                },
                            }
                        },
                        # Text search for keyword matching
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "content", "description", "summary", "raw_input", "product", "name"],
                                "type": "best_fields",
                                "boost": 0.5,
                            }
                        },
                    ]
                }
            },
            "_source": {"excludes": ["embedding"]},
        }

        # Check which indices actually exist before searching
        existing_indices = [idx for idx in indices if self.es.indices.exists(index=idx)]
        if not existing_indices:
            return []

        index_str = ",".join(existing_indices)
        response = self.es.search(index=index_str, body=body)

        results = []
        for hit in response["hits"]["hits"]:
            doc = hit["_source"]
            doc["_score"] = hit["_score"]
            doc["_index"] = hit["_index"]
            results.append(doc)

        return results

    def get_entries(self, category: str | None = None, limit: int = 50) -> list[dict]:
        """Get recent entries, optionally filtered by category."""
        if category:
            indices = [CATEGORY_INDEX_MAP.get(category, "cortex-notes")]
        else:
            indices = list(CATEGORY_INDEX_MAP.values())

        existing_indices = [idx for idx in indices if self.es.indices.exists(index=idx)]
        if not existing_indices:
            return []

        index_str = ",".join(existing_indices)

        body = {
            "size": limit,
            "sort": [{"created_at": {"order": "desc"}}],
            "_source": {"excludes": ["embedding"]},
        }

        response = self.es.search(index=index_str, body=body)

        results = []
        for hit in response["hits"]["hits"]:
            doc = hit["_source"]
            doc["_index"] = hit["_index"]
            results.append(doc)

        return results

    def delete_entry(self, entry_id: str, category: str) -> bool:
        """Delete an entry by ID and category."""
        index_name = CATEGORY_INDEX_MAP.get(category, "cortex-notes")
        try:
            self.es.delete(index=index_name, id=entry_id)
            return True
        except Exception:
            return False
