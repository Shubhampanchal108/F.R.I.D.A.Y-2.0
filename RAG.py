import chromadb
from sentence_transformers import SentenceTransformer
import os
from datetime import datetime, timezone
import uuid
from path import RAG_PATH

os.makedirs(RAG_PATH, exist_ok=True)

# Initialize ChromaDB
client = chromadb.PersistentClient(path=RAG_PATH)

COLLECTION_NAME = "Friday_memory"
collection = client.get_or_create_collection(name=COLLECTION_NAME)

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

# ---------------- SAVE MEMORY ---------------- #
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
        return f"✅ Saved: {text[:30]}..."

    except Exception as e:
        print("❌ Save error:", e)
        return False

# ---------------- SEARCH MEMORY (Updated to return IDs) ---------------- #
def search_vector_memory(query: str, top_k: int = 3):
    try:
        results = collection.query(
            query_embeddings=[embed(query)],
            n_results=top_k
        )

        if not results["documents"] or not results["documents"][0]:
            return []

        memories = []
        # Loop through results
        for i in range(len(results["documents"][0])):
            memories.append({
                "id": results["ids"][0][i],       # <--- ID add kiya hai delete ke liye
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })

        return memories

    except Exception as e:
        print("❌ Search error:", e)
        return []

# ---------------- DELETE FUNCTION (New) ---------------- #
def delete_memory_by_id(memory_id: str):
    try:
        collection.delete(ids=[memory_id])
        return True
    except Exception as e:
        print(f"❌ Error deleting ID {memory_id}: {e}")
        return False
