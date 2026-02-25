from __future__ import annotations

import hashlib
import os
from typing import List


def _fallback_embedding(text: str, dim: int = 128) -> List[float]:
    """Deterministic local embedding fallback when API keys are unavailable."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    seed = list(digest) * (dim // len(digest) + 1)
    return [((seed[i] / 255.0) * 2) - 1 for i in range(dim)]


def embed_text(text: str) -> List[float]:
    provider = os.getenv("EMBEDDING_PROVIDER", "fallback").lower()

    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
        response = client.embeddings.create(model=model, input=text)
        return response.data[0].embedding

    if provider == "gemini" and os.getenv("GEMINI_API_KEY"):
        import google.generativeai as genai

        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = os.getenv("GEMINI_EMBED_MODEL", "models/text-embedding-004")
        result = genai.embed_content(model=model, content=text)
        return result["embedding"]

    return _fallback_embedding(text)
