"""
Semantic Vector Embedding and Similarity Engine for Project SREE
Enables 100% offline, zero-cost semantic search and contextual memory recall.
Supports:
  1. Ollama Vector Embeddings (e.g. nomic-embed-text / all-minilm) when available.
  2. Built-in Deterministic Subword & Semantic Cluster Vectorizer (128-dim dense space).
  3. NumPy cosine similarity ranking and relevance gating.
"""

import re
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger("sree.memory.semantic_engine")

# Semantic domain clusters for zero-cost offline concept association
SEMANTIC_DOMAINS: Dict[str, List[str]] = {
    "coding": [
        "code", "coding", "programming", "developer", "software", "script",
        "python", "typescript", "javascript", "rust", "cpp", "csharp", "java",
        "editor", "ide", "vscode", "visual studio", "terminal", "git", "github",
        "compiler", "debug", "tools", "stack", "algorithm", "backend", "frontend"
    ],
    "preferences": [
        "prefer", "preference", "favorite", "favourite", "like", "love",
        "theme", "dark", "light", "mode", "color", "custom", "setting",
        "default", "config", "style", "font", "layout"
    ],
    "pets": [
        "pet", "dog", "cat", "puppy", "kitten", "animal", "max", "breed",
        "bark", "meow", "vet", "paws", "canine", "feline"
    ],
    "location": [
        "live", "living", "location", "city", "country", "home", "address",
        "state", "place", "resident", "san francisco", "california", "india",
        "chennai", "hometown", "residence", "timezone"
    ],
    "hardware": [
        "laptop", "pc", "computer", "gpu", "cpu", "ram", "memory", "nvidia",
        "rtx", "screen", "monitor", "display", "specs", "disk", "ssd", "hardware",
        "keyboard", "mouse", "headset", "microphone"
    ],
    "work": [
        "job", "work", "office", "career", "company", "meeting", "project",
        "boss", "colleague", "task", "deadline", "salary", "client", "business",
        "schedule", "manager", "team"
    ],
    "food": [
        "food", "diet", "eat", "eating", "drink", "coffee", "tea", "water",
        "breakfast", "lunch", "dinner", "restaurant", "pizza", "vegetarian",
        "vegan", "snack", "beverage"
    ],
    "health": [
        "health", "fitness", "exercise", "workout", "gym", "sleep", "walk",
        "run", "weight", "medicine", "doctor", "water", "hydration"
    ]
}

VECTOR_DIMENSION = 128

class SemanticEmbeddingEngine:
    def __init__(self, vector_dim: int = VECTOR_DIMENSION):
        self.vector_dim = vector_dim

    def embed_text_sync(self, text: str) -> List[float]:
        """
        Generates a normalized dense vector embedding (128-dim) using
        multi-domain semantic projection and subword character n-grams.
        Runs locally in <1ms with zero network requests or GPU overhead.
        """
        clean = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower()).strip()
        words = clean.split()
        if not words:
            return [0.0] * self.vector_dim

        vec = np.zeros(self.vector_dim, dtype=np.float32)

        # 1. Semantic domain affinity projection
        domain_names = list(SEMANTIC_DOMAINS.keys())
        for d_idx, (domain, keywords) in enumerate(SEMANTIC_DOMAINS.items()):
            score = 0.0
            for w in words:
                if w in keywords:
                    score += 2.5
                elif any(w in kw or kw in w for kw in keywords if len(w) >= 4):
                    score += 1.2
            if score > 0:
                # Project domain activation into dedicated 8-dim orthant
                base_idx = d_idx * 8
                for i in range(8):
                    vec[base_idx + i] += score * (1.0 / (i + 1.0))

        # 2. Subword n-gram hash projection (for vocabulary generalization)
        hash_start = len(domain_names) * 8
        hash_dim = self.vector_dim - hash_start

        tokens = list(words)
        for w in words:
            if len(w) >= 3:
                for n in (3, 4):
                    for i in range(len(w) - n + 1):
                        tokens.append(w[i:i+n])

        for tok in tokens:
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
            idx = hash_start + (h % hash_dim)
            sign = 1.0 if ((h >> 8) & 1) else -1.0
            weight = 0.4 + (0.05 * len(tok))
            vec[idx] += sign * weight

        # L2 Unit Normalization
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return [float(x) for x in vec]

    async def embed_text(self, text: str) -> List[float]:
        """
        Generates embeddings. First attempts local Ollama nomic-embed-text / all-minilm.
        Falls back seamlessly to local subword-semantic vectorizer if Ollama is unreachable.
        """
        try:
            from ..ai.ollama_client import ollama_client
            if await ollama_client.is_available():
                emb = await ollama_client.get_embedding(text)
                if emb and len(emb) > 0:
                    arr = np.array(emb, dtype=np.float32)
                    norm = np.linalg.norm(arr)
                    if norm > 0:
                        arr = arr / norm
                    return [float(x) for x in arr]
        except Exception as e:
            logger.debug(f"Ollama embedding skipped: {e}")

        return self.embed_text_sync(text)

    def cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity between two float vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def rank_memories(
        self,
        query_vector: List[float],
        candidates: List[Dict[str, Any]],
        top_k: int = 5,
        min_similarity: float = 0.20
    ) -> List[Dict[str, Any]]:
        """
        Ranks candidate memories by cosine similarity against query vector.
        Filters by min_similarity threshold and returns top_k results.
        """
        scored: List[Tuple[float, Dict[str, Any]]] = []

        for mem in candidates:
            emb = mem.get("embedding")
            if not emb:
                # If memory lacks embedding, compute synchronously on the fly
                fact_text = f"{mem.get('category', '')}: {mem.get('key', '')} is {mem.get('value', '')}"
                emb = self.embed_text_sync(fact_text)

            sim = self.cosine_similarity(query_vector, emb)
            if sim >= min_similarity:
                mem_copy = dict(mem)
                mem_copy["similarity"] = round(sim, 4)
                scored.append((sim, mem_copy))

        # Sort descending by similarity score
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

semantic_engine = SemanticEmbeddingEngine()

