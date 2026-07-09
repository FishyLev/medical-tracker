import os
import json
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

RAW_FILES = [
    "datasets/extracted/disease-and-symptoms/Diseases_Symptoms.csv",
    "datasets/extracted/disease-and-symptoms-dataset/Disease precaution.csv",
    "datasets/extracted/disease-and-symptoms-dataset/DiseaseAndSymptoms.csv",
    "datasets/extracted/disease-symptoms-and-treatments-dataset/Diseases_Symptoms.csv",
    "datasets/extracted/health-symptoms-and-disease-prediction-dataset/training.csv",
    "datasets/extracted/sympscan-symptomps-to-disease/description.csv",
    "datasets/extracted/sympscan-symptomps-to-disease/diets.csv",
    "datasets/extracted/sympscan-symptomps-to-disease/medications.csv",
    "datasets/extracted/sympscan-symptomps-to-disease/precautions.csv",
    "datasets/extracted/sympscan-symptomps-to-disease/workout.csv",
]

OPTIONAL_LARGE_FILE = "datasets/extracted/sympscan-symptomps-to-disease/Diseases_and_Symptoms_dataset.csv"

OUTPUT_DIR = "rag_store"
INDEX_PATH = os.path.join(OUTPUT_DIR, "medical.index")
DOCS_PATH = os.path.join(OUTPUT_DIR, "medical_docs.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)

embedder = SentenceTransformer("all-MiniLM-L6-v2")
documents = []


def clean_val(v):
    if pd.isna(v):
        return ""
    return str(v).strip()


def row_to_text(row, source):
    parts = []
    for col, val in row.items():
        val = clean_val(val)
        if not val or val.lower() == "nan":
            continue
        parts.append(f"{col}: {val}")
    if not parts:
        return None
    return {
        "source": source,
        "text": " | ".join(parts)
    }


for path in RAW_FILES:
    if not os.path.exists(path):
        print("Skipping missing:", path)
        continue

    print("Reading:", path)
    df = pd.read_csv(path)

    for _, row in df.iterrows():
        doc = row_to_text(row, os.path.basename(path))
        if doc:
            documents.append(doc)

# Optional: sample from the very large file instead of loading everything at once
if os.path.exists(OPTIONAL_LARGE_FILE):
    print("Reading sampled rows from large file:", OPTIONAL_LARGE_FILE)
    df_large = pd.read_csv(OPTIONAL_LARGE_FILE, nrows=20000)
    for _, row in df_large.iterrows():
        doc = row_to_text(row, os.path.basename(OPTIONAL_LARGE_FILE))
        if doc:
            documents.append(doc)

print("Total documents:", len(documents))

texts = [d["text"] for d in documents]
embeddings = embedder.encode(texts, show_progress_bar=True, convert_to_numpy=True)

dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings, dtype=np.float32))

faiss.write_index(index, INDEX_PATH)

with open(DOCS_PATH, "w", encoding="utf-8") as f:
    json.dump(documents, f, ensure_ascii=False, indent=2)

print("Saved index to", INDEX_PATH)
print("Saved docs to", DOCS_PATH)