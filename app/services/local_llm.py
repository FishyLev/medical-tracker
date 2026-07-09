# app/services/local_llm.py
import json
import os
import faiss
import numpy as np
import requests
from sentence_transformers import SentenceTransformer

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "")
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "Medical AI Assistant")

MEDICAL_INDEX_PATH = "rag_store/medical.index"
MEDICAL_DOCS_PATH = "rag_store/medical_docs.json"

MENTAL_INDEX_PATH = "rag_store/mental_health.index"
MENTAL_DOCS_PATH = "rag_store/mental_health_docs.json"

MEDICAL_SYSTEM_PROMPT = (
    "You are a cautious medical assistant. "
    "Use the retrieved medical reference context when relevant. "
    "Provide general educational information only. "
    "Do not diagnose with certainty. "
    "Encourage professional care when needed. "
    "If symptoms seem severe or urgent, clearly recommend immediate medical attention."
)

MENTAL_HEALTH_SYSTEM_PROMPT = (
    "You are a cautious mental health support assistant. "
    "Provide supportive, general, non-diagnostic guidance. "
    "Do not claim to be a therapist or counselor. "
    "Do not provide harmful instructions. "
    "Encourage seeking licensed professional help when appropriate. "
    "If the user mentions self-harm, suicide, or immediate danger, advise urgent crisis support immediately."
)

CRISIS_SYSTEM_PROMPT = (
    "You are a safety-focused assistant. "
    "If the user may be at risk of self-harm, suicide, or immediate danger, respond briefly, calmly, and supportively. "
    "Advise contacting local emergency services or a crisis hotline immediately. "
    "Encourage reaching out to a trusted person right now. "
    "Do not provide detailed harmful instructions."
)

medical_index = None
medical_documents = None
mental_index = None
mental_documents = None
embedder = None


def load_local_model():
    global medical_index, medical_documents, mental_index, mental_documents, embedder

    if LLM_PROVIDER == "ollama":
        try:
            response = requests.get("http://127.0.0.1:11434/api/tags", timeout=10)
            response.raise_for_status()
        except Exception as exc:
            raise RuntimeError(
                "Ollama is not running. Start Ollama first and make sure the model is pulled."
            ) from exc

    elif LLM_PROVIDER == "openrouter":
        if not OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY is missing.")
    else:
        raise RuntimeError("Unsupported LLM_PROVIDER. Use 'ollama' or 'openrouter'.")

    if medical_index is None:
        medical_index = faiss.read_index(MEDICAL_INDEX_PATH)

    if medical_documents is None:
        with open(MEDICAL_DOCS_PATH, "r", encoding="utf-8") as f:
            medical_documents = json.load(f)

    try:
        if mental_index is None:
            mental_index = faiss.read_index(MENTAL_INDEX_PATH)
        if mental_documents is None:
            with open(MENTAL_DOCS_PATH, "r", encoding="utf-8") as f:
                mental_documents = json.load(f)
    except Exception:
        mental_index = None
        mental_documents = None

    if embedder is None:
        embedder = SentenceTransformer("all-MiniLM-L6-v2")


def is_crisis_query(text: str) -> bool:
    text = text.lower()
    crisis_keywords = [
        "suicide", "kill myself", "end my life", "want to die",
        "self harm", "self-harm", "hurt myself", "cut myself",
        "harm myself", "i don't want to live", "i want to disappear"
    ]
    return any(keyword in text for keyword in crisis_keywords)


def is_mental_health_query(text: str) -> bool:
    text = text.lower()
    mental_keywords = [
        "anxiety", "anxious", "depressed", "depression", "panic",
        "stress", "overwhelmed", "lonely", "sad", "hopeless",
        "mental health", "worried", "worry", "fear", "trauma",
        "emotional", "burnout", "can't sleep", "cannot sleep",
        "insomnia", "grief", "low mood"
    ]
    return any(keyword in text for keyword in mental_keywords)


def retrieve_context(query: str, index, documents, top_k: int = 5) -> str:
    if index is None or documents is None:
        return ""

    query_vec = embedder.encode([query], convert_to_numpy=True).astype(np.float32)
    distances, indices = index.search(query_vec, top_k)

    chunks = []
    for idx in indices[0]:
        if 0 <= idx < len(documents):
            item = documents[idx]
            text = item.get("text", "").strip()
            if text:
                chunks.append(text)

    return "\n".join(f"- {chunk}" for chunk in chunks)


def build_prompt(system_prompt: str, context_label: str, context: str, user_message: str) -> str:
    return f"""
{system_prompt}

{context_label}:
{context if context else "- No additional retrieved context available."}

User question:
{user_message}

Assistant:
""".strip()


def call_ollama(prompt: str, temperature: float = 0.3, num_predict: int = 220) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
        },
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()


def call_openrouter(system_prompt: str, user_prompt: str, temperature: float = 0.3, max_tokens: int = 220) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    if OPENROUTER_SITE_URL:
        headers["HTTP-Referer"] = OPENROUTER_SITE_URL
    if OPENROUTER_APP_NAME:
        headers["X-OpenRouter-Title"] = OPENROUTER_APP_NAME

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()

    choices = data.get("choices", [])
    if not choices:
        return "No response returned."

    message = choices[0].get("message", {})
    return (message.get("content") or "").strip()


def generate_with_provider(system_prompt: str, context_label: str, context: str, user_message: str,
                           temperature: float = 0.3, max_tokens: int = 220) -> str:
    combined_prompt = build_prompt(system_prompt, context_label, context, user_message)

    if LLM_PROVIDER == "ollama":
        return call_ollama(combined_prompt, temperature=temperature, num_predict=max_tokens)

    if LLM_PROVIDER == "openrouter":
        user_prompt = f"""
{context_label}:
{context if context else "- No additional retrieved context available."}

User question:
{user_message}
""".strip()
        return call_openrouter(system_prompt, user_prompt, temperature=temperature, max_tokens=max_tokens)

    raise RuntimeError("Unsupported LLM provider.")


def generate_crisis_response(user_message: str) -> str:
    return generate_with_provider(
        system_prompt=CRISIS_SYSTEM_PROMPT,
        context_label="Safety context",
        context="User may be expressing self-harm, suicide risk, or immediate danger.",
        user_message=user_message,
        temperature=0.2,
        max_tokens=140,
    )


def generate_response(user_message: str) -> str:
    if medical_index is None or medical_documents is None or embedder is None:
        raise RuntimeError("Local RAG model is not loaded.")

    if is_crisis_query(user_message):
        return generate_crisis_response(user_message)

    use_mental = (
        is_mental_health_query(user_message)
        and mental_index is not None
        and mental_documents is not None
    )

    if use_mental:
        system_prompt = MENTAL_HEALTH_SYSTEM_PROMPT
        context = retrieve_context(user_message, mental_index, mental_documents, top_k=5)
        context_label = "Relevant mental health support context"
    else:
        system_prompt = MEDICAL_SYSTEM_PROMPT
        context = retrieve_context(user_message, medical_index, medical_documents, top_k=5)
        context_label = "Relevant medical reference context"

    return generate_with_provider(
        system_prompt=system_prompt,
        context_label=context_label,
        context=context,
        user_message=user_message,
        temperature=0.3,
        max_tokens=220,
    )