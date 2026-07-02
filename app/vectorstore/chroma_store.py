import uuid

import chromadb

from app.core.config import get_settings


class ChromaMemoryStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name
        )

    def add_memory(self, user_id: int, content: str, memory_type: str, metadata: dict | None = None) -> str:
        memory_id = str(uuid.uuid4())
        payload = {
            "user_id": str(user_id),
            "memory_type": memory_type,
        }
        if metadata:
            for key, value in metadata.items():
                payload[key] = str(value)

        self.collection.upsert(
            ids=[memory_id],
            documents=[content],
            metadatas=[payload],
        )
        return memory_id

    def search_memories(self, user_id: int, query: str, n_results: int = 5) -> list[dict]:
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"user_id": str(user_id)},
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]

        output = []
        for idx, doc in enumerate(documents):
            output.append(
                {
                    "id": ids[idx] if idx < len(ids) else "",
                    "document": doc,
                    "metadata": metadatas[idx] if idx < len(metadatas) else {},
                }
            )
        return output

    def delete_user_memories(self, user_id: int) -> None:
        matches = self.collection.get(where={"user_id": str(user_id)})
        ids = matches.get("ids", [])
        if ids:
            self.collection.delete(ids=ids)