from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from utils.embeddings import embed_text
from utils.vector_math import cosine_similarity

BASE_DIR = Path(__file__).resolve().parent
VECTOR_STORE_PATH = BASE_DIR / "data" / "vector_store.json"

app = FastAPI(title="RAG Assistant API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    session_id: str
    question: str


class ChatResponse(BaseModel):
    answer: str
    top_chunks: list[dict]


def load_vector_store() -> list[dict]:
    if not VECTOR_STORE_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail="vector_store.json not found. Run backend/scripts/ingest.py first.",
        )

    return json.loads(VECTOR_STORE_PATH.read_text(encoding="utf-8"))


def retrieve_top_chunks(question: str, top_k: int = 3) -> list[dict]:
    query_embedding = embed_text(question)
    rows = load_vector_store()

    scored = []
    for row in rows:
        score = cosine_similarity(query_embedding, row["embedding"])
        scored.append({**row, "score": score})

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def build_augmented_prompt(question: str, top_chunks: list[dict]) -> str:
    context_lines = [f"{i + 1}. {chunk['content']}" for i, chunk in enumerate(top_chunks)]
    return (
        "You are a helpful university support assistant. "
        "Answer the question using ONLY the context provided below. "
        "If the answer is not present, say you don't know.\n\n"
        f"CONTEXT:\n{os.linesep.join(context_lines)}\n\n"
        f"USER QUESTION: {question}\n\n"
        "ANSWER:"
    )


def generate_answer(prompt: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "fallback").lower()

    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a grounded assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        return response.choices[0].message.content or "I don't know."

    if provider == "gemini" and os.getenv("GEMINI_API_KEY"):
        import google.generativeai as genai

        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model_name = os.getenv("GEMINI_CHAT_MODEL", "gemini-1.5-flash")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text

    return (
        "I used retrieved policy context only. "
        "Configure OPENAI_API_KEY or GEMINI_API_KEY for model-generated responses."
    )


@app.get("/api/session")
def create_session() -> dict:
    return {"session_id": str(uuid.uuid4())}


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    top_chunks = retrieve_top_chunks(payload.question, top_k=3)
    prompt = build_augmented_prompt(payload.question, top_chunks)
    answer = generate_answer(prompt)

    return ChatResponse(
        answer=answer,
        top_chunks=[
            {
                "chunk_id": chunk["chunk_id"],
                "title": chunk["title"],
                "content": chunk["content"],
                "score": round(chunk["score"], 4),
            }
            for chunk in top_chunks
        ],
    )
