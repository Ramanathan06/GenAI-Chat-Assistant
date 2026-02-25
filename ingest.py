from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from utils.chunking import chunk_text
from utils.embeddings import embed_text

DOCS_PATH = BASE_DIR / "data" / "docs.json"
VECTOR_STORE_PATH = BASE_DIR / "data" / "vector_store.json"


def ingest_documents() -> None:
    docs = json.loads(DOCS_PATH.read_text(encoding="utf-8"))
    vector_rows = []

    for doc in docs:
        chunks = chunk_text(doc["content"], chunk_size=300, overlap=50)
        for idx, chunk in enumerate(chunks):
            vector_rows.append(
                {
                    "doc_id": doc["id"],
                    "title": doc["title"],
                    "chunk_id": f"{doc['id']}-chunk-{idx + 1}",
                    "content": chunk,
                    "embedding": embed_text(chunk),
                }
            )

    VECTOR_STORE_PATH.write_text(json.dumps(vector_rows, indent=2), encoding="utf-8")
    print(f"Ingested {len(vector_rows)} chunks into {VECTOR_STORE_PATH}")


if __name__ == "__main__":
    ingest_documents()
