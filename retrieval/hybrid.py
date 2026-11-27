from retrieval.baseline import retriever as baseline_retriever
from retrieval.chunks import retrieve as chunks_retrieve
from retrieval.rag_fusion import reciprocal_rank_fusion
from typing import List, Dict, Any

def retrieve(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Hybrid: fuse symptom-summary search and full-text chunk search with RRF"""
    baseline_retriever_docs = baseline_retriever.retrieve(query, top_k=10)
    chunks_retriever_docs = chunks_retrieve(query, top_k=10)
    
    return reciprocal_rank_fusion([baseline_retriever_docs, chunks_retriever_docs])[:top_k]

def query_retrieve(query: str, k: int = 5) -> List[str]:
    """Simple helper for evals: return just the top-k incident ids"""
    return [doc["id"] for doc in retrieve(query, top_k=k)]