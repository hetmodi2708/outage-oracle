from ingest.index import VectorStore
from retrieval.baseline import embedding_manager
from typing import List, Dict, Any

vector_store = VectorStore(collection_name="incident_chunks")

CANDIDATE_CHUNKS = 30    #fetch extra: several hits will be chunks of the same incident


def retrieve(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search full-text chunks, then return each parent incident once, scored by its best chunk"""
    query_embedding = embedding_manager.generate_embeddings([query])[0]

    try:
        results = vector_store.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=CANDIDATE_CHUNKS,
        )
    except Exception as e:
        print(f"Error occurred while querying the chunk store: {e}")
        return []

    retrieved_docs = []
    seen_incidents = set()

    
    for chunk_text, metadata, distance in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        incident_id = metadata["incident_id"]
        if incident_id in seen_incidents:
            continue                      
        seen_incidents.add(incident_id)

        retrieved_docs.append({
            "id": incident_id,            
            "similarity_score": float(1 - distance),
            "metadata": metadata,
            "content": chunk_text,        
            "rank": len(retrieved_docs) + 1,
        })

        if len(retrieved_docs) == top_k:
            break

    return retrieved_docs

def query_retrieve(query: str, k: int = 5) -> List[str]:
    """Simple helper for evals: return just the top-k incident ids"""
    return [doc["id"] for doc in retrieve(query, top_k=k)]