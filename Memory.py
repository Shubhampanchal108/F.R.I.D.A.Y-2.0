# import chromadb
# from sentence_transformers import SentenceTransformer
# import os

# BASE_DIR = r"C:\Users\j\OneDrive\Desktop\shubham studio\F.R.I.D.A.Y\Database\memory"
# os.makedirs(BASE_DIR, exist_ok=True)

# # ✅ Persistent Client (Disk Storage)
# client = chromadb.PersistentClient(
#     path=BASE_DIR
# )

# collection = client.get_or_create_collection("friday_memory")

# model = None


# def get_model():
#     global model
#     if model is None:
#         print("🔄 Loading memory...")
#         model = SentenceTransformer("all-MiniLM-L6-v2")
#     return model

# def embed(text):
#     return get_model().encode(text).tolist()

# def save_vector_memory(text):
#     try:
#         collection.add(
#             documents=[text],
#             embeddings=[embed(text)],
#             ids=[str(abs(hash(text)))]
#         )
#         return {
#             "status": "success",
#             "msg": "data saved to long term memory"
#         }
#     except Exception as e:
#         print("❌ Save error:", e)

# def search_vector_memory(query):
#     try:
#         results = collection.query(
#             query_embeddings=[embed(query)],
#             n_results=1
#         )

#         # ✅ Check if database is empty or no result found
#         if not results["documents"] or not results["documents"][0]:
#             return None

#         return results["documents"][0][0]

#     except Exception as e:
#         print("❌ Search error:", e)
#         return None


# # Test
# if __name__ == "__main__":
#     # save_vector_memory("Shubhu is building Friday AI")
    
#     while True:
#         w = input("Enter a chat : ")
#         ans = search_vector_memory(w)
#         print(ans)
