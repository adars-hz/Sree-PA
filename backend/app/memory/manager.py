"""
Memory and Context Management Layer for SREE
Distinguishes short-term conversational context from persistent long-term memories.
Provides offline semantic vector embedding recall and relevance ranking.
"""

import re
from typing import List, Dict, Any, Optional
from ..database.db import db_manager
from .semantic_engine import semantic_engine

class MemoryManager:
    def __init__(self):
        self.db = db_manager

    def add_memory(
        self,
        key: str,
        value: str,
        category: str = "general",
        compute_vector: bool = True
    ) -> int:
        """
        Stores memory and automatically generates local vector embedding.
        """
        embedding = None
        if compute_vector:
            fact_text = f"{category}: {key} is {value}"
            embedding = semantic_engine.embed_text_sync(fact_text)
        return self.db.add_memory(key=key, value=value, category=category, embedding=embedding)

    def search_semantic_memories(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.20
    ) -> List[Dict[str, Any]]:
        """
        Performs 100% offline semantic similarity search across stored memories
        using NumPy cosine similarity and subword-semantic embeddings.
        """
        candidates = self.db.get_all_memories(approved_only=True)
        if not candidates or not query.strip():
            return []

        query_vector = semantic_engine.embed_text_sync(query)
        ranked = semantic_engine.rank_memories(
            query_vector=query_vector,
            candidates=candidates,
            top_k=top_k,
            min_similarity=min_similarity
        )

        # Backfill any candidates that lacked an embedding in DB
        for item in ranked:
            if not item.get("embedding"):
                fact_text = f"{item.get('category', 'general')}: {item.get('key', '')} is {item.get('value', '')}"
                emb = semantic_engine.embed_text_sync(fact_text)
                self.db.update_memory_embedding(item["id"], emb)
                item["embedding"] = emb

        return ranked

    def get_memory_context_string(self) -> str:
        """Constructs a clean bulleted list of all approved memories to inject into LLM system prompt."""
        memories = self.db.get_all_memories(approved_only=True)
        if not memories:
            return ""
        
        lines = []
        for m in memories:
            lines.append(f"- [{m['category'].upper()}] {m['key']}: {m['value']}")
        return "\n".join(lines)

    def get_relevant_memory_context(
        self,
        user_query: Optional[str] = None,
        max_items: int = 5,
        min_similarity: float = 0.15
    ) -> str:
        """
        Constructs a semantically ranked bulleted list of approved memories to inject into LLM system prompt.
        If user_query is provided, ranks memories by cosine similarity and injects top-k closest matches.
        """
        if user_query and user_query.strip():
            ranked = self.search_semantic_memories(
                query=user_query,
                top_k=max_items,
                min_similarity=min_similarity
            )
            if ranked:
                lines = []
                for m in ranked:
                    sim = m.get("similarity", 1.0)
                    score_pct = int(sim * 100)
                    lines.append(f"- [{m['category'].upper()}] {m['key']}: {m['value']} (relevance: {score_pct}%)")
                return "\n".join(lines)

        # Fallback to general memory context if no semantic matches or no query
        return self.get_memory_context_string()

    def reindex_all_memories(self) -> int:
        """
        Computes and persists vector embeddings for any memories lacking one.
        Returns total number of updated memories.
        """
        memories = self.db.get_all_memories(approved_only=False)
        count = 0
        for m in memories:
            if not m.get("embedding"):
                fact_text = f"{m.get('category', 'general')}: {m.get('key', '')} is {m.get('value', '')}"
                emb = semantic_engine.embed_text_sync(fact_text)
                self.db.update_memory_embedding(m["id"], emb)
                count += 1
        return count

    def extract_memory_intent(self, user_message: str) -> Optional[Dict[str, str]]:
        """
        Rule-based heuristic detector to identify explicit memory requests.
        Examples:
          "Remember that my favorite language is Python"
          "Remember: I prefer concise answers"
        """
        patterns = [
            r"(?:please\s+)?remember\s*[:\-]?\s*(?:that\s+)?(.+)",
            r"(?:note\s+down\s*[:\-]?\s*(?:that\s+)?)(.+)",
            r"(?:save\s+to\s+memory\s*[:\-]?\s*)(.+)"
        ]
        
        lower_msg = user_message.strip()
        for p in patterns:
            match = re.search(p, lower_msg, re.IGNORECASE)
            if match:
                raw_fact = match.group(1).strip()
                # Split key/value if possible
                if " is " in raw_fact:
                    parts = raw_fact.split(" is ", 1)
                    key = parts[0].strip()
                    val = parts[1].strip()
                elif ":" in raw_fact:
                    parts = raw_fact.split(":", 1)
                    key = parts[0].strip()
                    val = parts[1].strip()
                else:
                    key = "preference"
                    val = raw_fact
                    
                return {"key": key, "value": val, "category": "user_preference"}
        return None

memory_manager = MemoryManager()
