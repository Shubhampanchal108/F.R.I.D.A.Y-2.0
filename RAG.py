import chromadb
from sentence_transformers import SentenceTransformer
import os
from datetime import datetime, timezone
import uuid
from path import RAG_PATH

os.makedirs(RAG_PATH, exist_ok=True)

# Initialize ChromaDB
client = chromadb.PersistentClient(path=RAG_PATH)

# ---- Collections (Multi-Type Memory Organization) ---- #
COLLECTIONS = {
    "general": "friday_general",          # General long-term memories
    "facts": "friday_facts",              # User facts & knowledge
    "episodes": "friday_episodes",        # Session summaries & episodic memory
    "preferences": "friday_preferences",  # User preferences & habits
    "procedures": "friday_procedures",    # Learned workflows
}


def get_collection(memory_type="general"):
    """Get or create a typed memory collection."""
    name = COLLECTIONS.get(memory_type, COLLECTIONS["general"])
    return client.get_or_create_collection(name=name)


# Legacy collection reference (old Friday_memory — kept for migration)
legacy_collection = client.get_or_create_collection(name="Friday_memory")


# ---- Embedding Model ---- #
model = None


def get_model():
    global model
    if model is None:
        print("🔄 Loading memory model...")
        try:
            model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            print("✅ Multilingual memory model loaded (Hindi/English support)")
        except Exception:
            print("⚠️ Multilingual model unavailable, falling back to MiniLM-L6")
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


# ---- RELEVANCE THRESHOLD ---- #
# ChromaDB uses L2 distance — lower = more similar
RELEVANCE_THRESHOLD = 1.2


# ---- TYPE MAPPING (backward compatible) ---- #
TYPE_MAPPING = {
    "Long-Term-Memory": "general",
    "preference": "preferences",
    "fact": "facts",
    "episode": "episodes",
    "procedure": "procedures",
    "instruction": "general",
    "relationship": "facts",
    "habit": "preferences",
    "emotion": "episodes",
    "goal": "general",
    "general": "general",
}


# ---------------- SAVE MEMORY ---------------- #
def save_longterm_memory(
    text: str,
    memory_type: str = "general",
    tags=None,
    importance: str = "medium",
    source: str = "user"
):
    collection_type = TYPE_MAPPING.get(memory_type, "general")
    target_collection = get_collection(collection_type)

    metadata = {
        "type": memory_type,
        "tags": normalize_tags(tags),
        "importance": importance,
        "source": source,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "access_count": 0,
        "last_accessed": "",
        "decay_score": 1.0,
    }

    try:
        target_collection.add(
            documents=[text],
            embeddings=[embed(text)],
            metadatas=[metadata],
            ids=[str(uuid.uuid4())]
        )
        return f"✅ Saved to {collection_type}: {text[:50]}..."

    except Exception as e:
        print("❌ Save error:", e)
        return False


# ---------------- SEARCH MEMORY (Multi-Collection + Relevance Filtering) ---------------- #
def search_vector_memory(query: str, top_k: int = 5, collections_to_search=None, apply_threshold=True):
    """
    Search across multiple memory collections with relevance filtering,
    temporal recency scoring, and importance weighting.
    """
    if collections_to_search is None:
        collections_to_search = ["general", "facts", "episodes", "preferences", "procedures"]

    all_memories = []
    query_embedding = embed(query)

    for col_type in collections_to_search:
        try:
            col = get_collection(col_type)
            count = col.count()
            if count == 0:
                continue

            results = col.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, count)
            )

            if not results["documents"] or not results["documents"][0]:
                continue

            for i in range(len(results["documents"][0])):
                distance = results["distances"][0][i]

                # Apply relevance threshold — skip irrelevant memories
                if apply_threshold and distance > RELEVANCE_THRESHOLD:
                    continue

                metadata = results["metadatas"][0][i]

                # Temporal recency scoring — boost recent memories
                recency_boost = _calculate_recency_boost(metadata.get("timestamp", ""))

                # Importance boost — critical memories surface more easily
                importance = metadata.get("importance", "medium")
                importance_multiplier = {
                    "critical": 0.5,
                    "high": 0.7,
                    "medium": 1.0,
                    "low": 1.3
                }.get(importance, 1.0)

                # Access frequency boost — frequently accessed = more relevant
                access_count = int(metadata.get("access_count", 0))
                access_boost = max(0.8, 1.0 - (access_count * 0.02))

                adjusted_distance = distance * recency_boost * importance_multiplier * access_boost

                all_memories.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": metadata,
                    "distance": distance,
                    "adjusted_distance": adjusted_distance,
                    "collection": col_type,
                })

                # Update access tracking (non-blocking)
                _update_access_tracking(col, results["ids"][0][i], metadata)

        except Exception as e:
            print(f"❌ Search error in {col_type}:", e)

    # Sort by adjusted distance (lower = more relevant)
    all_memories.sort(key=lambda x: x["adjusted_distance"])

    return all_memories[:top_k]


def _calculate_recency_boost(timestamp_str):
    """Boost recent memories — lower multiplier = higher priority."""
    if not timestamp_str:
        return 1.0
    try:
        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        age_hours = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
        if age_hours < 1:
            return 0.7       # Very recent — strong boost
        elif age_hours < 24:
            return 0.85      # Today — moderate boost
        elif age_hours < 168:  # 1 week
            return 0.95
        else:
            return 1.0       # Older — no boost
    except Exception:
        return 1.0


def _update_access_tracking(col, memory_id, metadata):
    """Update access count and last_accessed timestamp."""
    try:
        new_count = int(metadata.get("access_count", 0)) + 1
        metadata["access_count"] = new_count
        metadata["last_accessed"] = datetime.now(timezone.utc).isoformat()
        # Refresh decay score on access — memories that are used don't decay
        metadata["decay_score"] = min(1.0, float(metadata.get("decay_score", 1.0)) + 0.1)
        col.update(ids=[memory_id], metadatas=[metadata])
    except Exception:
        pass  # Non-critical — don't break the query flow


# ---------------- DELETE FUNCTION ---------------- #
def delete_memory_by_id(memory_id: str, collection_type: str = "general"):
    try:
        col = get_collection(collection_type)
        col.delete(ids=[memory_id])
        return True
    except Exception as e:
        print(f"❌ Error deleting ID {memory_id}: {e}")
        return False


# ---------------- GET ALL MEMORIES (for consolidation) ---------------- #
def get_all_memories(collection_type="general"):
    """Get all memories from a specific collection."""
    try:
        col = get_collection(collection_type)
        return col.get()
    except Exception as e:
        print(f"❌ Error getting all memories: {e}")
        return {"documents": [], "metadatas": [], "ids": []}


# ---------------- MIGRATION UTILITY ---------------- #
def migrate_legacy_memories():
    """
    Migrate memories from old Friday_memory collection to new typed collections.
    Re-embeds with the new multilingual model.
    """
    try:
        all_data = legacy_collection.get()
        if not all_data["documents"]:
            return "No legacy memories to migrate."

        migrated = 0
        for i in range(len(all_data["documents"])):
            text = all_data["documents"][i]
            old_metadata = all_data["metadatas"][i] if all_data["metadatas"] else {}

            save_longterm_memory(
                text=text,
                memory_type=old_metadata.get("type", "general"),
                tags=old_metadata.get("tags", ""),
                importance=old_metadata.get("importance", "medium"),
                source="migrated_legacy"
            )
            migrated += 1

        return f"✅ Migrated {migrated} memories from legacy collection to new typed collections."
    except Exception as e:
        return f"❌ Migration error: {e}"
