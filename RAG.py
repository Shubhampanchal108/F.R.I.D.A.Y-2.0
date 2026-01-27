import chromadb
from sentence_transformers import SentenceTransformer
import os
from datetime import datetime, timezone
import uuid
from dotenv import load_dotenv

load_dotenv()

RAG_PATH = os.getenv("RAG_PATH")
os.makedirs(RAG_PATH, exist_ok=True)

client = chromadb.PersistentClient(path=RAG_PATH)
COLLECTION_NAME = "Friday_memory"
collection = client.get_or_create_collection(COLLECTION_NAME)


model = None

def get_model():
    global model
    if model is None:
        print("🔄 Loading memory...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
    return model

def embed(text: str):
    return get_model().encode(text).tolist()


def normalize_tags(tags):
    if not tags:
        return ""
    if isinstance(tags, list):
        return ",".join(tags)
    return str(tags)


def save_longterm_memory(
    text: str,
    memory_type: str = "Long-Term-Memory",
    tags=None,
    importance: str = "medium",
    source: str = "user"
):
    metadata = {
        "type": memory_type,
        "tags": normalize_tags(tags),
        "importance": importance,
        "source": source,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    try:
        collection.add(
            documents=[text],
            embeddings=[embed(text)],
            metadatas=[metadata],
            ids=[str(uuid.uuid4())]
        )

        print(f"✅ Saved in [{memory_type}] | Tags: {metadata['tags']}")
        return True

    except Exception as e:
        print("❌ Save error:", e)
        return False


def search_vector_memory(
    query: str,
    top_k: int = 3
):
    try:
        results = collection.query(
            query_embeddings=[embed(query)],
            n_results=top_k
        )

        if not results["documents"] or not results["documents"][0]:
            return []

        memories = []
        for i in range(len(results["documents"][0])):
            memories.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })

        return memories

    except Exception as e:
        return("❌ Search error:", e)
        return []



