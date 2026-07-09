import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INPUT_FILES = [
    "datasets/extracted/mental-health/combined_intents.json",
    "datasets/extracted/mental-health-conversational-data/intents.json",
]

OUTPUT_DIR = "rag_store"
INDEX_PATH = os.path.join(OUTPUT_DIR, "mental_health.index")
DOCS_PATH = os.path.join(OUTPUT_DIR, "mental_health_docs.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)

embedder = SentenceTransformer("all-MiniLM-L6-v2")
documents = []


def normalize_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def add_doc(intent_name, pattern, response, source):
    pattern = normalize_text(pattern)
    response = normalize_text(response)

    if not pattern and not response:
        return

    text_parts = []
    if intent_name:
        text_parts.append(f"intent: {intent_name}")
    if pattern:
        text_parts.append(f"user_example: {pattern}")
    if response:
        text_parts.append(f"safe_support_reply: {response}")

    documents.append({
        "source": source,
        "intent": intent_name,
        "pattern": pattern,
        "response": response,
        "text": " | ".join(text_parts)
    })


for path in INPUT_FILES:
    if not os.path.exists(path):
        print("Skipping missing:", path)
        continue

    print("Reading:", path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    intents = data.get("intents", [])
    for item in intents:
        tag = normalize_text(item.get("tag"))
        patterns = item.get("patterns", [])
        responses = item.get("responses", [])

        if not patterns:
            patterns = [""]

        if not responses:
            responses = [""]

        for pattern in patterns:
            for response in responses[:3]:
                add_doc(tag, pattern, response, os.path.basename(path))

print("Total mental health docs:", len(documents))

texts = [d["text"] for d in documents]
embeddings = embedder.encode(texts, show_progress_bar=True, convert_to_numpy=True)

index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(np.array(embeddings, dtype=np.float32))
faiss.write_index(index, INDEX_PATH)

with open(DOCS_PATH, "w", encoding="utf-8") as f:
    json.dump(documents, f, ensure_ascii=False, indent=2)

print("Saved:", INDEX_PATH)
print("Saved:", DOCS_PATH)